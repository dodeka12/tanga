// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Frustum renderer — four corner lines from the near end (or apex) to the far
// end, end-plane outlines, and optional translucent faces.

import * as THREE from 'three';

import {
    makeFatSegmentsFromFlat,
    makeMaterial,
    parseColor,
    styleParam,
    tagEntity,
} from './utils.js';

function _quadGeometry(a, b, c, d) {
    const positions = new Float32Array([
        a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2],
        a[0], a[1], a[2], c[0], c[1], c[2], d[0], d[1], d[2],
    ]);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.computeVertexNormals();
    return geo;
}

function _fillFace(group, a, b, c, d, color, opacity) {
    const mesh = new THREE.Mesh(_quadGeometry(a, b, c, d), makeMaterial(color, opacity, true));
    mesh.userData.isFillQuad = true;
    group.add(mesh);
}

function _corners(y, hw, hh) {
    return [
        [-hw, y, -hh],
        [hw, y, -hh],
        [hw, y, hh],
        [-hw, y, hh],
    ];
}

export function createFrustum(ent) {
    const color = parseColor(ent, '#88ccff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const thickness = styleParam(ent, 'thickness', 1.0);
    const near = ent.near ?? 0.0;
    const far = Math.max(ent.far ?? 1.0, 0.001);
    const halfWidth = Math.max(ent.halfWidth ?? 1.0, 0.001);
    const halfHeight = Math.max(ent.halfHeight ?? 1.0, 0.001);
    const apex = near <= 0.0;

    // Canonical: apex at the origin (or the near plane at +Y `near`), the far
    // plane at +Y `far`, half-extents along +X / +Z.  The near half-extents
    // follow by similar triangles.  Placement rides on the node transform.
    const farCorners = _corners(far, halfWidth, halfHeight);
    const nearHalfWidth = halfWidth * (near / far);
    const nearHalfHeight = halfHeight * (near / far);
    const nearCorners = apex
        ? [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        : _corners(near, nearHalfWidth, nearHalfHeight);

    const group = new THREE.Group();

    // Corner lines: near[i] -> far[i] (from the apex when collapsed).
    const cornerLines = [];
    for (let i = 0; i < 4; i++) {
        cornerLines.push(...nearCorners[i], ...farCorners[i]);
    }
    group.add(makeFatSegmentsFromFlat(cornerLines, color, opacity, thickness));

    // End-plane outlines.
    const nearLoop = [];
    const farLoop = [];
    for (let i = 0; i < 4; i++) {
        const j = (i + 1) % 4;
        if (!apex) nearLoop.push(...nearCorners[i], ...nearCorners[j]);
        farLoop.push(...farCorners[i], ...farCorners[j]);
    }
    if (!apex) group.add(makeFatSegmentsFromFlat(nearLoop, color, opacity, thickness));
    group.add(makeFatSegmentsFromFlat(farLoop, color, opacity, thickness));

    // Optional translucent faces.
    if (styleParam(ent, 'fill', false)) {
        const fillOpacity = styleParam(ent, 'fill_opacity', 0.2);
        _fillFace(group, farCorners[0], farCorners[1], farCorners[2], farCorners[3], color, fillOpacity);
        if (!apex) {
            _fillFace(group, nearCorners[0], nearCorners[1], nearCorners[2], nearCorners[3], color, fillOpacity);
            for (let i = 0; i < 4; i++) {
                const j = (i + 1) % 4;
                _fillFace(group, nearCorners[i], nearCorners[j], farCorners[j], farCorners[i], color, fillOpacity);
            }
        } else {
            for (let i = 0; i < 4; i++) {
                const j = (i + 1) % 4;
                _fillFace(group, nearCorners[0], farCorners[i], farCorners[j], nearCorners[0], color, fillOpacity);
            }
        }
    }

    tagEntity(group, ent);
    return group;
}
