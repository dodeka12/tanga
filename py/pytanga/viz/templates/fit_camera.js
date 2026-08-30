// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Shared camera auto-fit used by both the live viewer and the HTML export
// bootstrap.  The live viewer reaches this through `view_mode.js` (which
// re-exports it); the export pipeline concatenates this file directly (imports
// and `export` keywords are stripped), so both paths run the exact same
// function.

import * as THREE from 'three';

const _REFERENCE_KINDS = new Set(['Axes3D', 'Axes2D', 'Axis', 'Grid']);

function _finiteAspect(w, h) {
    const width = Number(w);
    const height = Number(h);
    if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
        return NaN;
    }
    return width / height;
}

/**
 * Auto-fit the camera to the scene contents.
 *
 * @param {Map<string,{obj:THREE.Object3D|null,layer:string,data?:object}>} sceneObjects
 * @param {THREE.Camera} camera
 * @param {THREE.OrbitControls} controls
 * @param {number} spaceDim  2 or 3
 */
export function fitCamera(sceneObjects, camera, controls, spaceDim) {
    // ── 2D orthographic fit (top-down; unchanged behaviour) ──
    if (spaceDim === 2) {
        const box = new THREE.Box3();
        sceneObjects.forEach(entry => {
            if (entry && entry.layer === 'scene' && entry.obj) box.expandByObject(entry.obj);
        });
        if (box.isEmpty()) return;

        const center = new THREE.Vector3();
        box.getCenter(center);
        const size = new THREE.Vector3();
        box.getSize(size);

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

    // ── 3D perspective fit ──
    // Exclude reference-frame objects (axes/grid) so the fit frames the actual
    // content; always include the origin so the view stays anchored on it.
    const content = [];
    const reference = [];
    sceneObjects.forEach(entry => {
        if (!entry || entry.layer !== 'scene' || !entry.obj) return;
        const kind = entry.data && entry.data.kind;
        if (_REFERENCE_KINDS.has(kind)) reference.push(entry.obj);
        else content.push(entry.obj);
    });

    const box = new THREE.Box3();
    if (content.length === 0 && reference.length === 0) {
        // Completely empty scene → default 10-unit cube centred at the origin.
        box.set(new THREE.Vector3(-5, -5, -5), new THREE.Vector3(5, 5, 5));
    } else {
        box.expandByPoint(new THREE.Vector3(0, 0, 0));
        const sources = content.length > 0 ? content : reference;
        for (const obj of sources) box.expandByObject(obj);
    }

    const center = new THREE.Vector3();
    box.getCenter(center);
    const size = new THREE.Vector3();
    box.getSize(size);

    // Fit the box's bounding sphere within the vertical FOV (with a small
    // margin), looking at the world origin so orbit always rotates around it.
    const radius = Math.max(0.5, 0.5 * size.length());
    const fov = ((camera && camera.fov) || 50) * Math.PI / 180;
    const distance = (radius / Math.sin(fov / 2)) * 1.1;
    const dir = new THREE.Vector3(0.6, 0.5, 0.7).normalize();

    controls.target.set(0, 0, 0);
    camera.position.set(
        center.x + dir.x * distance,
        center.y + dir.y * distance,
        center.z + dir.z * distance,
    );
    camera.lookAt(controls.target);
    camera.near = Math.max(0.01, distance * 0.001);
    camera.far = distance * 10;
    camera.updateProjectionMatrix();
    controls.update();
}
