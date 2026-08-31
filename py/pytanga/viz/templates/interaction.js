// Tanga Interaction — Pointer event capture for interactive 3D objects.
//
// Responsibilities:
//   - Track which meshes are interactive (per their entity JSON "interaction" field)
//   - Raycaster on pointermove to detect hover + scroll targets
//   - Throttle events per (object_id, event_type) using config.throttle_ms
//   - Drag with setPointerCapture + OrbitControls conflict resolution
//   - Click / double-click detection (distance + time threshold)
//   - Scroll wheel capture (non-passive, only when hovering interactive object)
//   - Ray-plane intersection for drag: projects mouse ray onto depth plane
//   - Sends camera matrices with drag_start / click / dblclick / scroll events;
//     omits them from drag_move / drag_end (backend caches from drag_start)
//   - Construct JSON messages and send via WebSocket
//
// One `InteractionController` is created per rendered pane (`ThreeJsView`), so
// pointer state (camera, DOM element, controls, websocket, space dim, object
// registry, and drag/click/hover/throttle state) is independent for every pane
// in a split view.

import * as THREE from 'three';

// Double-click timeout (ms)
const DBLCLICK_TIMEOUT = 300;
// Click movement threshold (pixels)
const CLICK_THRESHOLD = 3;

export class InteractionController {
    constructor(camera, rendererDomElement, controls, websocket) {
        this.camera = camera;
        this.rendererDomElement = rendererDomElement;
        this.controls = controls;
        this.ws = websocket;

        // objectId → { mesh, config }
        this.interactiveObjects = new Map();
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.spaceDim = 3;  // set via setSpaceDim() from three-view.js

        // Throttling state: "objectId:eventType" → { lastSent, pendingTimer, pendingData }
        this._throttles = new Map();

        // Drag state: { objectId, button, modifiers, startPos, lastPos, pointerId,
        //   depth, viewDir, right, up, lastWorldPos }
        this._activeDrag = null;
        this._dragStarted = false;

        // Click detection state
        this._clickState = new Map();

        // Hover tracking and visual feedback
        this._hoveredObjectId = null;
        this._hoverState = new Map();  // objectId → { originalEmissive, originalScale }

        rendererDomElement.addEventListener('pointerdown', (e) => this._onPointerDown(e));
        rendererDomElement.addEventListener('pointermove', (e) => this._onPointerMove(e));
        rendererDomElement.addEventListener('pointerup', (e) => this._onPointerUp(e));
        rendererDomElement.addEventListener('lostpointercapture', () => this._onLostCapture());
        rendererDomElement.addEventListener('wheel', (e) => this._onWheel(e), { passive: false });
        rendererDomElement.addEventListener('dblclick', (e) => this._onDblClick(e));
    }

    setSpaceDim(dim) {
        this.spaceDim = dim;
    }

    setCamera(camera) {
        this.camera = camera;
    }

    setWebSocket(websocket) {
        this.ws = websocket;
    }

    registerInteractive(objectId, mesh, config) {
        if (!config || !config.enabled) return;
        this.interactiveObjects.set(objectId, { mesh, config });
    }

    unregisterInteractive(objectId) {
        this.interactiveObjects.delete(objectId);
        for (const key of this._throttles.keys()) {
            if (key.startsWith(objectId + ':')) {
                const entry = this._throttles.get(key);
                if (entry.pendingTimer) clearTimeout(entry.pendingTimer);
                this._throttles.delete(key);
            }
        }
        this._clickState.delete(objectId);
        if (this._activeDrag && this._activeDrag.objectId === objectId) this._cancelDrag();
        if (this._hoveredObjectId === objectId) this._hoveredObjectId = null;
    }

    clearAllInteractive() {
        this.interactiveObjects.clear();
        for (const entry of this._throttles.values()) {
            if (entry.pendingTimer) clearTimeout(entry.pendingTimer);
        }
        this._throttles.clear();
        this._clickState.clear();
        this._hoveredObjectId = null;
        this._cancelDrag();
    }

