// Image renderer — a plane drawn by the image shader.
//
// The `image` entity carries `images[]` (metadata), `shader{}`, and
// `uniforms{}`; pixel bytes arrive separately as binary frames (see
// `../image-frames.js`).  A `source:"url"` image is loaded at runtime.

import * as THREE from 'three';
import { tagEntity } from './utils.js';
import { buildImageFragment, buildImageVertex } from './image-shader.js';
import { bestPyramidLevel } from './image-tiles.js';
import { hasImageFrame, takeImageFrame } from '../image-frames.js';

// dtype code → THREE texture type + element width (see py/pytanga/viz/image.py).
const DTYPE_TYPES = {
    0: { type: THREE.UnsignedByteType, bytesPerElement: 1 },   // uint8
    1: { type: THREE.FloatType, bytesPerElement: 2 },          // uint16 (widened to float32)
    2: { type: THREE.FloatType, bytesPerElement: 4 },          // float32
};

// View the raw frame bytes as the dtype's element type.
function typedArrayFor(dtype, bytes) {
    if (dtype === 1) return new Uint16Array(bytes.buffer, bytes.byteOffset, bytes.length / 2);
    if (dtype === 2) return new Float32Array(bytes.buffer, bytes.byteOffset, bytes.length / 4);
    return new Uint8Array(bytes.buffer, bytes.byteOffset, bytes.length);
}

// Expand a 1/3-channel buffer to 4-channel RGBA.  uint8 stays 8-bit (the only
// normalized 8-bit color format three.js r170 uploads to WebGL2 —
// RGBFormat/LuminanceFormat were removed).  uint16 is widened to float32 because
// three.js `UnsignedShortType` maps to an *integer* texture (RGBA16UI) that a
// float `sampler2D` cannot sample; float32 is already the right width.  Both
// non-8-bit paths are lossless for the full 0..65535 range.
function toRgba(arr, channels) {
    const n = arr.length / channels;
    const useFloat = arr instanceof Float32Array || arr instanceof Uint16Array;
    const rgba = useFloat ? new Float32Array(n * 4) : new Uint8Array(n * 4);
    const alpha = useFloat ? 1.0 : 0xFF;
    if (channels === 1) {
        for (let i = 0; i < n; i++) {
            const v = arr[i];
            rgba[i * 4] = v; rgba[i * 4 + 1] = v; rgba[i * 4 + 2] = v; rgba[i * 4 + 3] = alpha;
        }
    } else if (channels === 3) {
        for (let i = 0; i < n; i++) {
            rgba[i * 4] = arr[i * 3];
            rgba[i * 4 + 1] = arr[i * 3 + 1];
            rgba[i * 4 + 2] = arr[i * 3 + 2];
            rgba[i * 4 + 3] = alpha;
        }
    } else {
        rgba.set(arr);
    }
    return rgba;
}

function emptyTypedArray(dtype, length) {
    if (dtype === 2) return new Float32Array(length);
    if (dtype === 1) return new Uint16Array(length);
    return new Uint8Array(length);
}

export function makeDataTexture(img, bytes) {
    const width = img.width;
    const height = img.height;
    const channels = img.channels || 1;
    const dtype = img.dtype ?? 0;
    const spec = DTYPE_TYPES[dtype] ?? DTYPE_TYPES[0];

    const frameBytes = bytes ?? (hasImageFrame(img.id) ? takeImageFrame(img.id).bytes : null);
    const raw = frameBytes
        ? typedArrayFor(dtype, frameBytes)
        : emptyTypedArray(dtype, width * height * channels);
    const data = toRgba(raw, channels);

    const texture = new THREE.DataTexture(data, width, height, THREE.RGBAFormat, spec.type);
    texture.magFilter = THREE.NearestFilter;
    // 8-bit data gets mipmaps + trilinear minification; float (uint16/float32)
    // data uses bilinear minification (float mipmap generation isn't universal).
    if (dtype === 0) {
        texture.generateMipmaps = true;
        texture.minFilter = THREE.LinearMipmapLinearFilter;
    } else {
        texture.minFilter = THREE.LinearFilter;
    }
    // `DataTexture` defaults to `flipY = false` (raw bytes, row 0 -> bottom
    // texel), but the image plane samples with the image's row 0 at the *top*
    // of the pane (matching the JPEG / URL / tiled / stream paths, whose
    // textures default to `flipY = true`).  Flip so every codec lines up.
    texture.flipY = true;
    texture.needsUpdate = true;
    return texture;
}

