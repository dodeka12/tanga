// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Image background renderer — a full-viewport NDC quad drawn *behind* the 3D
// scene.  The vertex shader writes clip-space coordinates directly (so the quad
// ignores the scene camera and always fills the pane), and the fragment shader
// samples the image texture.  Used by `ThreeJsView` for a
// `SceneView.background_image`.

import * as THREE from 'three';

import { addCustomUniforms, applyImageUniforms, buildColorUniforms, buildLayerUniforms, buildTiledTextureAtLevel, makeEncodedTexture, makeStreamTexture, updateImageLod } from './image.js';
import { levelForScreen } from './image-tiles.js';
import { buildImageLayerPipeline } from './image-shader.js';
import { hasImageFrame, registerImageFrameConsumer, takeImageFrame } from '../image-frames.js';
import { sendImageEvent } from '../events.js';

const _BG_VERTEX = /* glsl */ `
varying vec2 vNdc;
void main() {
    vNdc = position.xy;
    gl_Position = vec4(position.xy, 0.999999, 1.0);
}`;

function _buildBackgroundFragment(layerCount) {
    return /* glsl */ `
precision highp float;
varying vec2 vNdc;
uniform float uImageAspect;   // image width / height
uniform float uPaneAspect;    // pane width / height
uniform float uFit;           // 0.0 = letterbox (fit), 1.0 = stretch (fill)
uniform vec4 uCrop;           // (u0, v0, u1, v1) normalized image coords
uniform float uHx;            // explicit zoom-scaled letterbox half-extent (NDC)
uniform float uHy;            // explicit zoom-scaled letterbox half-extent (NDC)
${buildImageLayerPipeline(layerCount)}

void main() {
    float hx = uHx > 0.0 ? uHx : (uFit > 0.5 ? 1.0 : min(1.0, uImageAspect / uPaneAspect));
    float hy = uHy > 0.0 ? uHy : (uFit > 0.5 ? 1.0 : min(1.0, uPaneAspect / uImageAspect));
    vec2 q = vNdc / vec2(hx, hy);
    if (abs(q.x) > 1.0 || abs(q.y) > 1.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        vec2 p = q * 0.5 + 0.5;
        vec2 uv;
        uv.x = uCrop.x + p.x * (uCrop.z - uCrop.x);
        uv.y = 1.0 - uCrop.w + p.y * (uCrop.w - uCrop.y);
        vec3 color;
        float alpha;
        tangaComposite(uv, color, alpha);
        gl_FragColor = vec4(color, 1.0);
    }
}`;
}

/** Build the shared full-viewport background shader material. */
function _buildMaterial(imageMeta) {
    const img = imageMeta || {};
    const width = Number(img.width) || 1;
    const height = Number(img.height) || 1;
    const layerCount = Number(img.max_layers) || 8;
    const uniforms = {
        uImageAspect: { value: width / height },
        uPaneAspect: { value: 1.0 },
        uFit: { value: 0.0 },
        uCrop: { value: new THREE.Vector4(0, 0, 1, 1) },
        uHx: { value: 0.0 },
        uHy: { value: 0.0 },
        ...buildColorUniforms(img.uniforms),
        ...buildLayerUniforms(img.uniforms, layerCount),
    };
    for (let i = 0; i < layerCount; i++) {
        uniforms[`uImage${i}`] = { value: null };
    }
    addCustomUniforms(uniforms, img.uniforms);
    return new THREE.ShaderMaterial({
        vertexShader: img.shader?.vertex || _BG_VERTEX,
        fragmentShader: img.shader?.fragment || _buildBackgroundFragment(layerCount),
        uniforms,
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
                    sendImageEvent('image_loaded', {
                        image_id: img.id, source: 'url', width: img.width, height: img.height,
                    });
                    resolve(tex);
                },
                undefined,
                () => resolve(null),
            );
        });
    }
    const frame = hasImageFrame(img.id) ? takeImageFrame(img.id) : null;
    if (!frame) return Promise.resolve(null);   // no pixel frame yet — caller decides
    // `makeEncodedTexture` applies the correct per-codec orientation itself
    // (JPEG canvas texture and data texture both render row 0 at the top), so
    // no extra flip is needed here.
    return makeEncodedTexture(img, frame);
}

// The layer list to render.  `_image_view_meta` always emits `images[]`; fall
// back to the flat primary metadata for an older single-image background.
function _layersOf(imageMeta) {
    const img = imageMeta || {};
    if (Array.isArray(img.images) && img.images.length) return img.images;
    return img.source ? [img] : [];
}