    setDragAnchor(objectId, worldPosition) {
        if (!this._activeDrag) return;
        if (this._activeDrag.objectId !== objectId) return;
        if (!this._activeDrag.anchorPending) return;

        const anchor = new THREE.Vector3(worldPosition[0], worldPosition[1], worldPosition[2]);
        const { screenDx, screenDy, dist } = this._computeScreenPlaneVectors(anchor);
        const worldDelta = this._pixelToWorldDelta(
            this._activeDrag.pendingPixelDelta.x,
            this._activeDrag.pendingPixelDelta.y,
            screenDx,
            screenDy,
            this._activeDrag.dragMode,
        );

        this._activeDrag.accWorldPos.copy(anchor).add(worldDelta);
        this._activeDrag.screenDx = screenDx;
        this._activeDrag.screenDy = screenDy;
        this._activeDrag.dist = dist;
        this._activeDrag.anchorPending = false;

        // Send one immediate drag_move with the corrected world position,
        // bypassing the throttle (the backend rebases onto this anchor).
        const payload = {
            type: 'interaction:drag_move',
            event_type: 'drag_move',
            object_id: this._activeDrag.objectId,
            mouse_button: this._activeDrag.button,
            modifiers: Array.from(this._activeDrag.modifiers),
            screen_position: [this._activeDrag.lastPos.x, this._activeDrag.lastPos.y],
            delta_pixels: [
                this._activeDrag.pendingPixelDelta.x,
                this._activeDrag.pendingPixelDelta.y,
            ],
            world_position: [
                this._activeDrag.accWorldPos.x,
                this._activeDrag.accWorldPos.y,
                this._activeDrag.accWorldPos.z,
            ],
            world_delta: [worldDelta.x, worldDelta.y, worldDelta.z],
            drag_mode: this._activeDrag.dragMode,
        };
        if (this.ws) this.ws.send(JSON.stringify(payload));
    }

    // ── Hover effect helpers ───────────────────────────────────────

    _materialState(m) {
        const usesUniformOpacity = !!(m.uniforms && m.uniforms.uOpacity);
        return {
            ref: m,
            // MeshPhong/Standard emissive (hex); null = not applicable.
            emissive: m.emissive ? m.emissive.getHex() : null,
            // SDF proxy ShaderMaterial hover-glow uniform (hex); null = n/a.
            hover: (m.uniforms && m.uniforms.uHover) ? m.uniforms.uHover.value.getHex() : null,
            // Opacity: the SDF ShaderMaterial drives alpha via `uOpacity`; regular
            // materials use `.opacity` (Material always exposes `.opacity`, so check
            // the uniform first).
            opacity: usesUniformOpacity ? m.uniforms.uOpacity.value : m.opacity,
            usesUniformOpacity,
            transparent: m.transparent !== undefined ? m.transparent : null,
            depthWrite: m.depthWrite !== undefined ? m.depthWrite : null,
        };
    }

    _saveMeshState(mesh) {
        const state = { _materials: [] };
        mesh.traverse(child => {
            if (!child.material) return;
            if (Array.isArray(child.material)) {
                for (const m of child.material) state._materials.push(this._materialState(m));
            } else {
                state._materials.push(this._materialState(child.material));
            }
        });
        state._originalScale = mesh.scale.clone();
        return state;
    }

