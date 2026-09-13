// Image renderer — a plane drawn by the image shader.
//
// The `image` entity carries `images[]` (metadata), `shader{}`, and
// `uniforms{}`; pixel bytes arrive separately as binary frames (see
// `../image-frames.js`).  A `source:"url"` image is loaded at runtime.

import * as THREE from 'three';
import { tagEntity } from './utils.js';
import { buildImageFragment, buildImageVertex } from './image-shader.js';
import { hasImageFrame, takeImageFrame } from '../image-frames.js';

// dtype code → THREE texture type (see py/pytanga/viz/image.py).
const DTYPE_TYPES = {
    0: THREE.UnsignedByteType,   // uint8
    1: THREE.UnsignedShortType,  // uint16 (needs WebGL2 / float texture fallback)
    2: THREE.FloatType,          // float32 (needs WebGL2 / OES_texture_float)
};

function channelsFormat(channels) {
    if (channels === 1) return THREE.LuminanceFormat;
    if (channels === 3) return THREE.RGBFormat;
    return THREE.RGBAFormat;
}

function makeDataTexture(img) {
    const frame = takeImageFrame(img.id);
    const type = DTYPE_TYPES[img.dtype] ?? THREE.UnsignedByteType;
    const format = channelsFormat(img.channels);
    const data = frame ? frame.bytes : new Uint8Array(img.width * img.height * (img.channels || 1));
    const texture = new THREE.DataTexture(data, img.width, img.height, format, type);
    texture.magFilter = THREE.NearestFilter;
    texture.minFilter = THREE.NearestFilter;
    texture.needsUpdate = true;
    return texture;
}

function buildUniforms(ent) {
    const u = ent.uniforms || {};
    const images = ent.images || [];
    const primary = images[0] || {};
    return {
        uImage0: { value: null },
        uImage1: { value: null },
        uImage2: { value: null },
        uImage3: { value: null },
        uImageSize: { value: new THREE.Vector2(primary.width || 1, primary.height || 1) },
        u_value_min: { value: u.u_value_min ?? 0.0 },
        u_value_max: { value: u.u_value_max ?? 1.0 },
        u_brightness: { value: u.u_brightness ?? 0.0 },
        u_contrast: { value: u.u_contrast ?? 1.0 },
        u_midpoint: { value: u.u_midpoint ?? 0.5 },
        u_mode: { value: u.u_mode ?? 1 },
    };
}

export async function createImage(ent) {
    const frame = ent.frame || {};
    const width = frame.width || 1;
    const height = frame.height || 1;

    const geometry = new THREE.PlaneGeometry(width, height);
    const uniforms = buildUniforms(ent);

    const fragment = ent.shader?.fragment || buildImageFragment();
    const vertex = ent.shader?.vertex || buildImageVertex();

    const material = new THREE.ShaderMaterial({
        vertexShader: vertex,
        fragmentShader: fragment,
        uniforms,
    });

    const mesh = new THREE.Mesh(geometry, material);
    // Centre the plane on the pixel extent [−0.5, W−0.5] × [−0.5, H−0.5].
    mesh.position.set(width / 2 - 0.5, height / 2 - 0.5, 0);

    const images = ent.images || [];
    for (let i = 0; i < images.length && i < 4; i++) {
        const img = images[i];
        const key = `uImage${i}`;
        if (img.source === 'url') {
            uniforms[key].value = await new Promise((resolve) => {
                new THREE.TextureLoader().load(
                    img.url,
                    (t) => { t.minFilter = THREE.NearestFilter; t.magFilter = THREE.NearestFilter; resolve(t); },
                    undefined,
                    () => resolve(null)
                );
            });
        } else if (hasImageFrame(img.id)) {
            uniforms[key].value = makeDataTexture(img);
        }
    }

    tagEntity(mesh, ent);
    return mesh;
}

export function updateImage(mesh, ent, prev) {
    const material = mesh.material;
    if (!material || !material.uniforms) return false;
    const uniforms = ent.uniforms || {};
    if (material.uniforms.u_value_min) material.uniforms.u_value_min.value = uniforms.u_value_min ?? 0.0;
    if (material.uniforms.u_value_max) material.uniforms.u_value_max.value = uniforms.u_value_max ?? 1.0;
    if (material.uniforms.u_brightness) material.uniforms.u_brightness.value = uniforms.u_brightness ?? 0.0;
    if (material.uniforms.u_contrast) material.uniforms.u_contrast.value = uniforms.u_contrast ?? 1.0;
    if (material.uniforms.u_midpoint) material.uniforms.u_midpoint.value = uniforms.u_midpoint ?? 0.5;
    if (material.uniforms.u_mode) material.uniforms.u_mode.value = uniforms.u_mode ?? 1;
    return true;
}

// Merge a partial `{ uniforms: {...} }` patch (the `image_update` message).
export function applyImageUniforms(mesh, patch) {
    const material = mesh?.material;
    if (!material || !material.uniforms) return false;
    for (const [name, value] of Object.entries(patch || {})) {
        if (material.uniforms[name]) material.uniforms[name].value = value;
    }
    return true;
}