// Bind layer `i`'s texture to `uImage{i}`.  When the pixel frame has not arrived
// yet (it races the metadata over the wire), register a consumer so the texture
// is uploaded once the frame lands (mirrors renderers/image.js).
function _bindLayerTexture(material, img, i, prev) {
    const key = `uImage${i}`;
    if (!img) {
        // A cleared (stable-index) layer slot: disable its sampler.
        material.uniforms[key].value = null;
        return;
    }
    if (img.source === 'tiled') {
        // Preserve the resolved level across a re-bind of the same-sized image
        // so the pyramid does not reset to the 2048 fallback and bounce back to
        // the correct level a frame later.
        const sameSize = prev && prev.img && prev.img.width === img.width && prev.img.height === img.height;
        const level = prev && prev.level != null && sameSize ? prev.level : levelForScreen(img, 2048);
        sendImageEvent('image_tile_load', {
            image_id: img.id, source: 'tiled', width: img.width, height: img.height,
            level, tile_version: img.tile_version,
        });
        buildTiledTextureAtLevel(img, level).then((tex) => {
            material.uniforms[key].value = tex;
            sendImageEvent('image_tile_loaded', {
                image_id: img.id, source: 'tiled', width: img.width, height: img.height,
                level, tile_version: img.tile_version,
            });
            sendImageEvent('image_loaded', {
                image_id: img.id, source: 'tiled', width: img.width, height: img.height,
            });
        });
        material.userData._tiledLayers.push({
            img, index: i, level,
            stableMaxDim: prev ? prev.stableMaxDim : undefined,
            stableSince: prev ? prev.stableSince : undefined,
        });
        return;
    }
    _backgroundTexture(img).then((tex) => {
        if (tex) {
            material.uniforms[key].value = tex;
            if (img.source !== 'url') {
                sendImageEvent('image_loaded', {
                    image_id: img.id, source: 'data', width: img.width, height: img.height,
                });
            }
        } else {
            registerImageFrameConsumer(img.id, (frame) => {
                makeEncodedTexture(img, frame).then((t) => {
                    if (t) {
                        material.uniforms[key].value = t;
                        sendImageEvent('image_loaded', {
                            image_id: img.id, source: 'data', width: img.width, height: img.height,
                        });
                    }
                });
            });
        }
    });
}

// Identity of a layer for change detection.  A layer's `version` (a uuid
// bumped by `ImageData.update()` and by every fresh `ImageData`) is stable per
// content; fall back to `id` for hand-built metadata that omits it.
function _layerTag(img) {
    if (!img) return null;
    return `${img.source || 'data'}:${img.version ?? img.id}`;
}

// Bind every layer described by `imageMeta`, re-binding only the layers whose
// `version` changed (plus all tiled layers).  Without this, each
// `view_background_image` re-binds *unchanged* layers whose pixel frames were
// already consumed, registering one-shot consumers bound to stale placeholder
// metadata — which then decode a later, differently-sized frame with the wrong
// dimensions (the layer-texture race).
function _bindLayers(material, imageMeta, prevLayers) {
    const img = imageMeta || {};
    const layers = _layersOf(img);
    const layerCount = Number(img.max_layers) || 8;
    const bound = material.userData._layerVersions || (material.userData._layerVersions = new Map());
    for (let i = 0; i < layers.length && i < layerCount; i++) {
        const layer = layers[i];
        const key = `uImage${i}`;
        if (!layer) {
            // A cleared (stable-index) slot: null the sampler once.
            if (bound.get(key) !== null) {
                material.uniforms[key].value = null;
                bound.set(key, null);
            }
            continue;
        }
        const tag = _layerTag(layer);
        const prev = prevLayers && prevLayers.get(layer.id);
        if (bound.get(key) === tag) {
            // Unchanged tiled layer: keep its existing texture + resolved level
            // instead of re-fetching, so a same-image `view_background_image`
            // re-push does not reset the pyramid level or re-emit tile events.
            if (layer.source === 'tiled' && prev) {
                material.userData._tiledLayers.push(prev);
            }
            continue;
        }
        bound.set(key, tag);
        _bindLayerTexture(material, layer, i, prev);
    }
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
    // Tiled layers re-resolve their pyramid level when the view zooms; keep the
    // per-layer state on the material so `updateImageLod` can swap them.
    material.userData._tiledLayers = [];
    const mesh = new THREE.Mesh(geometry, material);
    mesh.frustumCulled = false;
    mesh.renderOrder = -1;
    // Remember which shader sources built this material so the pane can detect a
    // shader change (which requires a rebuild) versus a texture-only update.
    mesh.userData._backgroundShader = {
        fragment: img.shader?.fragment ?? null,
        vertex: img.shader?.vertex ?? null,
    };

    _bindLayers(material, img);

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
    // Re-apply color-processing + custom uniforms from the new metadata.
    applyImageUniforms(mesh, img.uniforms);
    // Capture the previous per-layer LOD state so an unchanged tiled layer keeps
    // its resolved level (and texture) across the re-bind, then re-bind only the
    // layers whose content actually changed (see `_bindLayers`).
    const prevLayers = new Map();
    for (const layer of mat.userData._tiledLayers || []) {
        prevLayers.set(layer.img.id, layer);
    }
    mat.userData._tiledLayers = [];
    _bindLayers(mat, img, prevLayers);
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
 * Set the explicit zoom-scaled letterbox half-extents (NDC) for a background
 * quad.  These override the aspect-fit letterbox derived from `uImageAspect` /
 * `uPaneAspect`; pass `0` for either axis to fall back to the aspect-fit value.
 *
 * @param {THREE.Mesh} mesh
 * @param {number} hx  display half-extent along x (NDC)
 * @param {number} hy  display half-extent along y (NDC)
 */
export function setBackgroundLetterbox(mesh, hx, hy) {
    const mat = mesh && mesh.material;
    if (mat && mat.uniforms) {
        if (mat.uniforms.uHx) mat.uniforms.uHx.value = Number(hx) || 0;
        if (mat.uniforms.uHy) mat.uniforms.uHy.value = Number(hy) || 0;
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