    _applyHover(mesh, config) {
        const emissiveColor = config.hover_emissive;
        const scale = config.hover_scale;
        const opacity = config.hover_opacity;

        // Save original state
        const state = this._saveMeshState(mesh);
        this._hoverState.set(mesh.uuid, state);

        // Apply emissive glow — MeshPhong/Standard use `.emissive`, the SDF proxy
        // ShaderMaterial uses its `uHover` uniform.
        if (emissiveColor) {
            const c = new THREE.Color(emissiveColor);
            for (const { ref: m } of state._materials) {
                if (m.emissive) m.emissive.copy(c);
                else if (m.uniforms && m.uniforms.uHover) m.uniforms.uHover.value.copy(c);
            }
        }

        // Apply opacity override.
        if (typeof opacity === 'number') {
            const translucent = opacity < 1.0;
            for (const entry of state._materials) {
                const m = entry.ref;
                if (entry.usesUniformOpacity) {
                    m.uniforms.uOpacity.value = opacity;
                    m.transparent = translucent;
                    // keep depthWrite: SDF depth is written for correct occlusion.
                } else if (m.opacity !== undefined) {
                    m.opacity = opacity;
                    m.transparent = translucent;
                    m.depthWrite = !translucent;
                }
            }
        }

        // Apply scale — `Object3D.scale` is universal, so this already works for
        // SDF proxies too: the shader marches in the mesh's *local* space and the
        // scale is carried to world space through `modelMatrix` / `uModelMatrix`
        // (unlike emissive/opacity, which needed explicit `uHover`/`uOpacity`
        // handling because a `ShaderMaterial` has no `.emissive`/`.opacity`).
        if (scale) {
            mesh.scale.multiplyScalar(scale);
        }

        this.rendererDomElement.style.cursor = 'pointer';
    }

    _resetHover(mesh) {
        if (!mesh) return;
        const state = this._hoverState.get(mesh.uuid);
        if (!state) return;

        for (const entry of state._materials) {
            const { ref: m, emissive, hover, opacity, transparent, depthWrite } = entry;
            if (emissive !== null && m.emissive) m.emissive.setHex(emissive);
            if (hover !== null && m.uniforms && m.uniforms.uHover) m.uniforms.uHover.value.setHex(hover);
            if (opacity !== null) {
                if (entry.usesUniformOpacity) {
                    m.uniforms.uOpacity.value = opacity;
                    m.transparent = transparent;
                } else if (m.opacity !== undefined) {
                    m.opacity = opacity;
                    m.transparent = transparent;
                    m.depthWrite = depthWrite;
                }
            }
        }

        // Restore scale
        mesh.scale.copy(state._originalScale);

        this._hoverState.delete(mesh.uuid);
        this.rendererDomElement.style.cursor = '';
    }

    // ── Camera payload helper ───────────────────────────────────────
    //
    // Sends view and projection matrices (and their inverses) plus viewport
    // dimensions.  This allows the Python backend to do full world↔screen
    // projection without any trigonometry.

    _getCameraPayload(worldPos) {
        const view = Array.from(this.camera.matrixWorldInverse.elements);
        const viewInv = Array.from(this.camera.matrixWorld.elements);
        const proj = Array.from(this.camera.projectionMatrix.elements);
        const projInv = Array.from(this.camera.projectionMatrixInverse.elements);
        const dist = worldPos ? this.camera.position.distanceTo(worldPos) : 0;

        return {
            camera: {
                view: view,
                view_inv: viewInv,
                proj: proj,
                proj_inv: projInv,
                viewport_width: this.rendererDomElement.clientWidth,
                viewport_height: this.rendererDomElement.clientHeight,
                space_dim: this.spaceDim,
            },
            camera_distance: dist,
        };
    }

    // ── Screen-plane delta vectors ───────────────────────────────

    _computeScreenPlaneVectors(intersectPoint) {
        // Compute world-space vectors corresponding to +1 pixel in
        // screen X and screen Y.  Perspective cameras scale by the vertical
        // FOV at the intersection depth; orthographic cameras (2D) use the
        // constant frustum height instead (camera.fov is undefined there).
        const dist = intersectPoint.distanceTo(this.camera.position);
        const viewportHeight = this.rendererDomElement.clientHeight;

        let scale;
        if (this.camera.isOrthographicCamera) {
            const frustumHeight = this.camera.top - this.camera.bottom;
            scale = frustumHeight / viewportHeight;
        } else {
            const vFov = THREE.MathUtils.degToRad(this.camera.fov || 50);
            scale = 2 * dist * Math.tan(vFov / 2) / viewportHeight;
        }

        const right = new THREE.Vector3();
        const up = new THREE.Vector3();
        const forward = new THREE.Vector3();
        this.camera.matrixWorld.extractBasis(right, up, forward);
        right.normalize();
        up.normalize();

        const screenDx = right.clone().multiplyScalar(scale);
        const screenDy = up.clone().multiplyScalar(-scale);  // screen -Y → world

        return { screenDx, screenDy, dist };
    }

