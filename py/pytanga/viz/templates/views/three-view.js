// Tanga Viewer — `ThreeJsView`: renders a single scene inside a View pane.
// Owns its Three.js scene/camera/renderer/controls, the per-scene object
// registry, and the per-scene message handling.  Extracted from viewer.js so
// the same logic can back the single-scene viewer and a split-view pane.

import * as THREE from 'three';
import { CSS2DRenderer } from 'three/addons/renderers/CSS2DRenderer.js';
import { View } from './view.js';
import { BannerView } from './banner-view.js';
import { setupControls } from '../controls.js';
import { createEntityMesh, removeEntityMesh, updateEntityMesh } from '../renderers/factory.js';
import { applyImageUniforms } from '../renderers/image.js';
import { createImageBackground, setBackgroundAspect, setBackgroundCrop } from '../renderers/image-background.js';
import { buildSceneObject, buildOverlay, removeObject, applyTransformToObject } from '../scene-builder.js';
import { startTween, updateTweens, cancelTween } from '../animator.js';
import { logForwardingEnabled, sendEvent, sendLog } from '../events.js';
import { attachGroupView, detachGroup, detachAll, releaseAttachedGroups } from '../controls-attached.js';
import { applyCameraLock, applyPinhole, createCamera, configureControls, fitCamera, handleResize, switchToCamera } from '../view_mode.js';
import { updateLineResolutions, applyStyleUpdate, entityRequiresRebuild } from '../renderers/utils.js';
import { InteractionController } from '../interaction.js';
import { AxesOverlay } from '../axes-overlay.js';
import { GridUnderlay } from '../grid-underlay.js';
import { clampOrthoView } from '../camera-fit.js';

// ── WebGL1 SDF fallback warning banner ──────────────────────
// SDF proxies need GLSL3 + `gl_FragDepth` (WebGL2). On WebGL1 those objects
// are skipped and a single yellow warning banner is shown (mirrors the
// version-mismatch banner pattern in viewer.js).

let _sdfWebGL2WarningShown = false;

function _showSdfWebGL2Warning() {
    if (_sdfWebGL2WarningShown) return;
    _sdfWebGL2WarningShown = true;

    const banner = document.createElement('div');
    banner.className = 'tanga-warning-banner';

    const text = document.createElement('span');
    text.textContent = 'SDF objects require WebGL2 — they are hidden in this viewer.';

    const btn = document.createElement('button');
    btn.textContent = 'Dismiss';
    btn.onclick = () => banner.remove();

    banner.appendChild(text);
    banner.appendChild(btn);
    document.body.insertBefore(banner, document.body.firstChild);
}

export function applyOverlayAnchor(el, anchor) {
    el.style.top = 'auto';
    el.style.right = 'auto';
    el.style.bottom = 'auto';
    el.style.left = 'auto';
    el.style.transform = '';
    switch (anchor) {
        case 'top-left':
            el.style.top = '8px';
            el.style.left = '8px';
            break;
        case 'top-right':
            // Stay clear of the fixed connection status dot + "Reconnect"
            // button that occupy the viewport's top-right corner.
            el.style.top = '36px';
            el.style.right = '8px';
            break;
        case 'bottom-left':
            el.style.bottom = '8px';
            el.style.left = '8px';
            break;
        case 'top':
            el.style.top = '8px';
            el.style.left = '50%';
            el.style.transform = 'translateX(-50%)';
            break;
        case 'bottom':
            el.style.bottom = '8px';
            el.style.left = '50%';
            el.style.transform = 'translateX(-50%)';
            break;
        case 'left':
            el.style.left = '8px';
            el.style.top = '50%';
            el.style.transform = 'translateY(-50%)';
            break;
        case 'right':
            el.style.right = '8px';
            el.style.top = '50%';
            el.style.transform = 'translateY(-50%)';
            break;
        case 'bottom-right':
        default:
            el.style.bottom = '8px';
            el.style.right = '8px';
            break;
    }
}

/** Renders a single named scene; `View` supplies extent + resize observation. */
export class ThreeJsView extends View {
    constructor(sceneName, ws = null, cameraOverride = null, viewId = null, lock = null, navigation = null, controls = null, viewport = null) {
        super();
        this.sceneName = sceneName || '';
        this._ws = ws;
        this._cameraOverride = cameraOverride || null;
        this.viewId = viewId || null;
        this._lock = lock || null;
        this._navigation = navigation || null;
        this._controls = controls || null;
        this._viewport = viewport || null;
        this._viewportDrag = null;
        this._browserId = null;
        this._interaction = null;

        this.sceneObjects = new Map(); // id → {obj, mesh, data, layer, el?}
        this.scene = new THREE.Scene();
        this.scene.fog = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.labelRenderer = null;
        this.sceneConfig = null;
        this._explicitBackground = null;
        this.cameraPositioned = false;
        this._titleElement = null;
        this._annotationPanel = null;
        this._overlays = [];
        this._pendingAttachedGroups = new Map(); // parent_id → [GroupView, …]
        this._banners = new Map();
        this._isWebGL2 = false;
        this._underlayEl = null;
        this._gridUnderlay = null;
        this._gridUnderlayId = null;
        this._axesOverlay = null;
        this._axesOverlayId = null;
        this._appliedInset = null;      // inset last applied to the camera/canvas
        this._backgroundImage = null;
        this._backgroundMesh = null;
        this._hide = new Set();
        this._show = null;

        this.el.classList.add('tanga-three-view');
        this.el.style.position = 'relative';
        this.el.style.overflow = 'hidden';
        this.el.style.width = '100%';
        this.el.style.height = '100%';

        this._initScene();
    }

