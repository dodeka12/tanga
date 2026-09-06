// Tanga Viewer — Dimension‑specific camera, controls, and rendering helpers.
// All space_dim‑dependent logic lives here; viewer.js calls these functions
// unconditionally.  No conditionals elsewhere in the codebase.

import * as THREE from 'three';

import { finiteAspect, orthoFrustum, applyOrthoFrustum } from './camera-fit.js';

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
        cam.userData._view2d = { xmin, xmax, ymin, ymax, stretch, border_px: borderPx };
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
 */
export function configureControls(controls, renderer, spaceDim) {
    if (spaceDim === 2) {
        controls.enableRotate = false;
        controls.mouseButtons = {
            LEFT: THREE.MOUSE.PAN,
            MIDDLE: THREE.MOUSE.DOLLY,
            RIGHT: THREE.MOUSE.PAN
        };
        return;
    }
    // 3D: explicit orbit mapping — left-drag rotates, right/middle pans.
    controls.enableRotate = true;
    controls.enablePan = true;
    controls.screenSpacePanning = true;
    controls.mouseButtons = {
        LEFT: THREE.MOUSE.ROTATE,
        MIDDLE: THREE.MOUSE.DOLLY,
        RIGHT: THREE.MOUSE.PAN
    };
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
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);

    if (labelRenderer) {
        labelRenderer.setSize(width, height);
    }
}