    _projectToPlane(deltaWorld, dragMode) {
        // Project a world-space delta onto the constraint plane by
        // zeroing the out-of-plane component.  For XY_PLANE, zero Z;
        // for XZ_PLANE, zero Y; for YZ_PLANE, zero X.
        const d = deltaWorld.clone();
        switch (dragMode) {
            case 'xy_plane': d.z = 0; break;
            case 'xz_plane': d.y = 0; break;
            case 'yz_plane': d.x = 0; break;
            // view_plane: no projection needed (screen deltas are
            // already tangent to the plane at the object's depth)
        }
        return d;
    }

    // ── Axis-aligned drag mapping ─────────────────────────────────
    // Maps screen-space pixel deltas to world-axis deltas on a
    // constraint plane.  Screen X movement drives one axis, screen Y
    // the other — simple, predictable, no singularities.

    _axisMappedDelta(dx, dy, screenDx, screenDy, dragMode) {
        const result = new THREE.Vector3();
        switch (dragMode) {
            case 'xy_plane':
                result.set(screenDx.x * dx, screenDy.y * dy, 0);
                break;
            case 'xz_plane':
                result.set(screenDx.x * dx, 0, screenDy.z * dy);
                break;
            case 'yz_plane':
                result.set(0, screenDx.y * dx, screenDy.z * dy);
                break;
            default:
                return null;  // view_plane: use raw delta
        }
        return result;
    }

    // ── Trigger Matching ─────────────────────────────────────────

    _findMatchingTriggers(objectId, eventType, button, modifiers) {
        const obj = this.interactiveObjects.get(objectId);
        if (!obj) return [];
        return obj.config.triggers.filter(t => {
            if (t.event_type !== eventType) return false;
            if (t.mouse_button != null && t.mouse_button !== button) return false;
            const reqMods = t.modifiers || [];
            if (reqMods.length > 0) {
                for (const m of reqMods) {
                    if (!modifiers.has(m)) return false;
                }
            }
            return true;
        });
    }

    _getActiveModifiers(event) {
        const mods = new Set();
        if (event.ctrlKey || event.metaKey) mods.add('ctrl');
        if (event.shiftKey) mods.add('shift');
        if (event.altKey) mods.add('alt');
        return mods;
    }

    _mouseButtonFromEvent(event) {
        switch (event.button) {
            case 0: return 'left';
            case 1: return 'middle';
            case 2: return 'right';
            default: return 'left';
        }
    }

    // ── Raycasting ───────────────────────────────────────────────

    _getInteractiveHit(event) {
        const meshes = [];
        for (const [, obj] of this.interactiveObjects) meshes.push(obj.mesh);
        if (meshes.length === 0) return null;

        const rect = this.rendererDomElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(meshes, true);
        if (intersects.length === 0) return null;

        const hitMesh = intersects[0].object;
        for (const [id, obj] of this.interactiveObjects) {
            if (obj.mesh === hitMesh || this._isDescendantOf(hitMesh, obj.mesh)) {
                return { objectId: id, intersect: intersects[0] };
            }
        }
        return null;
    }

    _isDescendantOf(child, ancestor) {
        let cur = child;
        while (cur) {
            if (cur === ancestor) return true;
            cur = cur.parent;
        }
        return false;
    }

    // ── Throttling ───────────────────────────────────────────────

