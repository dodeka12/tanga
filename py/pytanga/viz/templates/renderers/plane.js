// Plane renderer — rendered as a double-sided translucent quad
// with optional wireframe overlay.
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

/**
 * Build the quad geometry for a plane entity.
 *
 * When ``ent.span_u`` / ``ent.span_v`` are present, returns a parallelogram
 * quad (two triangles) whose corners are ``±span_u/2 ± span_v/2`` around the
 * origin (the span vectors are world-space edge vectors; the node transform
 * positions the quad).  Otherwise returns ``null`` and the caller falls back to
 * the default square of half-side ``extent`` centred at the origin (the
 * canonical XY plane).
 */
function _planeGeometry(ent) {
    const spanU = ent.span_u;
    const spanV = ent.span_v;
    if (!Array.isArray(spanU) || !Array.isArray(spanV)) {
        return null;
    }
    const u = new THREE.Vector3(...spanU);
    const v = new THREE.Vector3(...spanV);
    const a = u.clone().multiplyScalar(-0.5).addScaledVector(v, -0.5);
    const b = a.clone().add(u);
    const c = a.clone().add(u).add(v);
    const d = a.clone().add(v);
    const positions = new Float32Array([
        a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z,
        a.x, a.y, a.z, c.x, c.y, c.z, d.x, d.y, d.z,
    ]);
    const uvs = new Float32Array([0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1]);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
    geometry.computeVertexNormals();
    return geometry;
}

export async function createPlane(ent) {
    const color = parseColor(ent, '#4488ff');
    const opacity = styleParam(ent, 'opacity', 0.3);
    const extent = ent.extent ?? styleParam(ent, 'extent', 10.0);

    const spanGeometry = _planeGeometry(ent);
    const geometry = spanGeometry || new THREE.PlaneGeometry(extent * 2, extent * 2);
    const material = makeMaterial(color, opacity, true);
    const mesh = new THREE.Mesh(geometry, material);

    // ── Texture label ──
    const texLabel = ent.style?.texture_label;
    if (texLabel && texLabel.text) {
        // Plane defaults: no offset
        if (texLabel.offset_v === undefined) texLabel.offset_v = 0.0;
        // Default background to entity color so the label blends in
        if (!texLabel.background || texLabel.background === 'transparent') {
            texLabel.background = color;
        }

        const texture = await createTextureLabel(texLabel.text, texLabel);
        if (texture) {
            // Apply align mode
            const align = texLabel.align || 'stretch';
            switch (align) {
                case 'fit':
                    texture.wrapS = THREE.ClampToEdgeWrapping;
                    texture.wrapT = THREE.ClampToEdgeWrapping;
                    texture.repeat.set(1, 1);
                    break;
                case 'repeat':
                    texture.wrapS = THREE.RepeatWrapping;
                    texture.wrapT = THREE.RepeatWrapping;
                    texture.repeat.set(
                        texLabel.repeat_u || 1,
                        texLabel.repeat_v || 1
                    );
                    break;
                case 'stretch':
                default:
                    texture.wrapS = THREE.ClampToEdgeWrapping;
                    texture.wrapT = THREE.ClampToEdgeWrapping;
                    texture.repeat.set(1, 1);
                    break;
            }
            material.map = texture;
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
            spanGeometry || new THREE.PlaneGeometry(extent * 2, extent * 2),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}