// Decode a frame into a texture, dispatching on the frame's `codec`:
//   'jpeg' → createImageBitmap (GPU decode, RGBA, off-main-thread)
//   'zlib' → DecompressionStream, then the raw DataTexture path
//   'raw'  → the raw DataTexture path
export async function makeEncodedTexture(img, frame) {
    if (frame && frame.codec === 'jpeg') {
        const blob = new Blob([frame.bytes], { type: 'image/jpeg' });
        const bitmap = await createImageBitmap(blob);
        // Draw through a 2D canvas so the JPEG path shares the orientation and
        // filtering contract of the tiled/stream/data paths.  `ImageBitmap`
        // uploads don't honor `flipY` the way raw pixel data does, so a plain
        // `THREE.Texture(bitmap)` renders vertically flipped.
        const canvas = document.createElement('canvas');
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(bitmap, 0, 0);
        bitmap.close();
        const texture = new THREE.CanvasTexture(canvas);
        texture.flipY = true;
        texture.magFilter = THREE.NearestFilter;
        texture.generateMipmaps = true;
        texture.minFilter = THREE.LinearMipmapLinearFilter;
        texture.needsUpdate = true;
        return texture;
    }

    let bytes = frame ? frame.bytes : null;
    if (frame && frame.codec === 'zlib') {
        const stream = new Blob([frame.bytes]).stream()
            .pipeThrough(new DecompressionStream('deflate'));
        bytes = new Uint8Array(await new Response(stream).arrayBuffer());
    }

    return makeDataTexture(img, bytes);
}

// Compose a tiled float32/uint16 image into one float DataTexture by fetching
// the best-fitting level's tiles as zlib-compressed raw pixels, inflating them,
// expanding to RGBA, and placing them edge-clipped into a single buffer.
async function makeTiledDataTexture(img) {
    const tileSize = img.tile_size || 256;
    const level = bestPyramidLevel(img);
    const levelW = Math.ceil(img.width / (2 ** level));
    const levelH = Math.ceil(img.height / (2 ** level));
    const cols = Math.ceil(levelW / tileSize);
    const rows = Math.ceil(levelH / tileSize);
    const channels = img.channels || 1;
    const dtype = img.dtype ?? 0;

    const data = new Float32Array(levelW * levelH * 4);

    const jobs = [];
    for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
            jobs.push((async () => {
                const resp = await fetch(`/image/${img.id}/${level}/${x}/${y}?format=zlib`);
                if (!resp.ok) return;
                const compressed = new Uint8Array(await resp.arrayBuffer());
                const stream = new Blob([compressed]).stream()
                    .pipeThrough(new DecompressionStream('deflate'));
                const bytes = new Uint8Array(await new Response(stream).arrayBuffer());
                const rgba = toRgba(typedArrayFor(dtype, bytes), channels);
                const tileW = Math.min(tileSize, levelW - x * tileSize);
                const tileH = Math.min(tileSize, levelH - y * tileSize);
                for (let ty = 0; ty < tileH; ty++) {
                    const src = ty * tileW * 4;
                    const dst = ((y * tileSize + ty) * levelW + x * tileSize) * 4;
                    data.set(rgba.subarray(src, src + tileW * 4), dst);
                }
            })());
        }
    }
    await Promise.all(jobs);

    const texture = new THREE.DataTexture(data, levelW, levelH, THREE.RGBAFormat, THREE.FloatType);
    texture.magFilter = THREE.NearestFilter;
    texture.minFilter = THREE.LinearFilter; // no float mipmaps (matches makeDataTexture)
    texture.flipY = true;
    texture.needsUpdate = true;
    return texture;
}