    _throttledSend(objectId, eventType, buildPayload) {
        const obj = this.interactiveObjects.get(objectId);
        if (!obj || !this.ws) return;
        const throttleMs = obj.config.throttle_ms || 0;
        const key = objectId + ':' + eventType;

        if (throttleMs <= 0) { this.ws.send(JSON.stringify(buildPayload())); return; }

        const now = performance.now();
        const entry = this._throttles.get(key);

        if (entry && entry.lastSent && (now - entry.lastSent) < throttleMs) {
            entry.pendingData = buildPayload;
            if (!entry.pendingTimer) {
                entry.pendingTimer = setTimeout(() => this._flushThrottle(key),
                    throttleMs - (now - entry.lastSent));
            }
        } else {
            if (entry && entry.pendingTimer) {
                clearTimeout(entry.pendingTimer);
                entry.pendingTimer = null;
            }
            this._throttles.set(key, { lastSent: now, pendingTimer: null, pendingData: null });
            this.ws.send(JSON.stringify(buildPayload()));
        }
    }

    _flushThrottle(key) {
        const entry = this._throttles.get(key);
        if (!entry || !entry.pendingData || !this.ws) return;
        this.ws.send(JSON.stringify(entry.pendingData()));
        entry.lastSent = performance.now();
        entry.pendingData = null;
        entry.pendingTimer = null;
    }

    // ── Pointer Event Handlers ───────────────────────────────────

    _onPointerDown(event) {
        const hit = this._getInteractiveHit(event);
        if (!hit) return;

        const modifiers = this._getActiveModifiers(event);
        const button = this._mouseButtonFromEvent(event);

        const dragTriggers = this._findMatchingTriggers(hit.objectId, 'drag', button, modifiers);
        if (dragTriggers.length > 0) {
            const worldPos = hit.intersect.point;
            const { screenDx, screenDy, dist } = this._computeScreenPlaneVectors(worldPos);
            // Pick the most specific trigger (most modifier requirements wins)
            const trigger = dragTriggers.reduce((best, t) => {
                const bestMods = (best.modifiers || []).length;
                const tMods = (t.modifiers || []).length;
                return tMods > bestMods ? t : best;
            });
            const dragMode = trigger.drag_mode || 'view_plane';

            this._activeDrag = {
                objectId: hit.objectId,
                button, modifiers,
                startPos: { x: event.clientX, y: event.clientY },
                lastPos: { x: event.clientX, y: event.clientY },
                pointerId: event.pointerId,
                dragMode, screenDx, screenDy, dist,
                accWorldPos: worldPos.clone(),
                rayOrigin: [
                    this.raycaster.ray.origin.x,
                    this.raycaster.ray.origin.y,
                    this.raycaster.ray.origin.z,
                ],
                rayDirection: [
                    this.raycaster.ray.direction.x,
                    this.raycaster.ray.direction.y,
                    this.raycaster.ray.direction.z,
                ],
                anchorPending: true,
                pendingPixelDelta: new THREE.Vector2(),
            };
            this._dragStarted = false;
            this.rendererDomElement.setPointerCapture(event.pointerId);
            if (this.controls) this.controls.enabled = false;
            event.preventDefault();
            event.stopPropagation();
        }

        this._clickState.set(hit.objectId, {
            pointerDownPos: { x: event.clientX, y: event.clientY },
            pointerDownTime: performance.now(),
            button, modifiers,
        });
    }

    _pixelToWorldDelta(dx, dy, screenDx, screenDy, dragMode) {
        const axisDelta = this._axisMappedDelta(dx, dy, screenDx, screenDy, dragMode);
        if (axisDelta) {
            return axisDelta;
        }
        const rawDelta = new THREE.Vector3()
            .addScaledVector(screenDx, dx)
            .addScaledVector(screenDy, dy);
        return this._projectToPlane(rawDelta, dragMode);
    }