    // ── context setters ────────────────────────────────────────

    setWebSocket(ws) {
        this._ws = ws;
        if (this._interaction) this._interaction.setWebSocket(ws);
    }
    setBrowserId(id) { this._browserId = id; }

    // ── overlay ─────────────────────────────────────────────────

    /**
     * Mount an overlay view (e.g. a `GroupView`) over the canvas, anchored by
     * its `position` (`top-left`/`top-right`/`bottom-left`/`bottom-right`).
     */
    addOverlay(view) {
        if (view.parent_id) {
            const parentMesh = this.sceneObjects.get(view.parent_id)?.obj;
            if (parentMesh) {
                attachGroupView(view, parentMesh);
            } else {
                // The layout arrives before the scene entities, so defer the
                // CSS2D attach until `_upsertObject` registers the parent mesh.
                const pending = this._pendingAttachedGroups.get(view.parent_id) || [];
                pending.push(view);
                this._pendingAttachedGroups.set(view.parent_id, pending);
                sendLog('debug', 'Deferring group attach until parent entity arrives', {
                    source: 'three-view.js',
                    data: { parent_id: view.parent_id },
                });
            }
            return view;
        }
        view.mount(this.el);
        const el = view.el;
        el.style.position = 'absolute';
        el.style.zIndex = '20';
        applyOverlayAnchor(el, view.position || 'bottom-right');
        this._overlays.push(view);
        return view;
    }

    /** Soft-release a mesh's attached groups and re-defer them for re-attach. */
    _redeferAttachedGroups(obj) {
        const released = releaseAttachedGroups(obj);
        for (const { groupView } of released) {
            const parentId = groupView.parent_id;
            const pending = this._pendingAttachedGroups.get(parentId) || [];
            pending.push(groupView);
            this._pendingAttachedGroups.set(parentId, pending);
        }
    }

    /** Attach any deferred groups waiting on entity id `id` to `obj`. */
    _attachPendingGroups(id, obj) {
        const pending = this._pendingAttachedGroups.get(id);
        if (!pending) return;
        for (const group of pending) attachGroupView(group, obj);
        this._pendingAttachedGroups.delete(id);
    }

    /** Remove and destroy all mounted overlay views (used when a scene pane is reused). */
    clearOverlays() {
        for (const view of this._overlays) {
            if (typeof view.unmount === 'function') view.unmount();
            if (typeof view.destroy === 'function') view.destroy();
        }
        this._overlays = [];
        // Detach CSS2D-attached groups belonging to this pane's objects so a
        // layout re-push that reuses the pane doesn't leak or double-attach.
        for (const entry of this.sceneObjects.values()) {
            if (entry.obj && entry.obj.userData._attachedGroups) {
                for (const groupId of entry.obj.userData._attachedGroups) {
                    detachGroup(groupId);
                }
            }
        }
        this._pendingAttachedGroups.clear();
        this._disposeCoordinateFrame();
    }

    _log(phase, detail) {
        const parts = ['[tanga:' + phase + ']'];
        if (this._browserId) parts.push('id=' + this._browserId);
        if (this.sceneName) parts.push('scene=' + this.sceneName);
        if (detail) parts.push(detail);
        console.log(parts.join(' '));
        if (logForwardingEnabled()) {
            sendLog('info', detail || phase, { source: 'three-view.js', data: { phase } });
        }
    }

    // ── scene setup ────────────────────────────────────────────