// Compose a tiled image into one texture by fetching the tiles of the
// best-fitting level (long side ≤ 2048 px).  uint8 uses JPEG/PNG tiles drawn
// to a canvas; float32/uint16 use zlib tiles assembled into a float texture.
// The `source === "tiled"` metadata is `{id, width, height, tile_size, levels,
// dtype, channels}` (see `ImagePyramid.meta`).
export async function makeTiledTexture(img) {
    if (img.dtype === 1 || img.dtype === 2) {
        return makeTiledDataTexture(img);
    }

    const tileSize = img.tile_size || 256;
    const level = bestPyramidLevel(img);
    const scale = 2 ** level;
    const levelW = Math.ceil(img.width / scale);
    const levelH = Math.ceil(img.height / scale);
    const cols = Math.ceil(levelW / tileSize);
    const rows = Math.ceil(levelH / tileSize);

    const canvas = document.createElement('canvas');
    canvas.width = levelW;
    canvas.height = levelH;
    const ctx = canvas.getContext('2d');
    const format = (img.dtype === 0 && (img.channels === 1 || img.channels === 3)) ? 'jpeg' : 'png';

    const jobs = [];
    for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
            jobs.push((async () => {
                const resp = await fetch(`/image/${img.id}/${level}/${x}/${y}?format=${format}`);
                if (!resp.ok) return;
                const bitmap = await createImageBitmap(await resp.blob());
                ctx.drawImage(bitmap, x * tileSize, y * tileSize);
                bitmap.close();
            })());
        }
    }
    await Promise.all(jobs);

    const texture = new THREE.CanvasTexture(canvas);
    texture.generateMipmaps = true;
    texture.minFilter = THREE.LinearMipmapLinearFilter;
    texture.magFilter = THREE.NearestFilter;
    texture.needsUpdate = true;
    return texture;
}

// Stream an MJPEG camera feed (`/stream/{id}`) into a texture via a hidden
// `<img>` (browsers decode multipart/x-mixed-replace natively) redrawn to a
// canvas each animation frame.
export function makeStreamTexture(img) {
    const el = document.createElement('img');
    el.src = img.url;
    el.style.display = 'none';
    document.body.appendChild(el);

    const canvas = document.createElement('canvas');
    canvas.width = img.width || 1;
    canvas.height = img.height || 1;
    const ctx = canvas.getContext('2d');

    const texture = new THREE.CanvasTexture(canvas);
    texture.generateMipmaps = true;
    texture.minFilter = THREE.LinearMipmapLinearFilter;
    texture.magFilter = THREE.NearestFilter;

    const update = () => {
        if (el.naturalWidth > 0) {
            if (canvas.width !== el.naturalWidth || canvas.height !== el.naturalHeight) {
                canvas.width = el.naturalWidth;
                canvas.height = el.naturalHeight;
            }
            ctx.drawImage(el, 0, 0);
            texture.needsUpdate = true;
        }
        requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
    return texture;
}

function buildUniforms(ent) {
    const u = ent.uniforms || {};
    const images = ent.images || [];
    const primary = images[0] || {};
    const uniforms = {
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
    // Custom shader uniforms — any key beyond the standard set above (e.g.
    // a custom shader's `u_angle`).  `image_update` patches reuse the same
    // keys via `applyImageUniforms`.
    for (const [name, value] of Object.entries(u)) {
        if (!(name in uniforms)) {
            uniforms[name] = { value };
        }
    }
    return uniforms;
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
            if (typeof img.url === 'string' && img.url.includes('/stream/')) {
                uniforms[key].value = makeStreamTexture(img);
            } else {
                uniforms[key].value = await new Promise((resolve) => {
                    new THREE.TextureLoader().load(
                        img.url,
                        (t) => { t.minFilter = THREE.NearestFilter; t.magFilter = THREE.NearestFilter; resolve(t); },
                        undefined,
                        () => resolve(null)
                    );
                });
            }
        } else if (img.source === 'tiled') {
            uniforms[key].value = await makeTiledTexture(img);
        } else if (hasImageFrame(img.id)) {
            uniforms[key].value = await makeEncodedTexture(img, takeImageFrame(img.id));
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