    _onPointerMove(event) {
        if (this._activeDrag) {
            const dx = event.clientX - this._activeDrag.lastPos.x;
            const dy = event.clientY - this._activeDrag.lastPos.y;
            this._activeDrag.lastPos = { x: event.clientX, y: event.clientY };

            const { dragMode, screenDx, screenDy, accWorldPos } = this._activeDrag;

            const eventType = this._dragStarted ? 'drag_move' : 'drag_start';

            let worldDelta = [0, 0, 0];
            if (this._activeDrag.anchorPending) {
                // Buffer raw pixel deltas; convert to world space once the
                // ideal anchor arrives (setDragAnchor).  No drag_move is sent
                // until then — only the first-move drag_start goes out.
                this._activeDrag.pendingPixelDelta.x += dx;
                this._activeDrag.pendingPixelDelta.y += dy;
                if (this._dragStarted) {
                    event.preventDefault();
                    return;
                }
            } else {
                // Compute world-space delta from pixel movement.
                // For axis-aligned constraint planes, use axis mapping so
                // that mouse movement along the apparent world-axis direction
                // on screen produces pure world-axis movement.
                const worldDeltaVec = this._pixelToWorldDelta(dx, dy, screenDx, screenDy, dragMode);
                accWorldPos.add(worldDeltaVec);
                worldDelta = [worldDeltaVec.x, worldDeltaVec.y, worldDeltaVec.z];
            }

            const worldPos = accWorldPos;

            // Build payload: camera is only included for drag_start
            const basePayload = {
                type: 'interaction:drag_move',
                event_type: eventType,
                object_id: this._activeDrag.objectId,
                mouse_button: this._activeDrag.button,
                modifiers: Array.from(this._activeDrag.modifiers),
                screen_position: [event.clientX, event.clientY],
                delta_pixels: [dx, dy],
                world_position: [worldPos.x, worldPos.y, worldPos.z],
                world_delta: worldDelta,
                drag_mode: dragMode,
            };
            if (eventType === 'drag_start') {
                basePayload.ray_origin = this._activeDrag.rayOrigin;
                basePayload.ray_direction = this._activeDrag.rayDirection;
            }

            const payload = this._dragStarted
                ? () => ({ ...basePayload })  // drag_move: no camera
                : { ...basePayload, ...this._getCameraPayload(worldPos) };  // drag_start: include camera

            if (this._dragStarted) {
                this._throttledSend(this._activeDrag.objectId, 'drag_move', payload);
            } else {
                if (this.ws) this.ws.send(JSON.stringify(payload));
                this._dragStarted = true;
            }
            event.preventDefault();
            return;
        }

        const hit = this._getInteractiveHit(event);
        const newHoveredId = hit ? hit.objectId : null;

        if (newHoveredId !== this._hoveredObjectId) {
            // Reset previous hover
            if (this._hoveredObjectId) {
                const prevObj = this.interactiveObjects.get(this._hoveredObjectId);
                if (prevObj && prevObj.mesh) this._resetHover(prevObj.mesh);
            }
            // Apply new hover
            if (newHoveredId) {
                const newObj = this.interactiveObjects.get(newHoveredId);
                if (newObj && newObj.mesh && newObj.config) {
                    this._applyHover(newObj.mesh, newObj.config);
                }
            }
            this._hoveredObjectId = newHoveredId;
        }
    }

    // ── Pointer up / click / dblclick / wheel / capture ───────────

