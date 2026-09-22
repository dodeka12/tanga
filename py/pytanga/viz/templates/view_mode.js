// Tanga Viewer — Dimension‑specific camera, controls, and rendering helpers.
// All space_dim‑dependent logic lives here; viewer.js calls these functions
// unconditionally.  No conditionals elsewhere in the codebase.

import * as THREE from 'three';

import { finiteAspect, orthoFrustum, applyOrthoFrustum } from './camera-fit.js';
import { pinholeFraming } from './pinhole-framing.js';

/**
 * Create a camera appropriate for the given space dimension.
 *
 * @param {number} spaceDim  2 or 3
 * @param {number} aspect    window.innerWidth / window.innerHeight
 * @returns {THREE.Camera}
 */
export function createCamera(spaceDim, aspect) {
    // Always start with 3D perspective — switchToCamera() is called
    // from applySceneConfig() once sceneConfig arrives.
    const camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 1000);
    camera.position.set(6, 4.5, 7.5);
    camera.lookAt(0, 0, 0);
    return camera;
}

function _newOrthographic() {
    return new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 1000);
}

function _newPerspective(aspect, fov = 50) {
    return new THREE.PerspectiveCamera(fov, aspect, 0.1, 1000);
}

// Set an off-center perspective projection from stored pinhole intrinsics, and
// keep `projectionMatrixInverse` in sync so interaction raycasts stay correct.
// This is the single rebuild path used by both `switchToCamera` and `handleResize`.
export function applyPinhole(camera, p, aspect, crop) {
    const f = pinholeFraming(
        p.fx, p.fy, p.cx, p.cy, p.width, p.height, p.near, p.far, aspect, p.fit || 'fit', crop || null
    );
    camera.projectionMatrix.makePerspective(f.left, f.right, f.top, f.bottom, f.near, f.far);
    camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
    camera.userData._pinholeCrop = f.crop;
}

/**
 * Apply the camera described by ``cameraConfig`` to the scene.
 *
 * The config carries a ``type`` discriminator (``"2d"`` or ``"3d"``) rather
 * than the old ``view_2d`` / ``view_plane`` specs.  The 2D case carries an
 * orthographic world rectangle plus a scaling policy; the 3D case carries a
 * precomputed perspective camera (position / target / up / fov / clipping).
 *
 * Handles three cases:
 *   - ``type === "2d"``: orthographic view from a world rectangle.
 *   - ``type === "3d"``: perspective camera (precomputed on the backend).
 *   - otherwise: fall back to an orthographic 2D view when ``spaceDim`` is 2.
 *
 * @param {THREE.Camera} camera
 * @param {THREE.OrbitControls} controls
 * @param {number} spaceDim  2 or 3
 * @param {object|null} cameraConfig  normalized ``camera`` config dict
 * @param {number|null} viewWidth  pane width in CSS px; falls back to the window
 *   width when null/non-finite.
 * @param {number|null} viewHeight  pane height in CSS px; falls back to the window
 *   height when null/non-finite.
 * @returns {THREE.Camera} the (possibly replaced) camera
 */
