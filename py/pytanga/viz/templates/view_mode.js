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
    camera.position.set(8, 6, 10);
    camera.lookAt(0, 0, 0);
    return camera;
}

function _newOrthographic() {
    return new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 1000);
}

function _newPerspective(aspect, fov = 50) {
    return new THREE.PerspectiveCamera(fov, aspect, 0.1, 1000);
}

function _normalize(v) {
    const len = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
    if (len < 1e-9) return [0, 0, 1];
    return [v[0] / len, v[1] / len, v[2] / len];
}

function _cross(a, b) {
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ];
}

/**
 * Compute an in-plane horizontal direction when the user did not provide
 * ``span_u``.  Returns a normalized vector perpendicular to ``n``.
 */
function _autoSpanU(n) {
    const ref = Math.abs(n[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
    return _normalize(_cross(ref, n));
}

/**
 * Apply the camera described by ``cameraConfig`` to the scene.
 *
 * Handles three cases:
 *   - ``view_2d``: orthographic view from a rectangle (extent_x × extent_y).
 *   - ``view_plane``: perspective view defined by a virtual plane.
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

    // ── view_2d ──
    if (cc.view_2d) {
        const v = cc.view_2d;
        const cx = v.center ? v.center[0] : 0;
        const cy = v.center ? v.center[1] : 0;
        const extX = Math.abs(v.extent_x || 10);
        const extY = Math.abs(v.extent_y || 10);

        let cam = camera;
        if (!cam.isOrthographicCamera) {
            cam = _newOrthographic();
            controls.object = cam;
        }
        const fit = Math.max(extX / aspect, extY);
        cam.left = -fit * aspect / 2;
        cam.right = fit * aspect / 2;
        cam.top = fit / 2;
        cam.bottom = -fit / 2;
        cam.near = 0.1;
        cam.far = 1000;
        cam.position.set(cx, cy, 20);
        cam.lookAt(cx, cy, 0);
        cam.updateProjectionMatrix();
        cam.userData._view2d = { extent_x: extX, extent_y: extY, center: [cx, cy] };
        controls.target.set(cx, cy, 0);
        controls.update();
        return cam;
    }

    // ── view_plane ──
    if (cc.view_plane) {
        const v = cc.view_plane;
        const n = _normalize(v.normal || [0, 0, 1]);
        const center = v.center || v.point || [0, 0, 0];
        const extU = Math.abs(v.extent_u || 10);
        const extV = Math.abs(v.extent_v || 10);
        const fov = v.fov || 50;

        let u = v.span_u ? _normalize(v.span_u) : _autoSpanU(n);
        // Orthogonalize u against n (relevant when span_u had a normal
        // component) and build v = n × u.
        const dot = u[0] * n[0] + u[1] * n[1] + u[2] * n[2];
        u = _normalize([
            u[0] - dot * n[0],
            u[1] - dot * n[1],
            u[2] - dot * n[2],
        ]);
        const vv = _cross(n, u);

        const distance = (Math.max(extU, extV) / 2) / Math.tan((fov * Math.PI / 180) / 2);

        let cam = camera;
        if (cam.isOrthographicCamera) {
            cam = _newPerspective(aspect, fov);
            controls.object = cam;
        }
        cam.fov = fov;
        cam.aspect = aspect;
        cam.near = Math.max(0.01, distance * 0.001);
        cam.far = distance * 10;
        cam.position.set(
            center[0] + n[0] * distance,
            center[1] + n[1] * distance,
            center[2] + n[2] * distance
        );
        cam.up.set(vv[0], vv[1], vv[2]);
        cam.lookAt(center[0], center[1], center[2]);
        cam.updateProjectionMatrix();
        controls.target.set(center[0], center[1], center[2]);
        controls.update();
        return cam;
    }

    // ── Default 2D (no explicit view config) ──
    if (spaceDim === 2 && !camera.isOrthographicCamera) {
        const frustumSize = 20;  // sensible default full height
        const newCam = _newOrthographic();
        newCam.left = frustumSize * aspect / -2;
        newCam.right = frustumSize * aspect / 2;
        newCam.top = frustumSize / 2;
        newCam.bottom = frustumSize / -2;
        newCam.position.set(0, 0, 20);
        newCam.lookAt(0, 0, 0);
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
        renderer.sortObjects = false;
    }
    // 3D: no changes needed — defaults are set by setupControls()
}

/**
 * Auto‑fit the camera to encompass all entity meshes.
 *
 * @param {Map<string,THREE.Object3D>} entityMeshes
 * @param {THREE.Camera} camera
 * @param {THREE.OrbitControls} controls
 * @param {number} spaceDim  2 or 3
 */
export function fitCamera(entityMeshes, camera, controls, spaceDim) {
    if (entityMeshes.size === 0) return;

    const box = new THREE.Box3();
    entityMeshes.forEach(m => box.expandByObject(m));
    const center = new THREE.Vector3();
    box.getCenter(center);
    const size = new THREE.Vector3();
    box.getSize(size);

    if (spaceDim === 2) {
        const frustumSize = Math.max(size.x, size.y, 1) * 1.2;
        const aspect = window.innerWidth / window.innerHeight;
        camera.left = frustumSize * aspect / -2;
        camera.right = frustumSize * aspect / 2;
        camera.top = frustumSize / 2;
        camera.bottom = frustumSize / -2;
        camera.position.set(center.x, center.y, 20);
        camera.lookAt(center.x, center.y, 0);
        camera.updateProjectionMatrix();
        controls.target.set(center.x, center.y, 0);
        controls.update();
        return;
    }

    // 3D
    const maxDim = Math.max(size.x, size.y, size.z, 1);
    const distance = maxDim * 1.5 + 2;
    // Keep the orbit target at the world origin so rotation always
    // orbits around (0,0,0) regardless of entity placement.
    console.log('[tanga-debug] fitCamera 3D — center:', center.toArray(),
        'size:', size.toArray(),
        'maxDim:', maxDim,
        'distance:', distance,
        'setting controls.target to [0,0,0]');
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
 * Handle window resize.  For 2D orthographic cameras, adjusts the frustum
 * to preserve the visible area.
 *
 * @param {THREE.Camera} camera
 * @param {THREE.WebGLRenderer} renderer
 * @param {object|null} labelRenderer  window._labelRenderer
 * @param {HTMLElement|null} viewerContainer  window._viewerContainer
 * @param {number} spaceDim  2 or 3
 */
export function handleResize(camera, renderer, labelRenderer, viewerContainer, spaceDim) {
    if (spaceDim === 2 && camera.isOrthographicCamera) {
        const aspect = window.innerWidth / window.innerHeight;
        // Prefer the custom view_2d extents stored by switchToCamera;
        // otherwise preserve the current visible full height.
        const v2d = camera.userData?._view2d;
        const extX = v2d ? v2d.extent_x : Math.abs(camera.right - camera.left);
        const extY = v2d ? v2d.extent_y : Math.abs(camera.top - camera.bottom);
        const fit = Math.max(extX / aspect, extY);
        camera.left = -fit * aspect / 2;
        camera.right = fit * aspect / 2;
        camera.top = fit / 2;
        camera.bottom = -fit / 2;
    }

    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);

    if (labelRenderer) {
        labelRenderer.setSize(window.innerWidth, window.innerHeight);
    }
    if (viewerContainer) {
        viewerContainer.style.width = '100%';
        viewerContainer.style.height = '100%';
    }
}

/**
 * Apply 2D overlay draw order to a mesh: z‑coordinate determines stack order.
 * In 3D mode this is a no‑op (depth testing handles all layering naturally).
 *
 * @param {THREE.Object3D} mesh
 * @param {number} z       z‑coordinate (position[2])
 * @param {number} spaceDim  2 or 3
 */
export function applyOverlayDrawOrder(mesh, z, spaceDim) {
    if (spaceDim !== 2) return;

    mesh.renderOrder = Math.round(z * 100);
    mesh.traverse(child => {
        if (child.material) {
            child.material.depthTest = false;
            child.material.depthWrite = false;
            child.material.needsUpdate = true;
        }
    });
}