    _initScene() {
        this._underlayEl = document.createElement('div');
        this._underlayEl.className = 'tanga-underlay';
        this._underlayEl.style.position = 'absolute';
        this._underlayEl.style.top = '0';
        this._underlayEl.style.left = '0';
        this._underlayEl.style.width = '100%';
        this._underlayEl.style.height = '100%';
        this._underlayEl.style.pointerEvents = 'none';
        this._underlayEl.style.zIndex = '0';
        this.el.appendChild(this._underlayEl);

        let webglOk = true;
        try {
            this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
            this.renderer.setPixelRatio(window.devicePixelRatio);
            this.renderer.setSize(this.width || window.innerWidth, this.height || window.innerHeight);
            this.renderer.shadowMap.enabled = false;
            this.renderer.domElement.style.position = 'absolute';
            this.renderer.domElement.style.top = '0';
            this.renderer.domElement.style.left = '0';
            this.renderer.domElement.style.zIndex = '1';
            this.el.appendChild(this.renderer.domElement);
            this._isWebGL2 = !!this.renderer.capabilities.isWebGL2;
        } catch (e) {
            console.warn('WebGL renderer failed — falling back to headless mode:', e.message);
            sendLog('error', 'WebGL renderer failed — falling back to headless mode', { source: 'three-view.js', data: { error: e && e.message ? e.message : String(e) } });
            webglOk = false;
            this.renderer = null;
        }

        try {
            this.labelRenderer = new CSS2DRenderer();
            this.labelRenderer.setSize(this.width || window.innerWidth, this.height || window.innerHeight);
            this.labelRenderer.domElement.style.position = 'absolute';
            this.labelRenderer.domElement.style.top = '0px';
            this.labelRenderer.domElement.style.pointerEvents = 'none';
            this.labelRenderer.domElement.style.zIndex = '2';
            this.el.appendChild(this.labelRenderer.domElement);
        } catch (e) {
            this.labelRenderer = null;
        }

        this.camera = createCamera(
            this.sceneConfig?.space_dim || 3,
            (this.width || window.innerWidth) / Math.max(1, this.height || window.innerHeight)
        );

        this._addDefaultLights();

        if (webglOk && this.renderer) {
            this.controls = setupControls(this.camera, this.renderer);
            this.controls.addEventListener('change', () => this._syncViewportFromControls());
            this._bindViewportInput();
            this._interaction = new InteractionController(this.camera, this.renderer.domElement, this.controls, this._ws);
        }
    }

    _addDefaultLights() {
        this.scene.add(new THREE.AmbientLight(0xffffff, 0.5));
        const d1 = new THREE.DirectionalLight(0xffffff, 0.8);
        d1.position.set(10, 20, 10);
        this.scene.add(d1);
        const d2 = new THREE.DirectionalLight(0xffffff, 0.3);
        d2.position.set(-5, -2, -8);
        this.scene.add(d2);
    }

    // ── sizing / render ────────────────────────────────────────

    _onExtentChanged() { this.resize(); }

    /**
     * Height of the annotation panel, if any, in CSS pixels.
     */
    _annotationInset() {
        if (!this._annotationPanel) return 0;
        return Math.max(0, this._annotationPanel.offsetHeight || 0);
    }

    /**
     * Space reserved at the bottom of the pane so the coordinate frame + grid
     * (and the data they frame) sit above the annotation panel.  Only applies
     * when a coordinate frame overlay is mounted; a plain 3D annotation stays
     * a translucent overlay as before.
     */
    _frameInset() {
        if (!this._axesOverlay && !this._gridUnderlay) return 0;
        return this._annotationInset();
    }

    resize() {
        const width = this.width || window.innerWidth;
        const height = this.height || window.innerHeight;
        const inset = this._frameInset();
        const plotHeight = Math.max(1, height - inset);
        if (this.camera) {
            handleResize(this.camera, this.renderer, this.labelRenderer, this.sceneConfig?.space_dim || 3, width, plotHeight);
            this._applyViewport();
        }
        if (this._backgroundMesh && width > 0 && height > 0) {
            setBackgroundAspect(this._backgroundMesh, width / height);
        }
        this._appliedInset = inset;
        updateLineResolutions();
    }

    fitCamera() {
        if (!this.camera) return;
        fitCamera(this.sceneObjects, this.camera, this.controls,
            this.sceneConfig?.space_dim || 3,
            this.width || window.innerWidth, this.height || window.innerHeight);
    }

    render() {
        if (!this.renderer || !this.camera) return;
        if (this.controls) this.controls.update();
        clampOrthoView(this.camera, this.controls);
        updateTweens(this.sceneObjects);
        const width = this.width || window.innerWidth;
        const height = this.height || window.innerHeight;
        const inset = this._frameInset();
        // The annotation height can change (added/removed/KaTeX reflow), so
        // reframe the camera + canvas whenever it drifts from what we applied.
        if (inset !== this._appliedInset) this.resize();
        const cam = this._cameraParams();
        if (this._gridUnderlay) this._gridUnderlay.update(cam, width, height, inset);
        this.renderer.render(this.scene, this.camera);
        if (this._axesOverlay) this._axesOverlay.update(cam, width, height, inset);
        if (this.labelRenderer) this.labelRenderer.render(this.scene, this.camera);
    }

    _cameraParams() {
        const c = this.camera;
        return {
            left: c.left,
            right: c.right,
            top: c.top,
            bottom: c.bottom,
            zoom: c.zoom || 1,
            x: c.position.x,
            y: c.position.y,
        };
    }