export function switchToCamera(camera, controls, spaceDim, cameraConfig, viewWidth = null, viewHeight = null) {
    const cc = cameraConfig || {};
    const w = (Number.isFinite(viewWidth) && viewWidth > 0) ? viewWidth : window.innerWidth;
    const h = (Number.isFinite(viewHeight) && viewHeight > 0) ? viewHeight : window.innerHeight;
    const aspect = finiteAspect(w, h);

    // ── 2D orthographic ──
    if (cc.type === '2d') {
        const xmin = cc.xmin ?? 0;
        const xmax = cc.xmax ?? 0;
        const ymin = cc.ymin ?? 0;
        const ymax = cc.ymax ?? 0;
        const cx = (xmin + xmax) / 2;
        const cy = (ymin + ymax) / 2;
        const stretch = cc.stretch || 'fit';  // default letterbox
        const borderPx = cc.border_px || 0;

        let cam = camera;
        if (!cam.isOrthographicCamera) {
            cam = _newOrthographic();
            controls.object = cam;
        }

        const f = orthoFrustum(xmin, xmax, ymin, ymax, stretch, borderPx, w, h);
        cam.left = f.left;
        cam.right = f.right;
        cam.top = f.top;
        cam.bottom = f.bottom;

        cam.near = cc.near || 0.1;
        cam.far = cc.far || 1000;
        cam.position.set(
            cc.position ? cc.position[0] : cx,
            cc.position ? cc.position[1] : cy,
            cc.position ? cc.position[2] : 20
        );
        cam.lookAt(
            cc.target ? cc.target[0] : cx,
            cc.target ? cc.target[1] : cy,
            cc.target ? cc.target[2] : 0
        );
        cam.updateProjectionMatrix();
        cam.userData._view2d = {
            xmin, xmax, ymin, ymax, stretch, border_px: borderPx,
            pan_xmin: cc.pan_xmin, pan_xmax: cc.pan_xmax,
            pan_ymin: cc.pan_ymin, pan_ymax: cc.pan_ymax,
            min_zoom: cc.min_zoom, max_zoom: cc.max_zoom,
        };
        controls.target.set(
            cc.target ? cc.target[0] : cx,
            cc.target ? cc.target[1] : cy,
            cc.target ? cc.target[2] : 0
        );
        controls.update();
        return cam;
    }

    // ── 3D perspective ──
    if (cc.type === '3d') {
        const fov = cc.fov || 50;

        let cam = camera;
        if (cam.isOrthographicCamera) {
            cam = _newPerspective(aspect, fov);
            controls.object = cam;
        }

        // Explicit projective camera placement.  This is a free 3D camera:
        // the user can orbit (rotate), pan, and zoom via OrbitControls.
        cam.fov = fov;
        cam.aspect = aspect;
        if (cc.near) cam.near = cc.near;
        if (cc.far) cam.far = cc.far;
        if (cc.up) cam.up.set(cc.up[0], cc.up[1], cc.up[2]);
        if (cc.position) cam.position.set(cc.position[0], cc.position[1], cc.position[2]);
        if (cc.target) {
            cam.lookAt(cc.target[0], cc.target[1], cc.target[2]);
            controls.target.set(cc.target[0], cc.target[1], cc.target[2]);
        }
        cam.updateProjectionMatrix();
        controls.update();
        return cam;
    }

    // ── Calibrated pinhole (off-center projection) ──
    if (cc.type === 'pinhole') {
        let cam = camera;
        if (cam.isOrthographicCamera) {
            cam = _newPerspective(aspect, 50);
            controls.object = cam;
        }

        const pinhole = {
            fx: cc.fx, fy: cc.fy, cx: cc.cx, cy: cc.cy,
            width: cc.width, height: cc.height,
            near: cc.near || 0.1, far: cc.far || 1000,
            fit: cc.fit || 'fit',
        };
        cam.userData._pinhole = pinhole;
        cam.aspect = aspect;
        cam.near = pinhole.near;
        cam.far = pinhole.far;
        if (cc.up) cam.up.set(cc.up[0], cc.up[1], cc.up[2]);
        if (cc.position) cam.position.set(cc.position[0], cc.position[1], cc.position[2]);
        if (cc.target) {
            cam.lookAt(cc.target[0], cc.target[1], cc.target[2]);
            controls.target.set(cc.target[0], cc.target[1], cc.target[2]);
        }
        applyPinhole(cam, pinhole, aspect);
        controls.update();
        return cam;
    }

    // ── Default 2D (no explicit view config) ──
    if (spaceDim === 2 && !camera.isOrthographicCamera) {
        const frustumSize = 20;  // sensible default full height
        const safeAspect = Number.isFinite(aspect) ? aspect : 1.0;
        const newCam = _newOrthographic();
        newCam.left = frustumSize * safeAspect / -2;
        newCam.right = frustumSize * safeAspect / 2;
        newCam.top = frustumSize / 2;
        newCam.bottom = frustumSize / -2;
        newCam.position.set(0, 0, 20);
        newCam.lookAt(0, 0, 0);
        newCam.updateProjectionMatrix();
        newCam.userData._view2d = {
            xmin: -frustumSize * safeAspect / 2,
            xmax: frustumSize * safeAspect / 2,
            ymin: -frustumSize / 2,
            ymax: frustumSize / 2,
            stretch: 'fit',
            border_px: 0,
        };
        controls.object = newCam;
        return newCam;
    }

    // ── Default 3D (no explicit view config) ──
    if (spaceDim === 3 && camera.isOrthographicCamera) {
        const newCam = _newPerspective(aspect, 50);
        newCam.position.set(6, 4.5, 7.5);
        newCam.lookAt(0, 0, 0);
        newCam.updateProjectionMatrix();
        controls.object = newCam;
        return newCam;
    }

    return camera;
}

