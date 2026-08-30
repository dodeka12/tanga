// Tanga Viewer — Dimension‑specific camera, controls, and rendering helpers.
// All space_dim‑dependent logic lives here; viewer.js calls these functions
// unconditionally.  No conditionals elsewhere in the codebase.

import * as THREE from 'three';

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
 * Compute the orthographic left/right/top/bottom for a 2D camera.
 *
 * @param {number} xmin
 * @param {number} xmax
 * @param {number} ymin
 * @param {number} ymax
 * @param {boolean} uniform  letterbox (true) vs stretch-to-fill (false)
 * @param {number} borderPx  pixel margin (all modes)
 * @param {number} aspect     window.innerWidth / window.innerHeight
 * @returns {{left:number, right:number, top:number, bottom:number}}
 */
function _orthoFrustum(xmin, xmax, ymin, ymax, uniform, borderPx, aspect) {
    const extX = Math.abs(xmax - xmin) || 10;
    const extY = Math.abs(ymax - ymin) || 10;

    if (!uniform) {
        // Stretch-to-fill: the rectangle's width/height each fill the content
        // area (viewport inset by border_px), scaling X and Y independently
        // (non-uniform).  The camera is centered on the rectangle, so use
        // symmetric half-extents expanded back to the full window.
        const w = window.innerWidth;
        const h = window.innerHeight;
        const bp = borderPx || 0;
        const cw = w - 2 * bp;
        const ch = h - 2 * bp;
        const fX = cw > 0 ? w / cw : 1;
        const fY = ch > 0 ? h / ch : 1;
        return {
            left: -(extX / 2) * fX,
            right: (extX / 2) * fX,
            top: (extY / 2) * fY,
            bottom: -(extY / 2) * fY,
        };
    }

    // Undistorted letterboxing: a single world-units-per-pixel scale so the
    // full requested rectangle is contained.  An optional pixel border shrinks
    // the effective content area before the fit.
    const w = window.innerWidth;
    const h = window.innerHeight;
    const bp = borderPx || 0;
    const cw = w - 2 * bp;
    const ch = h - 2 * bp;
    const aspectContent = (cw > 0 && ch > 0) ? (cw / ch) : aspect;

    const fit = Math.max(extX / aspectContent, extY);
    // Expand the fitted content frustum back to the full viewport so the
    // border appears as extra margin (still uniform scale).
    const fitFull = (bp > 0 && cw > 0 && ch > 0) ? (fit * h / ch) : fit;

    return {
        left: -fitFull * aspect / 2,
        right: fitFull * aspect / 2,
        top: fitFull / 2,
        bottom: -fitFull / 2,
    };
}

/**
 * Return a finite aspect ratio (width / height), or NaN when the size is not
 * usable (zero, negative, or non-finite).  Callers must never write NaN into a
 * camera frustum, so they guard on this result.
 *
 * @param {number} width
 * @param {number} height
 * @returns {number}
 */
function _finiteAspect(width, height) {
    if (!Number.isFinite(width) || !Number.isFinite(height)) return NaN;
    if (width <= 0 || height <= 0) return NaN;
    return width / height;
}

/**
 * Set the 2D orthographic frustum (left/right/top/bottom) for the given aspect
 * ratio.  Recomputed from the stored fit (``camera.userData._view2d``) when
 * available; otherwise the current full height is preserved.  Never writes
 * NaN/Infinity — a corrupt frustum is reset to a sane default box.
 *
 * @param {THREE.OrthographicCamera} camera
 * @param {number} aspect  finite width/height ratio
 */