    clearAll() {
        this._log('init', 'clear_all → resetting scene (objects=' + this.sceneObjects.size + ')');
        while (this.scene.children.length > 0) {
            const child = this.scene.children[0];
            this.scene.remove(child);
            if (child.geometry) child.geometry.dispose();
            if (child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach((m) => m.dispose());
                } else {
                    child.material.dispose();
                }
            }
        }
        if (this.labelRenderer && this.labelRenderer.domElement) {
            this.labelRenderer.domElement.innerHTML = '';
        }
        this._interaction.clearAllInteractive();
        this.sceneObjects.clear();
        this._removeAnnotation();
        if (this._titleElement) {
            this._titleElement.remove();
            this._titleElement = null;
        }
        detachAll();
        this._pendingAttachedGroups.clear();
        this._clearBanners();
        this._disposeCoordinateFrame();
        this.cameraPositioned = false;
        this._addDefaultLights();
    }

    // ── scene config / overlays ────────────────────────────────

    _applySceneConfig(config) {
        this.sceneConfig = config;
        const spaceDim = config.space_dim || 3;
        // A per-pane camera override (SceneView(scene, camera=…)) wins over the
        // scene's own camera; otherwise fall back to the scene config.
        const cameraConfig = this._cameraOverride || config.camera;

        if (config.background_color) {
            this._explicitBackground = config.background_color;
            this.scene.background = new THREE.Color(config.background_color);
        } else {
            this._explicitBackground = null;
            this.applyThemeBackground();
        }

        this._applyCamera(cameraConfig);

        this._reconfigureControls();
        this._interaction.setSpaceDim(spaceDim);
        this.resize();

        if (config.title !== undefined) {
            this._renderTitle(config.title);
            this.emit('titlechange', { title: config.title });
        }

        if (config.annotation) {
            this._renderAnnotation(config.annotation, null);
        } else if (config.annotation === '') {
            this._removeAnnotation();
        }

        this._interaction.setSceneCursor(config.cursor);
    }

    /**
     * Point this pane's scene background at the active theme's `--tanga-bg`
     * token.  A no-op when the scene config set an explicit `background_color`.
     */
    applyThemeBackground() {
        if (this._explicitBackground) return;
        const bg = getComputedStyle(document.documentElement)
            .getPropertyValue('--tanga-bg').trim();
        this.scene.background = bg ? new THREE.Color(bg) : null;
    }

    /**
     * Apply a camera config to this pane's camera + orbit controls.  Shared by
     * `_applySceneConfig` and `setCamera`.
     */
    _applyCamera(cameraConfig) {
        const spaceDim = (this.sceneConfig && this.sceneConfig.space_dim) || 3;
        const viewWidth = this.width > 0 ? this.width : null;
        const viewHeight = this.height > 0 ? this.height : null;

        this.camera = switchToCamera(this.camera, this.controls, spaceDim, cameraConfig || null, viewWidth, viewHeight);
        this._interaction.setCamera(this.camera);
        this.controls.update();
    }

    /**
     * Move this pane's camera at runtime (per-pane `view_camera` message).
     * Passing `null`/`undefined` reverts to the scene's own camera.
     */
    setCamera(cameraConfig) {
        this._cameraOverride = cameraConfig || null;
        const effective = this._cameraOverride || (this.sceneConfig && this.sceneConfig.camera);
        this._applyCamera(effective);
        this.resize();
    }

    /** Update this pane's camera lock and re-apply it to the controls. */
    setLock(lock) {
        this._lock = lock || null;
        if (this.controls) {
            applyCameraLock(this.controls, this._lock);
        }
    }

    /** Update this pane's navigation mode and re-apply the controls. */
    setNavigation(navigation) {
        this._navigation = navigation || null;
        this._reconfigureControls();
    }

    /** Update this pane's per-pane controls mapping and re-apply it. */
    setControls(controls) {
        this._controls = controls || null;
        this._reconfigureControls();
    }

    /** (Re)apply the navigation mode + button mapping + lock to the controls. */
    _reconfigureControls() {
        if (!this.controls || !this.renderer) return;
        const spaceDim = (this.sceneConfig && this.sceneConfig.space_dim) || 3;
        const sceneControls = (this.sceneConfig && this.sceneConfig.controls) || null;
        configureControls(
            this.controls, this.renderer, spaceDim,
            this._controls || sceneControls, this._navigation,
        );
        applyCameraLock(this.controls, this._lock);
        const pinhole2d = this._navigation === '2d' && this.camera && this.camera.userData._pinhole;
        if (pinhole2d) {
            // A calibrated camera pane is fixed in 3D; the viewport crop is
            // driven by the custom pointer handlers, so OrbitControls must not
            // move the camera.
            this.controls.enableRotate = false;
            this.controls.enablePan = false;
            this.controls.enableZoom = false;
        }
    }

    /**
     * Merge a partial `{zoom?, pan?}` viewport into this pane's viewport state
     * and re-apply it (per-pane `view_viewport` message).
     */
    setViewport(viewport) {
        const v = viewport || {};
        const cur = this._viewport || { zoom: 1, pan: [0, 0] };
        this._viewport = {
            zoom: v.zoom !== undefined ? Number(v.zoom) : cur.zoom,
            pan: v.pan !== undefined ? [Number(v.pan[0]), Number(v.pan[1])] : cur.pan,
        };
        this._applyViewport();
    }

    /** Apply this pane's viewport (zoom + pan) to the camera. */
    _applyViewport() {
        if (!this.camera) return;
        const vp = this._viewport;
        if (this.camera.userData._pinhole) {
            // Pinhole framing is the single source for projection + background;
            // the crop window is folded in by `_applyPinholeFraming` (Phase 6).
            this._applyPinholeFraming(vp);
            return;
        }
        if (!vp) {
            this.camera.zoom = 1;
            this.camera.clearViewOffset();
            this.camera.updateProjectionMatrix();
            return;
        }
        this.camera.zoom = vp.zoom;
        const w = this.width || 1;
        const h = this.height || 1;
        // Pan shifts the rendered window opposite the drag (screen-space).
        this.camera.setViewOffset(
            w, h,
            -(vp.pan[0] || 0) * w / 2,
            -(vp.pan[1] || 0) * h / 2,
            w, h,
        );
        this.camera.updateProjectionMatrix();
    }

    /** Fold the viewport crop into the pinhole framing + background image. */
    _applyPinholeFraming(vp) {
        const p = this.camera && this.camera.userData._pinhole;
        if (!p) return;
        const crop = vp ? { zoom: vp.zoom, pan: vp.pan } : null;
        const aspect = (this.width || 1) / Math.max(1, this.height || 1);
        applyPinhole(this.camera, p, aspect, crop);
        if (this._backgroundMesh) {
            setBackgroundCrop(this._backgroundMesh, this.camera.userData._pinholeCrop || null);
        }
    }

    /**
     * OrbitControls-driven gesture → keep the viewport state in sync for the
     * non-pinhole `"2d"` case (the calibrated-camera crop is handled by the
     * custom pointer handlers below).
     */
    _syncViewportFromControls() {
        if (this._navigation !== '2d' || !this.camera) return;
        if (this.camera.userData._pinhole) return;
        const cur = this._viewport || { zoom: 1, pan: [0, 0] };
        this._viewport = { zoom: this.camera.zoom || 1, pan: cur.pan };
    }

    // ── 2D viewport crop input (calibrated camera panes) ────────────────

    /** Install wheel + drag handlers that drive the pinhole crop window. */
    _bindViewportInput() {
        const el = this.renderer && this.renderer.domElement;
        if (!el) return;
        el.addEventListener('wheel', (e) => this._onViewportWheel(e), { passive: false });
        el.addEventListener('pointerdown', (e) => this._onViewportPointerDown(e));
        el.addEventListener('pointermove', (e) => this._onViewportPointerMove(e));
        el.addEventListener('pointerup', (e) => this._onViewportPointerUp(e));
        el.addEventListener('pointercancel', (e) => this._onViewportPointerUp(e));
    }

    /** The crop input only applies to a fixed calibrated camera pane. */
    _viewportInputEnabled() {
        return this._navigation === '2d' && !!this.camera && !!this.camera.userData._pinhole;
    }

    /** Pointer position in pane-NDC: x right=+1, y bottom=+1 (image v-down). */
    _screenNdc(e) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        const ny = ((e.clientY - rect.top) / rect.height) * 2 - 1;
        return [nx, ny];
    }

    _onViewportWheel(e) {
        if (!this._viewportInputEnabled()) return;
        e.preventDefault();
        const delta = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
        const [nx, ny] = this._screenNdc(e);
        this._zoomViewport(nx, ny, Math.exp(-delta * 0.0015));
    }

    _onViewportPointerDown(e) {
        if (!this._viewportInputEnabled()) return;
        const [nx, ny] = this._screenNdc(e);
        this._viewportDrag = { nx, ny, pointerId: e.pointerId };
        this.renderer.domElement.setPointerCapture(e.pointerId);
    }

    _onViewportPointerMove(e) {
        if (!this._viewportDrag || e.pointerId !== this._viewportDrag.pointerId) return;
        const [nx, ny] = this._screenNdc(e);
        const dnx = nx - this._viewportDrag.nx;
        const dny = ny - this._viewportDrag.ny;
        this._viewportDrag = { nx, ny, pointerId: e.pointerId };
        this._panViewport(dnx, dny);
    }

    _onViewportPointerUp(e) {
        if (this._viewportDrag && e.pointerId === this._viewportDrag.pointerId) {
            this._viewportDrag = null;
        }
    }

    /** Clamp `pan` so the crop window stays inside the image extent. */
    _clampPan(pan, zoom) {
        const lim = 1 - 1 / zoom;
        return [
            Math.min(lim, Math.max(-lim, pan[0])),
            Math.min(lim, Math.max(-lim, pan[1])),
        ];
    }

    /** Cursor-anchored zoom: keep the image point under `(nx, ny)` fixed. */
    _zoomViewport(nx, ny, factor) {
        const vp = this._viewport || { zoom: 1, pan: [0, 0] };
        const newZoom = Math.min(1000, Math.max(1, vp.zoom * factor));
        if (newZoom === vp.zoom) return;
        const k = 1 / vp.zoom - 1 / newZoom;
        this._viewport = {
            zoom: newZoom,
            pan: this._clampPan([vp.pan[0] + nx * k, vp.pan[1] + ny * k], newZoom),
        };
        this._applyViewport();
    }

    /** Drag pan: shift the crop opposite the pointer (grab-and-pan). */
    _panViewport(dnx, dny) {
        const vp = this._viewport || { zoom: 1, pan: [0, 0] };
        const z = vp.zoom || 1;
        this._viewport = {
            zoom: vp.zoom,
            pan: this._clampPan([vp.pan[0] - dnx / z, vp.pan[1] - dny / z], z),
        };
        this._applyViewport();
    }

    /** Mount (or clear) this pane's full-viewport background image. */
    setBackgroundImage(imageMeta) {
        this._backgroundImage = imageMeta || null;
        if (this._backgroundMesh) {
            this.scene.remove(this._backgroundMesh);
            this._backgroundMesh = null;
        }
        if (this._backgroundImage) {
            this._backgroundMesh = createImageBackground(this._backgroundImage);
            this.scene.add(this._backgroundMesh);
        }
    }

    /** Set this pane's entity visibility filter (per-pane ``hide``/``show``). */
    setVisibilityFilter(hide, show) {
        this._hide = new Set(hide || []);
        this._show = show && show.length ? new Set(show) : null;
    }

    /** Refresh this reused pane from a serialized ``scene_view`` node. */
    updateFromNode(node) {
        const camView = node.camera_view || {};
        this.clearOverlays();
        this.setLock(camView.lock || null);
        this.setNavigation(camView.navigation || null);
        this.setControls(camView.controls || null);
        this.setViewport(camView.viewport || null);
        this.setBackgroundImage(camView.background_image || null);
        this.setVisibilityFilter(node.hide || null, node.show || null);
    }

    _isFilteredOut(id) {
        if (this._hide.has(id)) return true;
        return this._show !== null && !this._show.has(id);
    }

    _renderTitle(titleText) {
        if (!this._titleElement) {
            this._titleElement = document.createElement('div');
            this._titleElement.className = 'tanga-title-overlay';
            this._titleElement.style.position = 'absolute';
            this._titleElement.style.top = '10px';
            this._titleElement.style.left = '50%';
            this._titleElement.style.transform = 'translateX(-50%)';
            this.el.appendChild(this._titleElement);
        }
        this._titleElement.textContent = '';
        this._titleElement.innerHTML = titleText;
        if (typeof renderMathInElement !== 'undefined') {
            try {
                renderMathInElement(this._titleElement, {
                    delimiters: [
                        { left: '$$', right: '$$', display: true },
                        { left: '$', right: '$', display: false },
                    ],
                    throwOnError: false,
                });
            } catch (e) { /* ignore */ }
        }
    }

    _renderAnnotation(mdText, styleData) {
        this._removeAnnotation();

        const s = styleData || {};
        const container = document.createElement('div');

        if (typeof marked !== 'undefined') {
            container.innerHTML = marked.parse(mdText, { breaks: true });
        } else {
            container.textContent = mdText;
        }

        if (typeof renderMathInElement !== 'undefined') {
            try {
                renderMathInElement(container, {
                    delimiters: [
                        { left: '$$', right: '$$', display: true },
                        { left: '$', right: '$', display: false },
                    ],
                    throwOnError: false,
                });
            } catch (e) {
                console.warn('KaTeX rendering error:', e);
            }
        }

        container.style.position = 'absolute';
        container.style.bottom = '0px';
        container.style.left = '0px';
        container.style.right = '0px';
        container.style.width = s.width || '100%';
        container.style.maxWidth = s.max_width || 'none';
        container.style.maxHeight = s.max_height || '250px';
        container.style.overflowY = 'auto';
        container.style.fontFamily = s.font_family || 'sans-serif';
        container.style.fontSize = (s.font_size || 13) + 'px';
        container.style.color = s.color || '#cccccc';
        container.style.backgroundColor = s.background || 'rgba(0, 0, 0, 0.75)';
        container.style.padding = s.padding || '10px 16px';
        container.style.borderRadius = s.border_radius || '4px';
        container.style.zIndex = '5';
        container.style.lineHeight = '1.5';
        container.className = 'annotation-container';

        const linkColor = s.link_color || '#88ccff';
        const codeBg = s.code_background || 'rgba(255,255,255,0.1)';
        const styleEl = document.createElement('style');
        styleEl.textContent = `
            .annotation-container h1, .annotation-container h2, .annotation-container h3,
            .annotation-container h4, .annotation-container h5, .annotation-container h6 {
                margin-top: 0.6em; margin-bottom: 0.3em;
            }
            .annotation-container h1 { font-size: 1.3em; }
            .annotation-container h2 { font-size: 1.15em; }
            .annotation-container h3 { font-size: 1.05em; }
            .annotation-container p { margin: 0.3em 0; }
            .annotation-container a { color: ${linkColor}; }
            .annotation-container code {
                background: ${codeBg}; padding: 1px 4px; border-radius: 3px;
            }
            .annotation-container pre {
                background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; overflow-x: auto;
            }
            .annotation-container hr {
                border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 0.5em 0;
            }
        `;
        container.appendChild(styleEl);

        this.el.appendChild(container);
        this._annotationPanel = container;
    }

    _removeAnnotation() {
        if (this._annotationPanel) {
            this._annotationPanel.remove();
            this._annotationPanel = null;
        }
    }

    // ── per-scene message handling ─────────────────────────────

    async handleMessage(msg) {
        if (msg.type === 'clear_all') {
            this.clearAll();
        } else if (msg.type === 'scene_config') {
            this._log('init', 'scene_config name=' + (msg.name || '') + ' space_dim=' + msg.space_dim);
            this._applySceneConfig(msg);
        } else if (msg.type === 'scene_update') {
            this._log('init', 'scene_update objects=' + (msg.objects ? msg.objects.length : 0) + ' removed=' + (msg.removed ? msg.removed.length : 0));
            if (msg.removed) {
                for (const id of msg.removed) this._removeSceneObject(id);
            }
            if (msg.objects) {
                for (const obj of msg.objects) await this._upsertObject(obj);
            }
            if (msg.fit_camera) this.fitCamera();
            if (this._ws && this._ws.readyState === WebSocket.OPEN) {
                this._log('ws-send', 'type=scene_synced browser_id=' + this._browserId);
                this._ws.send(JSON.stringify({ type: 'scene_synced', browser_id: this._browserId }));
            }
        } else if (msg.type === 'object_update') {
            if (msg.removed) {
                for (const id of msg.removed) this._removeSceneObject(id);
            }
            if (msg.patches) {
                for (const patch of msg.patches) await this._applyObjectPatch(patch);
            }
            if (msg.fit_camera) this.fitCamera();
        } else if (msg.type === 'animate') {
            this._handleAnimate(msg);
        } else if (msg.type === 'timeline') {
            this._handleTimeline(msg);
        } else if (msg.type === 'banner_define') {
            this._showBanner(msg);
        } else if (msg.type === 'banner_remove') {
            this._removeBanner(msg.id);
        } else if (msg.type === 'banner_clear') {
            this._clearBanners();
        } else if (msg.type === 'interaction:drag_anchor') {
            this._interaction.setDragAnchor(msg.object_id, msg.world_position);
        } else if (msg.type === 'image_update') {
            const entry = this.sceneObjects.get(msg.id);
            if (entry && entry.mesh) applyImageUniforms(entry.mesh, msg.uniforms);
        }
    }

    _showBanner(msg) {
        this._removeBanner(msg.id);
        const view = new BannerView({
            id: msg.id,
            title: msg.title,
            text: msg.text,
            align_x: msg.align_x,
            align_y: msg.align_y,
            auto_hide: msg.auto_hide,
            dismissable: msg.dismissable,
            controls: msg.controls || [],
            backdropMode: 'absolute',
            onClose: (id) => this._sendBannerClosed(id),
        });
        this._banners.set(msg.id, view);
        view.mount(this.el);
    }

    _removeBanner(id) {
        const view = this._banners.get(id);
        if (!view) return;
        this._banners.delete(id);
        view.destroy();
    }

    _clearBanners() {
        for (const id of [...this._banners.keys()]) this._removeBanner(id);
    }

    _sendBannerClosed(id) {
        sendEvent(id, 'close');
    }

    async _upsertObject(msg) {
        const old = this.sceneObjects.get(msg.id);
        if (old) {
            if (old.layer === 'scene' && old.obj) {
                this._redeferAttachedGroups(old.obj);
                removeEntityMesh(old.obj);
            } else if (old.obj && old.obj.removeFromParent) {
                old.obj.removeFromParent();
            }
            if (old.el) old.el.remove();
            this.sceneObjects.delete(msg.id);
        }
        if (msg.layer === 'scene') {
            // Per-pane visibility filter (SceneView.hide / SceneView.show).
            if (this._isFilteredOut(msg.id)) {
                return;
            }
            // SDF proxies require WebGL2 (GLSL3 + gl_FragDepth); on WebGL1 they
            // are skipped and a single yellow warning banner is shown.
            if (msg.kind === 'sdf' && !this._isWebGL2) {
                _showSdfWebGL2Warning();
                return;
            }
            const entry = await buildSceneObject(msg, this.scene, this.sceneObjects);
            if (entry && entry.obj) {
                this._attachPendingGroups(msg.id, entry.obj);
            }
            if (entry && msg.interaction) {
                this._interaction.registerInteractive(msg.id, entry.obj, msg.interaction);
            }
        } else if (msg.layer === 'overlay') {
            if (msg.kind === 'annotation') {
                if (!msg.text) return;
                this._renderAnnotation(msg.text, msg.style || null);
                if (this._annotationPanel) {
                    this.sceneObjects.set(msg.id, { obj: null, mesh: null, data: { ...msg }, el: this._annotationPanel, layer: 'overlay' });
                }
                return;
            }
            if (msg.kind === 'axes_overlay') {
                if (this._axesOverlay) {
                    this._axesOverlay.setSpec(msg.spec);
                } else {
                    this._axesOverlay = new AxesOverlay(msg.spec);
                    this._axesOverlay.mount(this.el);
                }
                this._axesOverlayId = msg.id;
                this.sceneObjects.set(msg.id, { obj: null, mesh: null, data: { ...msg }, layer: 'overlay' });
                return;
            }
            buildOverlay(msg, this.scene, this.sceneObjects);
        } else if (msg.layer === 'underlay') {
            if (msg.kind === 'grid_underlay') {
                if (this._gridUnderlay) {
                    this._gridUnderlay.setSpec(msg.spec);
                } else {
                    this._gridUnderlay = new GridUnderlay(msg.spec);
                    this._gridUnderlay.mount(this._underlayEl);
                }
                this._gridUnderlayId = msg.id;
                this.sceneObjects.set(msg.id, { obj: null, mesh: null, data: { ...msg }, layer: 'underlay' });
                this._updateOverlayTransparency();
                return;
            }
        }
    }

    _updateOverlayTransparency() {
        if (this._gridUnderlay) {
            this.scene.background = null;
        } else {
            this.applyThemeBackground();
        }
    }

    _disposeCoordinateFrame() {
        if (this._axesOverlay) {
            this._axesOverlay.dispose();
            this._axesOverlay = null;
            this._axesOverlayId = null;
        }
        if (this._gridUnderlay) {
            this._gridUnderlay.dispose();
            this._gridUnderlay = null;
            this._gridUnderlayId = null;
        }
        this._updateOverlayTransparency();
    }

    _removeSceneObject(id) {
        this._interaction.unregisterInteractive(id);
        const entry = this.sceneObjects.get(id);
        if (entry && entry.layer === 'scene' && entry.obj && entry.obj.userData._attachedGroups) {
            for (const groupId of entry.obj.userData._attachedGroups) {
                detachGroup(groupId);
            }
        }
        if (id === this._axesOverlayId) {
            if (this._axesOverlay) this._axesOverlay.dispose();
            this._axesOverlay = null;
            this._axesOverlayId = null;
        }
        if (id === this._gridUnderlayId) {
            if (this._gridUnderlay) this._gridUnderlay.dispose();
            this._gridUnderlay = null;
            this._gridUnderlayId = null;
            this._updateOverlayTransparency();
        }
        removeObject(id, this.sceneObjects);
        cancelTween(id);
    }

    async _applyObjectPatch(patch) {
        const id = patch.id;
        const aspect = patch.aspect;
        const value = patch.value || {};

        if (aspect === 'full') {
            await this._upsertObject(value);
            return;
        }
        if (aspect === 'interaction') {
            this._interaction.unregisterInteractive(id);
            const intEntry = this.sceneObjects.get(id);
            if (intEntry && intEntry.obj && value.interaction) {
                this._interaction.registerInteractive(id, intEntry.obj, value.interaction);
            }
            return;
        }
        const entry = this.sceneObjects.get(id);
        if (!entry) return;

        if (aspect === 'content') {
            await this._updateEntityContent(id, value);
            return;
        }
        if (aspect === 'transform') {
            if (entry.obj) applyTransformToObject(entry.obj, value);
            return;
        }
        if (aspect === 'visible') {
            if (entry.obj) entry.obj.visible = value.visible !== false;
            return;
        }
        if (aspect === 'style') {
            if (value.style && entry.obj) {
                const prev = entry.data || {};
                const merged = { ...prev, style: { ...(prev.style || {}), ...value.style } };
                if (entityRequiresRebuild(merged, prev)) {
                    await this._updateEntityContent(id, merged);
                } else {
                    entry.data = merged;
                    if (entry.obj.isObject3D) applyStyleUpdate(entry.obj, merged);
                }
            }
        }
    }

    async _updateEntityContent(id, content) {
        const entry = this.sceneObjects.get(id);
        if (!entry || entry.layer !== 'scene' || !entry.mesh) return;
        const prev = entry.data || {};

        if (updateEntityMesh(entry.mesh, content, prev)) {
            entry.data = { ...prev, ...content };
            return;
        }

        const newMesh = await createEntityMesh({ ...prev, ...content });
        if (!newMesh) return;

        if (entry.obj === entry.mesh) {
            const attachedLabels = (entry.obj.userData._labels || []).slice();
            const parent = entry.obj.parent;
            this._redeferAttachedGroups(entry.obj);
            removeEntityMesh(entry.obj);
            entry.obj = newMesh;
            entry.mesh = newMesh;
            newMesh.userData.parentId = prev.parent_id || null;
            newMesh.userData._labels = [];
            if (parent) parent.add(newMesh); else this.scene.add(newMesh);
            for (const lblId of attachedLabels) {
                const lblEntry = this.sceneObjects.get(lblId);
                if (lblEntry && lblEntry.obj) {
                    newMesh.add(lblEntry.obj);
                    newMesh.userData._labels.push(lblId);
                }
            }
            this._attachPendingGroups(id, newMesh);
        } else {
            removeEntityMesh(entry.mesh);
            entry.obj.add(newMesh);
            entry.mesh = newMesh;
        }
        entry.data = { ...prev, ...content };
        if (prev.interaction) {
            this._interaction.registerInteractive(id, entry.obj, prev.interaction);
        }
    }

    _handleAnimate(msg) {
        if (!msg.animations) return;
        for (const anim of msg.animations) {
            startTween(anim.id, anim.target, anim.duration || 1.0, anim.easing || 'ease-in-out', this.sceneObjects);
        }
    }

    _handleTimeline(msg) {
        if (!msg.steps) return;
        for (const step of msg.steps) {
            const delay = (step.at || 0) * 1000;
            setTimeout(() => {
                this._handleAnimate({ animations: [step.animate] });
            }, delay);
        }
    }
}