/**
 * Configure controls and renderer for the given space dimension.
 * Called from applySceneConfig() after the config arrives.
 *
 * @param {THREE.OrbitControls} controls
 * @param {THREE.WebGLRenderer} renderer
 * @param {number} spaceDim  2 or 3
 * @param {object|null} controlsConfig  optional per-button overrides, e.g.
 *   { left: "pan", right: "dolly" } (a ``null`` value disables a button)
 */
export function configureControls(controls, renderer, spaceDim, controlsConfig, navigation) {
    // Action string → THREE.MOUSE code.
    const ACTION = {
        rotate: THREE.MOUSE.ROTATE,
        dolly: THREE.MOUSE.DOLLY,
        pan: THREE.MOUSE.PAN
    };
    const nav2d = navigation === '2d';
    // Per-dimension defaults; a scene-level `controls` config overrides
    // individual buttons (a `null` value disables that button).  A pane in
    // `"2d"` navigation swaps rotate for pan (dolly + screen-space pan, no
    // orbit).
    const defaults = (spaceDim === 2 || nav2d)
        ? { left: 'pan', middle: 'dolly', right: 'pan' }
        : { left: 'rotate', middle: 'dolly', right: 'pan' };
    const mapping = { ...defaults, ...(controlsConfig || {}) };

    // Note: use `??` (not `||`) — THREE.MOUSE.ROTATE is 0, which is falsy, so
    // `|| null` would silently disable the left-mouse rotation in 3D scenes.
    controls.mouseButtons = {
        LEFT: ACTION[mapping.left] ?? null,
        MIDDLE: ACTION[mapping.middle] ?? null,
        RIGHT: ACTION[mapping.right] ?? null
    };

    const actions = Object.values(mapping);
    controls.enableRotate = actions.includes('rotate');
    controls.enablePan = actions.includes('pan');

    if (spaceDim === 2) {
        controls.zoomToCursor = true;
    } else {
        controls.screenSpacePanning = true;
    }
    if (nav2d) {
        controls.enableRotate = false;
        controls.zoomToCursor = true;
        controls.screenSpacePanning = true;
    }
}

/**
 * Fix parts of a pane's camera by disabling the matching OrbitControls action.
 * Called after ``configureControls`` for panes that carry a ``SceneView.lock``.
 *
 * @param {THREE.OrbitControls} controls
 * @param {string[]|null} lock  e.g. `["rotate", "pan", "zoom"]`
 */
export function applyCameraLock(controls, lock) {
    const locked = new Set(lock || []);
    if (locked.has('rotate')) controls.enableRotate = false;
    if (locked.has('pan')) controls.enablePan = false;
    controls.enableZoom = !locked.has('zoom');
}

export { fitCamera } from './fit_camera.js';

/**
 * Handle a viewport resize.  Recomputes 2D orthographic frusta from the new
 * aspect ratio and keeps every camera's aspect updated.  The size is passed in
 * explicitly (from a ResizeObserver / window event) rather than read from
 * ``window``, and non-finite sizes are ignored so a not-yet-laid-out container
 * can never corrupt the frustum.
 *
 * @param {THREE.Camera} camera
 * @param {THREE.WebGLRenderer} renderer
 * @param {object|null} labelRenderer  window._labelRenderer
 * @param {number} spaceDim  2 or 3
 * @param {number} width   renderer width in CSS pixels
 * @param {number} height  renderer height in CSS pixels
 */
export function handleResize(camera, renderer, labelRenderer, spaceDim, width, height) {
    const aspect = finiteAspect(width, height);
    if (!Number.isFinite(aspect)) return;

    if (spaceDim === 2 && camera.isOrthographicCamera) {
        applyOrthoFrustum(camera, width, height);
    }

    camera.aspect = aspect;
    if (camera.userData._pinhole) {
        applyPinhole(camera, camera.userData._pinhole, aspect);
    } else {
        camera.updateProjectionMatrix();
    }
    renderer.setSize(width, height);

    if (labelRenderer) {
        labelRenderer.setSize(width, height);
    }
}