function _applyOrthoFrustum(camera, aspect) {
    const v2d = camera.userData?._view2d;
    const finiteRect = v2d
        && Number.isFinite(v2d.xmin) && Number.isFinite(v2d.xmax)
        && Number.isFinite(v2d.ymin) && Number.isFinite(v2d.ymax);

    if (finiteRect) {
        const f = _orthoFrustum(
            v2d.xmin, v2d.xmax, v2d.ymin, v2d.ymax,
            v2d.uniform !== false, v2d.border_px || 0, aspect
        );
        camera.left = f.left;
        camera.right = f.right;
        camera.top = f.top;
        camera.bottom = f.bottom;
        return;
    }

    // Fall back to preserving the current full height, but never propagate a
    // non-finite/corrupt frustum (Math.max(NaN, …) === NaN).
    const extX = Math.abs(camera.right - camera.left);
    const extY = Math.abs(camera.top - camera.bottom);
    if (!Number.isFinite(extX) || !Number.isFinite(extY) || extX <= 0 || extY <= 0) {
        const height = 10;  // sane default full height
        camera.left = -height * aspect / 2;
        camera.right = height * aspect / 2;
        camera.top = height / 2;
        camera.bottom = -height / 2;
        return;
    }

    const fit = Math.max(extX / aspect, extY);
    camera.left = -fit * aspect / 2;
    camera.right = fit * aspect / 2;
    camera.top = fit / 2;
    camera.bottom = -fit / 2;
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
 * @returns {THREE.Camera} the (possibly replaced) camera
 */
export function switchToCamera(camera, controls, spaceDim, cameraConfig) {
    const cc = cameraConfig || {};
    const aspect = window.innerWidth / window.innerHeight;

    // ── 2D orthographic ──
    if (cc.type === '2d') {
        const xmin = cc.xmin ?? 0;
        const xmax = cc.xmax ?? 0;
        const ymin = cc.ymin ?? 0;
        const ymax = cc.ymax ?? 0;
        const cx = (xmin + xmax) / 2;
        const cy = (ymin + ymax) / 2;
        const uniform = cc.uniform !== false;  // default true
        const borderPx = cc.border_px || 0;

        let cam = camera;
        if (!cam.isOrthographicCamera) {
            cam = _newOrthographic();
            controls.object = cam;
        }

        const f = _orthoFrustum(xmin, xmax, ymin, ymax, uniform, borderPx, aspect);
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
        cam.userData._view2d = { xmin, xmax, ymin, ymax, uniform, border_px: borderPx };
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
            uniform: true,
            border_px: 0,
        };
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

/**
 * Auto‑fit the camera to encompass all entity meshes.
 *
 * @param {Map<string,{obj:THREE.Object3D|null,layer:string}>} sceneObjects
 * @param {THREE.Camera} camera
 * @param {THREE.OrbitControls} controls
 * @param {number} spaceDim  2 or 3
 */
export function fitCamera(sceneObjects, camera, controls, spaceDim) {
    const box = new THREE.Box3();
    sceneObjects.forEach(entry => {
        if (entry.layer === 'scene' && entry.obj) box.expandByObject(entry.obj);
    });
    if (box.isEmpty()) return;

    const center = new THREE.Vector3();
    box.getCenter(center);
    const size = new THREE.Vector3();
    box.getSize(size);

    if (spaceDim === 2) {
        const frustumSize = Math.max(size.x, size.y, 1) * 1.2;
        const aspect = _finiteAspect(window.innerWidth, window.innerHeight);
        const safeAspect = Number.isFinite(aspect) ? aspect : 1.0;
        camera.left = frustumSize * safeAspect / -2;
        camera.right = frustumSize * safeAspect / 2;
        camera.top = frustumSize / 2;
        camera.bottom = frustumSize / -2;
        camera.position.set(center.x, center.y, 20);
        camera.lookAt(center.x, center.y, 0);
        camera.updateProjectionMatrix();
        controls.target.set(center.x, center.y, 0);
        controls.update();
        // Persist the fitted rectangle so resize recomputes from the original
        // fit (letterbox) rather than the current, possibly-corrupt frustum.
        camera.userData._view2d = {
            xmin: center.x - frustumSize * safeAspect / 2,
            xmax: center.x + frustumSize * safeAspect / 2,
            ymin: center.y - frustumSize / 2,
            ymax: center.y + frustumSize / 2,
            uniform: true,
            border_px: 0,
        };
        return;
    }

    // 3D
    const maxDim = Math.max(size.x, size.y, size.z, 1);
    const distance = maxDim * 1.5 + 2;
    // Keep the orbit target at the world origin so rotation always
    // orbits around (0,0,0) regardless of entity placement.
    controls.target.set(0, 0, 0);
    camera.position.set(
        center.x + distance * 0.6,
        center.y + distance * 0.5,
        center.z + distance * 0.7
    );
    camera.lookAt(controls.target);
    camera.near = Math.max(0.01, distance * 0.001);
    camera.far = distance * 10;
    camera.updateProjectionMatrix();
    controls.update();
}

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
    const aspect = _finiteAspect(width, height);
    if (!Number.isFinite(aspect)) return;

    if (spaceDim === 2 && camera.isOrthographicCamera) {
        _applyOrthoFrustum(camera, aspect);
    }

    camera.aspect = aspect;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);

    if (labelRenderer) {
        labelRenderer.setSize(width, height);
    }
}

