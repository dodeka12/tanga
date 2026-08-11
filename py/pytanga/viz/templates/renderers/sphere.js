// Sphere renderer — rendered as a sphere with optional wireframe overlay.
// Phase 5: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
    createTextureLabel,
} from './utils.js';

export async function createSphere(ent) {
    const color = parseColor(ent, '#ffaa00');
    const opacity = styleParam(ent, 'opacity', 0.4);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);

    const geometry = new THREE.SphereGeometry(radius, 32, 32);
    const doubleSided = styleParam(ent, 'double_sided', false);
    const material = makeMaterial(color, opacity, doubleSided);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(center[0], center[1], center[2]);

    // ── Texture label ──
    const texLabel = ent.style?.texture_label;
    if (texLabel && texLabel.text) {
        // Default background to entity color so the label blends in
        if (!texLabel.background || texLabel.background === 'transparent') {
            texLabel.background = color;
        }
        const texture = await createTextureLabel(texLabel.text, texLabel);
        if (texture) {
            material.map = texture;
            // Set material color to white so the texture's own colors
            // pass through unmodified (MeshPhongMaterial multiplies
            // material.color * texture pixel values).
            material.color.set(0xffffff);
            material.needsUpdate = true;
        }
    }

    // Wireframe overlay
    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.SphereGeometry(radius * 1.005, 24, 24),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}
