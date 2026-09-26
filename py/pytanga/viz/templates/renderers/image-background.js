// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Image background renderer — a full-viewport NDC quad drawn *behind* the 3D
// scene.  The vertex shader writes clip-space coordinates directly (so the quad
// ignores the scene camera and always fills the pane), and the fragment shader
// samples the image texture.  Used by `ThreeJsView` for a
// `SceneView.background_image`.

import * as THREE from 'three';

import { makeEncodedTexture, makeStreamTexture, makeTiledTexture } from './image.js';
import { hasImageFrame, takeImageFrame } from '../image-frames.js';

const _BG_VERTEX = /* glsl */ `
varying vec2 vNdc;
void main() {
    vNdc = position.xy;
    gl_Position = vec4(position.xy, 0.999999, 1.0);
}`;

const _BG_FRAGMENT = /* glsl */ `
precision highp float;
varying vec2 vNdc;
uniform sampler2D uImage;
uniform float uImageAspect;   // image width / height
uniform float uPaneAspect;    // pane width / height
uniform float uFit;           // 0.0 = letterbox (fit), 1.0 = stretch (fill)
uniform vec4 uCrop;           // (u0, v0, u1, v1) normalized image coords

void main() {
    float hx = uFit > 0.5 ? 1.0 : min(1.0, uImageAspect / uPaneAspect);
    float hy = uFit > 0.5 ? 1.0 : min(1.0, uPaneAspect / uImageAspect);
    vec2 q = vNdc / vec2(hx, hy);
    if (abs(q.x) > 1.0 || abs(q.y) > 1.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        vec2 p = q * 0.5 + 0.5;
        vec2 uv;
        uv.x = uCrop.x + p.x * (uCrop.z - uCrop.x);
        uv.y = 1.0 - uCrop.w + p.y * (uCrop.w - uCrop.y);
        gl_FragColor = texture2D(uImage, uv);
    }
}`;

/** Build the shared full-viewport background shader material. */
function _buildMaterial(imageMeta) {
    const img = imageMeta || {};
    const width = Number(img.width) || 1;
    const height = Number(img.height) || 1;
    return new THREE.ShaderMaterial({
        vertexShader: _BG_VERTEX,
        fragmentShader: _BG_FRAGMENT,
        uniforms: {
            uImage: { value: null },
            uImageAspect: { value: width / height },
            uPaneAspect: { value: 1.0 },
            uFit: { value: 0.0 },
            uCrop: { value: new THREE.Vector4(0, 0, 1, 1) },
        },
        depthTest: false,
        depthWrite: false,
    });
}

/**
 * Resolve the texture for a background image, dispatching on its `source`.
 * Returns a `Promise<THREE.Texture|null>`; `null` means the image could not be
 * loaded and the previous texture (if any) should remain visible.
 */
function _backgroundTexture(img) {
    if (img.source === 'url' && img.url) {
        if (img.url.includes('/stream/')) {
            return Promise.resolve(makeStreamTexture(img));
        }
        return new Promise((resolve) => {
            new THREE.TextureLoader().load(
                img.url,
                (tex) => {
                    tex.minFilter = THREE.NearestFilter;
                    tex.magFilter = THREE.NearestFilter;
                    resolve(tex);
                },
                undefined,
                () => resolve(null),
            );
        });
    }
    if (img.source === 'tiled') {
        return makeTiledTexture(img);
    }
    const frame = hasImageFrame(img.id) ? takeImageFrame(img.id) : null;
    // `makeEncodedTexture` applies the correct per-codec orientation itself
    // (JPEG canvas texture and data texture both render row 0 at the top), so
    // no extra flip is needed here.
    return makeEncodedTexture(img, frame);
}

/**
 * Build a screen-space image background quad.
 *
 * @param {object} imageMeta  the serialized `background_image` metadata dict
 * @returns {THREE.Mesh}
 */
export function createImageBackground(imageMeta) {
    const img = imageMeta || {};
    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = _buildMaterial(img);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.frustumCulled = false;
    mesh.renderOrder = -1;

    _backgroundTexture(img).then((tex) => {
        if (tex) material.uniforms.uImage.value = tex;
    });

    return mesh;
}

/**
 * Swap the texture of an existing background quad to a new image, keeping the
 * previous texture visible until the new one decodes (no black flash), and
 * leaving the crop (`uCrop`) untouched so a same-size swap preserves zoom/pan.
 *
 * @param {THREE.Mesh} mesh
 * @param {object} imageMeta  the serialized `background_image` metadata dict
 */
export function updateImageBackground(mesh, imageMeta) {
    const mat = mesh && mesh.material;
    if (!mat || !mat.uniforms) return;
    const img = imageMeta || {};
    const width = Number(img.width) || 1;
    const height = Number(img.height) || 1;
    mat.uniforms.uImageAspect.value = width / height;
    _backgroundTexture(img).then((tex) => {
        if (tex) mat.uniforms.uImage.value = tex;
    });
}

/**
 * Update a background quad's pane aspect (call on resize).
 *
 * @param {THREE.Mesh} mesh
 * @param {number} paneAspect  pane width / height
 */
export function setBackgroundAspect(mesh, paneAspect) {
    const mat = mesh && mesh.material;
    if (mat && mat.uniforms && mat.uniforms.uPaneAspect) {
        mat.uniforms.uPaneAspect.value = Number(paneAspect) || 1.0;
    }
}

/**
 * Update a background quad's crop window `{u0, v0, u1, v1}` (normalized image
 * coordinates, v=0 at the top).  Pass `null`/`undefined` to reset to the full
 * image.
 */
export function setBackgroundCrop(mesh, crop) {
    const mat = mesh && mesh.material;
    if (mat && mat.uniforms && mat.uniforms.uCrop) {
        const c = crop || { u0: 0, v0: 0, u1: 1, v1: 1 };
        mat.uniforms.uCrop.value.set(
            c.u0 !== undefined ? c.u0 : 0,
            c.v0 !== undefined ? c.v0 : 0,
            c.u1 !== undefined ? c.u1 : 1,
            c.v1 !== undefined ? c.v1 : 1,
        );
    }
}