    _onPointerUp(event) {
        if (this._activeDrag && this._activeDrag.pointerId === event.pointerId) {
            const { dragMode, accWorldPos } = this._activeDrag;

            // drag_end: no camera payload (backend cached it from drag_start)
            const payload = {
                type: 'interaction:drag_end',
                event_type: 'drag_end',
                object_id: this._activeDrag.objectId,
                mouse_button: this._activeDrag.button,
                modifiers: Array.from(this._activeDrag.modifiers),
                screen_position: [event.clientX, event.clientY],
                delta_pixels: [
                    event.clientX - this._activeDrag.startPos.x,
                    event.clientY - this._activeDrag.startPos.y,
                ],
                world_position: [accWorldPos.x, accWorldPos.y, accWorldPos.z],
                world_delta: [0, 0, 0],
                drag_mode: dragMode,
            };
            if (this.ws) this.ws.send(JSON.stringify(payload));

            this.rendererDomElement.releasePointerCapture(event.pointerId);
            if (this.controls) this.controls.enabled = true;
            this._activeDrag = null;
            this._dragStarted = false;
            return;
        }

        const hit = this._getInteractiveHit(event);
        const objectId = hit ? hit.objectId : null;
        if (objectId) {
            const state = this._clickState.get(objectId);
            if (state) {
                const dist = Math.hypot(
                    event.clientX - state.pointerDownPos.x,
                    event.clientY - state.pointerDownPos.y);
                const elapsed = performance.now() - state.pointerDownTime;

                if (dist < CLICK_THRESHOLD && elapsed < DBLCLICK_TIMEOUT) {
                    const button = this._mouseButtonFromEvent(event);
                    const modifiers = this._getActiveModifiers(event);
                    const triggers = this._findMatchingTriggers(objectId, 'click', button, modifiers);
                    if (triggers.length > 0 && hit) {
                        const wp = hit.intersect.point;
                        const normal = hit.intersect.face
                            ? hit.intersect.face.normal : new THREE.Vector3(0, 0, 1);
                        const payload = {
                            type: 'interaction:click',
                            event_type: 'click',
                            object_id: objectId,
                            mouse_button: button,
                            modifiers: Array.from(modifiers),
                            screen_position: [event.clientX, event.clientY],
                            world_position: [wp.x, wp.y, wp.z],
                            world_normal: [normal.x, normal.y, normal.z],
                            ...this._getCameraPayload(wp),
                        };
                        if (this.ws) this.ws.send(JSON.stringify(payload));
                    }
                }
                this._clickState.delete(objectId);
            }
        }
        if (this._activeDrag) this._cancelDrag();
    }

    // ── Dblclick / wheel / capture / cancel ──────────────────────

    _onDblClick(event) {
        const hit = this._getInteractiveHit(event);
        if (!hit) return;
        const button = this._mouseButtonFromEvent(event);
        const modifiers = this._getActiveModifiers(event);
        const triggers = this._findMatchingTriggers(hit.objectId, 'dblclick', button, modifiers);
        if (triggers.length > 0) {
            const wp = hit.intersect.point;
            const normal = hit.intersect.face
                ? hit.intersect.face.normal : new THREE.Vector3(0, 0, 1);
            const payload = {
                type: 'interaction:dblclick',
                event_type: 'dblclick',
                object_id: hit.objectId,
                mouse_button: button,
                modifiers: Array.from(modifiers),
                screen_position: [event.clientX, event.clientY],
                world_position: [wp.x, wp.y, wp.z],
                world_normal: [normal.x, normal.y, normal.z],
                ...this._getCameraPayload(wp),
            };
            if (this.ws) this.ws.send(JSON.stringify(payload));
        }
    }

    _onWheel(event) {
        const hit = this._getInteractiveHit(event);
        if (!hit) return;
        const modifiers = this._getActiveModifiers(event);
        const triggers = this._findMatchingTriggers(hit.objectId, 'scroll', null, modifiers);
        if (triggers.length > 0) {
            event.preventDefault();
            const wp = hit.intersect.point;
            const payload = () => ({
                type: 'interaction:scroll',
                event_type: 'scroll',
                object_id: hit.objectId,
                modifiers: Array.from(modifiers),
                screen_position: [event.clientX, event.clientY],
                delta_xy: [event.deltaX, event.deltaY],
                ...this._getCameraPayload(wp),
            });
            this._throttledSend(hit.objectId, 'scroll', payload);
        }
    }

    _onLostCapture() { if (this._activeDrag) this._cancelDrag(); }

    _cancelDrag() {
        if (this._activeDrag) {
            if (this._dragStarted && this.ws) {
                const payload = {
                    type: 'interaction:drag_end',
                    event_type: 'drag_end',
                    object_id: this._activeDrag.objectId,
                    mouse_button: this._activeDrag.button,
                    modifiers: Array.from(this._activeDrag.modifiers),
                    screen_position: [this._activeDrag.lastPos.x, this._activeDrag.lastPos.y],
                    delta_pixels: [0, 0],
                    world_position: [0, 0, 0],
                    world_delta: [0, 0, 0],
                };
                try { this.ws.send(JSON.stringify(payload)); } catch (e) {}
            }
            if (this.controls) this.controls.enabled = true;
            this._activeDrag = null;
            this._dragStarted = false;
        }
    }
}






