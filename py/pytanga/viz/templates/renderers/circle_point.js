// CirclePointStyle renderer — a flat circle marker (filled disc or outline
// ring) instead of a sphere.

import * as THREE from 'three';
import { makeMaterial, styleParam, parseColor, tagEntity, tagScreenSpaceMarker } from './utils.js';

const CIRCLE_POINT_SEGMENTS = 64;

export function createCirclePoint(ent) {
    const color = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const size = styleParam(ent, 'size', 0.08); // circle radius (world units)
    const screenSpace = styleParam(ent, 'screen_space', false);
    const thickness = styleParam(ent, 'thickness', Math.max(size * 0.2, 0.001));
    const filled = styleParam(ent, 'filled', true);
    const pos = ent.position || [0, 0, 0];

    let mesh;
    if (filled) {
        // Filled disc; its opacity is `fill_opacity` (defaulting to `opacity`).
        const fillOpacity = styleParam(ent, 'fill_opacity', opacity);
        mesh = new THREE.Mesh(
            new THREE.CircleGeometry(size, CIRCLE_POINT_SEGMENTS),
            makeMaterial(color, fillOpacity, true)
        );
        mesh.userData.isFillQuad = true;
    } else {
        // Outline ring: a flat annulus whose radial width is `thickness`.
        const inner = Math.max(size - thickness, 0.0005);
        mesh = new THREE.Mesh(
            new THREE.RingGeometry(inner, size, CIRCLE_POINT_SEGMENTS),
            makeMaterial(color, opacity, true)
        );
    }

    // Lift the flat marker slightly above the xy-plane so it renders and
    // raycasts above coplanar bodies at z = 0 (e.g. an image or a rectangle
    // fill) instead of z-fighting with them.  `size` is in world units for
    // world-space markers, but in screen PIXELS for screen-space markers
    // (rescaled later by `_updateScreenSpaceMarkers`).  Screen-space markers
    // must keep the entity's exact z so a perspective camera introduces no
    // zoom-dependent parallax; they are layered above coplanar bodies via
    // `polygonOffset` + `renderOrder` instead of a world-space lift.
    const lift = screenSpace ? 0 : size * 0.1;
    mesh.position.set(pos[0], pos[1], pos[2] + lift);
    tagEntity(mesh, ent);
    tagScreenSpaceMarker(mesh, screenSpace, { layered: true });
    return mesh;
}
