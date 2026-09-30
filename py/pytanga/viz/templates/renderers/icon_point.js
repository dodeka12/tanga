// IconPointStyle renderer — a flat quad textured with an icon glyph (Material
// Symbols ligature or a unicode symbol) instead of a sphere.

import * as THREE from 'three';
import { makeMaterial, styleParam, parseColor, tagEntity } from './utils.js';

function _iconParts(icon) {
    const i = icon.indexOf(':');
    if (i === -1) return { family: 'material', name: icon };
    return { family: icon.slice(0, i) || 'material', name: icon.slice(i + 1) };
}

function _makeIconTexture(icon) {
    // Draw the glyph in white; the mesh material color tints it, so a color
    // change is applied in place (without re-rendering the canvas).
    const { family, name } = _iconParts(icon);
    const font = family === 'uc'
        ? '48px sans-serif'
        : '48px "Material Symbols Outlined"';
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 64;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.clearRect(0, 0, 64, 64);
    ctx.fillStyle = '#ffffff';
    ctx.font = font;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(name, 32, 32);
    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    return texture;
}

export function createIconPoint(ent) {
    const color = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const size = styleParam(ent, 'size', 0.1); // half-extent (world units)
    const screenSpace = styleParam(ent, 'screen_space', false);
    const icon = styleParam(ent, 'icon', '');
    const pos = ent.position || [0, 0, 0];

    const material = makeMaterial(color, opacity, true);
    if (icon) {
        const texture = _makeIconTexture(icon);
        if (texture) {
            material.map = texture;
            material.transparent = true;
            material.depthWrite = false;
        }
    }
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(size * 2, size * 2), material);
    // Lift the flat quad slightly above the xy-plane so it renders and
    // raycasts above coplanar bodies at z = 0 (e.g. a rectangle fill)
    // instead of being occluded by them.  `size` is in world units for
    // world-space markers, but in screen PIXELS for screen-space markers
    // (rescaled later by `_updateScreenSpaceMarkers`), so the lift must use a
    // tiny world-unit offset in that case rather than `size * 0.1`.
    const lift = screenSpace ? 1e-3 : size * 0.1;
    mesh.position.set(pos[0], pos[1], pos[2] + lift);
    tagEntity(mesh, ent);
    if (screenSpace) {
        mesh.userData.isScreenSpace = true;
    }
    return mesh;
}
