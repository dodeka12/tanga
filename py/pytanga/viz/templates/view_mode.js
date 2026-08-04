// Tanga Viewer — Dimension‑specific camera, controls, and rendering helpers.
// All space_dim‑dependent logic lives here; viewer.js calls these functions
// unconditionally.  No conditionals elsewhere in the codebase.

import * as THREE from 'three';

/**
 * Create a camera appropriate for the given space dimension.
 *
 * @param {number} spaceDim  2 or 3
 * @param {number} aspect    window.innerWidth / window.innerHeight
 * @param {number} extent    space_extent from scene config (default 10)
 * @returns {THREE.Camera}
 */
export function createCamera(spaceDim, aspect, extent = 10) {
    // Always start with 3D perspective — switchToCamera() is called
    // from applySceneConfig() once sceneConfig arrives.
    const camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 1000);
    camera.position.set(8, 6, 10);
    camera.lookAt(0, 0, 0);
    return camera;
}

/**
 * Switch the camera and/or grid from the current mode to 2D orthographic.
 * Called from applySceneConfig() when space_dim is 2.
 *
 * @param {THREE.Camera} camera    — will be replaced with OrthographicCamera
 * @param {THREE.OrbitControls} controls
 * @param {number} extent          space_extent from scene config
 * @returns {THREE.Camera}         the new (or same) camera
 */
export function switchToCamera(camera, controls, spaceDim, extent) {
    if (spaceDim !== 2 || camera.isOrthographicCamera) {
        return camera;
    }

    const frustumSize = extent * 2;
    const aspect = window.innerWidth / window.innerHeight;
    const newCam = new THREE.OrthographicCamera(
        frustumSize * aspect / -2,
        frustumSize * aspect / 2,
        frustumSize / 2,
        frustumSize / -2,
        0.1,
        1000
    );
    newCam.position.set(0, 0, 20);
    newCam.lookAt(0, 0, 0);
    controls.object = newCam;
    return newCam;
}

/**
 * Create a grid helper appropriate for the given space dimension.
 * 2D: XY-plane grid (rotated GridHelper), 3D: XZ-plane grid.
 *
 * @param {THREE.Scene} scene
 * @param {number} extent  space_extent from scene config
 * @param {number} spaceDim  2 or 3
 * @returns {THREE.GridHelper|THREE.Group}
 */
export function createGrid(scene, extent, spaceDim) {
    const size = extent * 2;
    const divisions = Math.max(size, 20);

    if (spaceDim === 2) {
        // GridHelper makes XZ-plane grid (normal=Y). Rotate it so
        // the grid lies in the XY plane (normal=Z) for top‑down view.
        const grid = new THREE.GridHelper(size, divisions, 0x444466, 0x222244);
        grid.rotation.x = Math.PI / 2;  // XZ → XY
        return grid;
    }

    // 3D: XZ plane (default)
    return new THREE.GridHelper(size, divisions, 0x444466, 0x222244);
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
            LEFT: null,
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
    controls.target.copy(center);
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
        const frustumSize = (Math.abs(camera.right - camera.left) + Math.abs(camera.top - camera.bottom)) / 2;
        const aspect = window.innerWidth / window.innerHeight;
        camera.left = frustumSize * aspect / -2;
        camera.right = frustumSize * aspect / 2;
        camera.top = frustumSize / 2;
        camera.bottom = frustumSize / -2;
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