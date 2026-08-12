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

import * as THREE from 'three';

// ── State ────────────────────────────────────────────────────

const interactiveObjects = new Map();  // objectId → { mesh, config }
let ws = null;
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();
let camera = null;
let rendererDomElement = null;
let controls = null;
let _spaceDim = 3;  // set via setSpaceDim() from viewer.js

// Throttling state: "objectId:eventType" → { lastSent, pendingTimer, pendingData }
const _throttles = new Map();

// Drag state
let _activeDrag = null;
// { objectId, button, modifiers, startPos, lastPos, pointerId,
//   depth, viewDir, right, up, lastWorldPos }
let _dragStarted = false;

// Click detection state
const _clickState = new Map();

// Hover tracking and visual feedback
let _hoveredObjectId = null;
const _hoverState = new Map();  // objectId → { originalEmissive, originalScale }

// ── Hover effect helpers ───────────────────────────────────────

function _saveMeshState(mesh) {
    const state = {};
    mesh.traverse(child => {
        if (child.material) {
            if (!state._materials) state._materials = [];
            if (Array.isArray(child.material)) {
                state._materials.push(...child.material.map(m => ({
                    ref: m,
                    emissive: m.emissive ? m.emissive.getHex() : 0,
                    emissiveIsSet: m.emissive ? true : false,
                })));
            } else {
                state._materials.push({
                    ref: child.material,
                    emissive: child.material.emissive ? child.material.emissive.getHex() : 0,
                    emissiveIsSet: child.material.emissive ? true : false,
                });
            }
        }
    });
    state._originalScale = mesh.scale.clone();
    return state;
}

function _applyHover(mesh, config) {
    const emissiveColor = config.hover_emissive;
    const scale = config.hover_scale;

    // Save original state
    const state = _saveMeshState(mesh);
    _hoverState.set(mesh.uuid, state);

    // Apply emissive
    if (emissiveColor) {
        const c = new THREE.Color(emissiveColor);
        mesh.traverse(child => {
            if (child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach(m => {
                        if (m.emissive) m.emissive.copy(c);
                    });
                } else if (child.material.emissive) {
                    child.material.emissive.copy(c);
                }
            }
        });
    }

    // Apply scale
    if (scale) {
        mesh.scale.multiplyScalar(scale);
    }

    rendererDomElement.style.cursor = 'pointer';
}

function _resetHover(mesh) {
    if (!mesh) return;
    const state = _hoverState.get(mesh.uuid);
    if (!state) return;

    // Restore emissive
    if (state._materials) {
        state._materials.forEach(({ ref, emissive, emissiveIsSet }) => {
            if (emissiveIsSet && ref.emissive) {
                ref.emissive.setHex(emissive);
            }
        });
    }

    // Restore scale
    mesh.scale.copy(state._originalScale);

    _hoverState.delete(mesh.uuid);
    rendererDomElement.style.cursor = '';
}

// Double-click timeout (ms)
const DBLCLICK_TIMEOUT = 300;
// Click movement threshold (pixels)
const CLICK_THRESHOLD = 3;

// ── Camera payload helper ───────────────────────────────────────
//
// Sends view and projection matrices (and their inverses) plus viewport
// dimensions.  This allows the Python backend to do full world↔screen
// projection without any trigonometry.

function getCameraPayload(worldPos) {
    const view = Array.from(camera.matrixWorldInverse.elements);
    const viewInv = Array.from(camera.matrixWorld.elements);
    const proj = Array.from(camera.projectionMatrix.elements);
    const projInv = Array.from(camera.projectionMatrixInverse.elements);
    const dist = worldPos ? camera.position.distanceTo(worldPos) : 0;

    return {
        camera: {
            view: view,
            view_inv: viewInv,
            proj: proj,
            proj_inv: projInv,
            viewport_width: rendererDomElement.clientWidth,
            viewport_height: rendererDomElement.clientHeight,
            space_dim: _spaceDim,
        },
        camera_distance: dist,
    };
}

// ── Screen-plane delta vectors ───────────────────────────────

function computeScreenPlaneVectors(intersectPoint) {
    // Compute world-space vectors corresponding to +1 pixel in
    // screen X and screen Y, using the same scaling as the
    // raycaster's near-plane projection.
    //
    // The intersection point's distance from the camera determines
    // the scale: farther points → larger per-pixel world vectors.
    const dist = intersectPoint.distanceTo(camera.position);
    const vFov = THREE.MathUtils.degToRad(camera.fov);
    const viewportHeight = rendererDomElement.clientHeight;
    const scale = 2 * dist * Math.tan(vFov / 2) / viewportHeight;

    const right = new THREE.Vector3();
    const up = new THREE.Vector3();
    const forward = new THREE.Vector3();
    camera.matrixWorld.extractBasis(right, up, forward);
    right.normalize();
    up.normalize();

    const screenDx = right.clone().multiplyScalar(scale);
    const screenDy = up.clone().multiplyScalar(-scale);  // screen -Y → world

    return { screenDx, screenDy, dist };
}

function projectToPlane(deltaWorld, dragMode) {
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

function axisMappedDelta(dx, dy, screenDx, screenDy, dragMode) {
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

// ── Initialization ───────────────────────────────────────────

export function initInteraction(_camera, _rendererDomElement, _controls, websocket) {
    camera = _camera;
    rendererDomElement = _rendererDomElement;
    controls = _controls;
    ws = websocket;

    rendererDomElement.addEventListener('pointerdown', onPointerDown);
    rendererDomElement.addEventListener('pointermove', onPointerMove);
    rendererDomElement.addEventListener('pointerup', onPointerUp);
    rendererDomElement.addEventListener('lostpointercapture', onLostCapture);
    rendererDomElement.addEventListener('wheel', onWheel, { passive: false });
    rendererDomElement.addEventListener('dblclick', onDblClick);
}

export function setSpaceDim(dim) {
    _spaceDim = dim;
}

// ── Object Registration ──────────────────────────────────────

export function registerInteractive(objectId, mesh, config) {
    if (!config || !config.enabled) return;
    interactiveObjects.set(objectId, { mesh, config });
}

export function unregisterInteractive(objectId) {
    interactiveObjects.delete(objectId);
    for (const key of _throttles.keys()) {
        if (key.startsWith(objectId + ':')) {
            const entry = _throttles.get(key);
            if (entry.pendingTimer) clearTimeout(entry.pendingTimer);
            _throttles.delete(key);
        }
    }
    _clickState.delete(objectId);
    if (_activeDrag && _activeDrag.objectId === objectId) cancelDrag();
    if (_hoveredObjectId === objectId) _hoveredObjectId = null;
}

export function clearAllInteractive() {
    interactiveObjects.clear();
    for (const entry of _throttles.values()) {
        if (entry.pendingTimer) clearTimeout(entry.pendingTimer);
    }
    _throttles.clear();
    _clickState.clear();
    _hoveredObjectId = null;
    cancelDrag();
}

export function setWebSocket(websocket) { ws = websocket; }

// ── Trigger Matching ─────────────────────────────────────────

function findMatchingTriggers(objectId, eventType, button, modifiers) {
    const obj = interactiveObjects.get(objectId);
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

function getActiveModifiers(event) {
    const mods = new Set();
    if (event.ctrlKey || event.metaKey) mods.add('ctrl');
    if (event.shiftKey) mods.add('shift');
    if (event.altKey) mods.add('alt');
    return mods;
}

function mouseButtonFromEvent(event) {
    switch (event.button) {
        case 0: return 'left';
        case 1: return 'middle';
        case 2: return 'right';
        default: return 'left';
    }
}

// ── Raycasting ───────────────────────────────────────────────

function getInteractiveHit(event) {
    const meshes = [];
    for (const [, obj] of interactiveObjects) meshes.push(obj.mesh);
    if (meshes.length === 0) return null;

    const rect = rendererDomElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(meshes, true);
    if (intersects.length === 0) return null;

    const hitMesh = intersects[0].object;
    for (const [id, obj] of interactiveObjects) {
        if (obj.mesh === hitMesh || isDescendantOf(hitMesh, obj.mesh)) {
            return { objectId: id, intersect: intersects[0] };
        }
    }
    return null;
}

function isDescendantOf(child, ancestor) {
    let cur = child;
    while (cur) {
        if (cur === ancestor) return true;
        cur = cur.parent;
    }
    return false;
}

// ── Throttling ───────────────────────────────────────────────

function throttledSend(objectId, eventType, buildPayload) {
    const obj = interactiveObjects.get(objectId);
    if (!obj || !ws) return;
    const throttleMs = obj.config.throttle_ms || 0;
    const key = objectId + ':' + eventType;

    if (throttleMs <= 0) { ws.send(JSON.stringify(buildPayload())); return; }

    const now = performance.now();
    const entry = _throttles.get(key);

    if (entry && entry.lastSent && (now - entry.lastSent) < throttleMs) {
        entry.pendingData = buildPayload;
        if (!entry.pendingTimer) {
            entry.pendingTimer = setTimeout(() => flushThrottle(key),
                throttleMs - (now - entry.lastSent));
        }
    } else {
        if (entry && entry.pendingTimer) {
            clearTimeout(entry.pendingTimer);
            entry.pendingTimer = null;
        }
        _throttles.set(key, { lastSent: now, pendingTimer: null, pendingData: null });
        ws.send(JSON.stringify(buildPayload()));
    }
}

function flushThrottle(key) {
    const entry = _throttles.get(key);
    if (!entry || !entry.pendingData || !ws) return;
    ws.send(JSON.stringify(entry.pendingData()));
    entry.lastSent = performance.now();
    entry.pendingData = null;
    entry.pendingTimer = null;
}

// ── Pointer Event Handlers ───────────────────────────────────

function onPointerDown(event) {
    const hit = getInteractiveHit(event);
    if (!hit) return;

    const modifiers = getActiveModifiers(event);
    const button = mouseButtonFromEvent(event);

    const dragTriggers = findMatchingTriggers(hit.objectId, 'drag', button, modifiers);
    if (dragTriggers.length > 0) {
        const worldPos = hit.intersect.point;
        const { screenDx, screenDy, dist } = computeScreenPlaneVectors(worldPos);
        // Pick the most specific trigger (most modifier requirements wins)
        const trigger = dragTriggers.reduce((best, t) => {
            const bestMods = (best.modifiers || []).length;
            const tMods = (t.modifiers || []).length;
            return tMods > bestMods ? t : best;
        });
        const dragMode = trigger.drag_mode || 'view_plane';

        _activeDrag = {
            objectId: hit.objectId,
            button, modifiers,
            startPos: { x: event.clientX, y: event.clientY },
            lastPos: { x: event.clientX, y: event.clientY },
            pointerId: event.pointerId,
            dragMode, screenDx, screenDy, dist,
            accWorldPos: worldPos.clone(),
        };
        _dragStarted = false;
        rendererDomElement.setPointerCapture(event.pointerId);
        if (controls) controls.enabled = false;
        event.preventDefault();
        event.stopPropagation();
    }

    _clickState.set(hit.objectId, {
        pointerDownPos: { x: event.clientX, y: event.clientY },
        pointerDownTime: performance.now(),
        button, modifiers,
    });
}

function onPointerMove(event) {
    if (_activeDrag) {
        const dx = event.clientX - _activeDrag.lastPos.x;
        const dy = event.clientY - _activeDrag.lastPos.y;
        _activeDrag.lastPos = { x: event.clientX, y: event.clientY };

        const { dragMode, screenDx, screenDy, accWorldPos } = _activeDrag;

        // Compute world-space delta from pixel movement.
        // For axis-aligned constraint planes, use axis mapping so
        // that mouse movement along the apparent world-axis direction
        // on screen produces pure world-axis movement.
        let worldDeltaVec;
        const axisDelta = axisMappedDelta(dx, dy, screenDx, screenDy, dragMode);
        if (axisDelta) {
            worldDeltaVec = axisDelta;
        } else {
            const rawDelta = new THREE.Vector3()
                .addScaledVector(screenDx, dx)
                .addScaledVector(screenDy, dy);
            worldDeltaVec = projectToPlane(rawDelta, dragMode);
        }

        // Accumulate position
        accWorldPos.add(worldDeltaVec);

        const worldPos = accWorldPos;
        const worldDelta = [worldDeltaVec.x, worldDeltaVec.y, worldDeltaVec.z];

        const eventType = _dragStarted ? 'drag_move' : 'drag_start';

        // Build payload: camera is only included for drag_start
        const basePayload = {
            type: 'interaction:drag_move',
            event_type: eventType,
            object_id: _activeDrag.objectId,
            mouse_button: _activeDrag.button,
            modifiers: Array.from(_activeDrag.modifiers),
            screen_position: [event.clientX, event.clientY],
            delta_pixels: [dx, dy],
            world_position: [worldPos.x, worldPos.y, worldPos.z],
            world_delta: worldDelta,
            drag_mode: dragMode,
        };

        const payload = _dragStarted
            ? () => ({ ...basePayload })  // drag_move: no camera
            : { ...basePayload, ...getCameraPayload(worldPos) };  // drag_start: include camera

        if (_dragStarted) {
            throttledSend(_activeDrag.objectId, 'drag_move', payload);
        } else {
            if (ws) ws.send(JSON.stringify(payload));
            _dragStarted = true;
        }
        event.preventDefault();
        return;
    }

    const hit = getInteractiveHit(event);
    const newHoveredId = hit ? hit.objectId : null;

    if (newHoveredId !== _hoveredObjectId) {
        // Reset previous hover
        if (_hoveredObjectId) {
            const prevObj = interactiveObjects.get(_hoveredObjectId);
            if (prevObj && prevObj.mesh) _resetHover(prevObj.mesh);
        }
        // Apply new hover
        if (newHoveredId) {
            const newObj = interactiveObjects.get(newHoveredId);
            if (newObj && newObj.mesh && newObj.config) {
                _applyHover(newObj.mesh, newObj.config);
            }
        }
        _hoveredObjectId = newHoveredId;
    }
}

function onPointerUp(event) {
    if (_activeDrag && _activeDrag.pointerId === event.pointerId) {
        const { dragMode, accWorldPos } = _activeDrag;

        // drag_end: no camera payload (backend cached it from drag_start)
        const payload = {
            type: 'interaction:drag_end',
            event_type: 'drag_end',
            object_id: _activeDrag.objectId,
            mouse_button: _activeDrag.button,
            modifiers: Array.from(_activeDrag.modifiers),
            screen_position: [event.clientX, event.clientY],
            delta_pixels: [
                event.clientX - _activeDrag.startPos.x,
                event.clientY - _activeDrag.startPos.y,
            ],
            world_position: [accWorldPos.x, accWorldPos.y, accWorldPos.z],
            world_delta: [0, 0, 0],
            drag_mode: dragMode,
        };
        if (ws) ws.send(JSON.stringify(payload));

        rendererDomElement.releasePointerCapture(event.pointerId);
        if (controls) controls.enabled = true;
        _activeDrag = null;
        _dragStarted = false;
        return;
    }

    const hit = getInteractiveHit(event);
    const objectId = hit ? hit.objectId : null;
    if (objectId) {
        const state = _clickState.get(objectId);
        if (state) {
            const dist = Math.hypot(
                event.clientX - state.pointerDownPos.x,
                event.clientY - state.pointerDownPos.y);
            const elapsed = performance.now() - state.pointerDownTime;

            if (dist < CLICK_THRESHOLD && elapsed < DBLCLICK_TIMEOUT) {
                const button = mouseButtonFromEvent(event);
                const modifiers = getActiveModifiers(event);
                const triggers = findMatchingTriggers(objectId, 'click', button, modifiers);
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
                        ...getCameraPayload(wp),
                    };
                    if (ws) ws.send(JSON.stringify(payload));
                }
            }
            _clickState.delete(objectId);
        }
    }
    if (_activeDrag) cancelDrag();
}

function onDblClick(event) {
    const hit = getInteractiveHit(event);
    if (!hit) return;
    const button = mouseButtonFromEvent(event);
    const modifiers = getActiveModifiers(event);
    const triggers = findMatchingTriggers(hit.objectId, 'dblclick', button, modifiers);
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
            ...getCameraPayload(wp),
        };
        if (ws) ws.send(JSON.stringify(payload));
    }
}

function onWheel(event) {
    const hit = getInteractiveHit(event);
    if (!hit) return;
    const modifiers = getActiveModifiers(event);
    const triggers = findMatchingTriggers(hit.objectId, 'scroll', null, modifiers);
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
            ...getCameraPayload(wp),
        });
        throttledSend(hit.objectId, 'scroll', payload);
    }
}

function onLostCapture() { if (_activeDrag) cancelDrag(); }

function cancelDrag() {
    if (_activeDrag) {
        if (_dragStarted && ws) {
            const payload = {
                type: 'interaction:drag_end',
                event_type: 'drag_end',
                object_id: _activeDrag.objectId,
                mouse_button: _activeDrag.button,
                modifiers: Array.from(_activeDrag.modifiers),
                screen_position: [_activeDrag.lastPos.x, _activeDrag.lastPos.y],
                delta_pixels: [0, 0],
                world_position: [0, 0, 0],
                world_delta: [0, 0, 0],
            };
            try { ws.send(JSON.stringify(payload)); } catch (e) {}
        }
        if (controls) controls.enabled = true;
        _activeDrag = null;
        _dragStarted = false;
    }
}