// Depth image renderer — a decimated grid displaced by the depth texture.
//
// The `depth_image` entity carries `frame`, `depth`, `image`, `segmentation`,
// `shader`, `mesh`, and `uniforms` metadata; pixel bytes arrive as id-keyed
// binary frames (reusing the image-frame store).  Depth and segmentation are
// nearest-filtered single-channel textures; the color image uses the standard
// mipmapped path from image.js.

import * as THREE from 'three';
import { tagEntity } from './utils.js';
import { buildDepthFragment, buildDepthVertex } from './depth-shader.js';
import {
    DEFAULT_LIGHTING,
    MAX_LIGHTS,
    parseLighting,
    setLightUniforms,
} from './shader-lighting.js';
import { makeEncodedTexture } from './image.js';
import {
    hasImageFrame,
    registerImageFrameConsumer,
    takeImageFrame,
} from '../image-frames.js';

const MAX_SELECTED_SEGMENTS = 16;

// A nearest-filtered scalar texture (depth / segmentation): reuse the shared
// decode path, then disable mipmaps and set nearest minification so the
// sentinel and integer labels are sampled exactly.
function makeScalarTexture(meta, frame) {
    return makeEncodedTexture(meta, frame).then((tex) => {
        tex.generateMipmaps = false;
        tex.minFilter = THREE.NearestFilter;
        tex.magFilter = THREE.NearestFilter;
        tex.needsUpdate = true;
        return tex;
    });
}

function fallbackTexture() {
    const tex = new THREE.DataTexture(
        new Uint8Array([255, 255, 255, 255]),
        1,
        1,
        THREE.RGBAFormat,
        THREE.UnsignedByteType
    );
    tex.needsUpdate = true;
    return tex;
}

function buildDepthUniforms(ent) {
    const u = ent.uniforms || {};
    const depth = ent.depth || {};
    const image = ent.image || {};
    const seg = ent.segmentation || {};
    // Object-space distance between adjacent depth samples (for the vertex
    // finite-difference normal): the depth grid spans the full world extent.
    const worldScale = (ent.mesh && ent.mesh.world_scale) ?? 1.0;
    const frameW = (ent.frame && ent.frame.width) || 1;
    const frameH = (ent.frame && ent.frame.height) || 1;
    const worldStep = new THREE.Vector2(
        (frameW * worldScale) / Math.max(1, (depth.width || 2) - 1),
        (frameH * worldScale) / Math.max(1, (depth.height || 2) - 1)
    );
    const cam = (ent.mesh && ent.mesh.camera) || null;
    const _DEPTH_KIND_CODES = { axial: 1, radial: 2, inverse: 3 };
    const depthKind = cam ? (_DEPTH_KIND_CODES[cam.depth_kind] ?? 1) : 0;
    const uniforms = {
        uDepth: { value: fallbackTexture() },
        uSegMask: { value: fallbackTexture() },
        uImage0: { value: fallbackTexture() },
        uDepthSize: { value: new THREE.Vector2(depth.width || 1, depth.height || 1) },
        uSegSize: { value: new THREE.Vector2(seg.width || 1, seg.height || 1) },
        uImageSize: { value: new THREE.Vector2(image.width || 1, image.height || 1) },
        u_render_mode: { value: u.u_render_mode ?? 0 },
        u_colormap: { value: u.u_colormap ?? 1 },
        u_depth_scale: { value: u.u_depth_scale ?? 1.0 },
        u_depth_offset: { value: u.u_depth_offset ?? 0.0 },
        u_depth_min: { value: u.u_depth_min ?? 0.0 },
        u_depth_max: { value: u.u_depth_max ?? 1.0 },
        u_depth_kind: { value: depthKind },
        u_fx: { value: cam ? cam.fx : 1.0 },
        u_fy: { value: cam ? cam.fy : 1.0 },
        u_cx: { value: cam ? cam.cx : 0.0 },
        u_cy: { value: cam ? cam.cy : 0.0 },
        u_frame_size: { value: new THREE.Vector2(frameW, frameH) },
        u_missing_depth: { value: u.u_missing_depth ?? -3.402823466e38 },
        u_discard_missing: { value: u.u_discard_missing ?? 1 },
        u_seg_enabled: { value: u.u_seg_enabled ?? 0 },
        u_num_selected: { value: u.u_num_selected ?? 0 },
        // uint8 masks are normalized to 0..1 on upload, so the shader rescales
        // by 255 to recover the integer label; float/uint16 need no rescale.
        u_seg_scale: { value: (seg.dtype === 0) ? 255.0 : 1.0 },
        u_selected_segments: {
            value: (u.u_selected_segments ?? new Array(MAX_SELECTED_SEGMENTS).fill(0)).slice(0, MAX_SELECTED_SEGMENTS),
        },
        u_color: { value: new THREE.Vector3(...(u.u_color ?? [1, 1, 1])) },
        u_opacity: { value: u.u_opacity ?? 1.0 },
        u_shininess: { value: u.u_shininess ?? 32.0 },
        u_specular: { value: new THREE.Vector3(...(u.u_specular ?? [1, 1, 1])) },
        uWorldStep: { value: worldStep },
        uLightCount: { value: 0 },
        uLightDir: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uLightColor: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uAmbientColor: { value: new THREE.Vector3() },
    };
    // Any custom uniform key (e.g. a custom shader's `u_angle`) rides along.
    for (const [name, value] of Object.entries(u)) {
        if (!(name in uniforms)) uniforms[name] = { value };
    }
    return uniforms;
}

// Bind a frame-backed texture (or leave the fallback in place when absent).
function bindFrameTexture(mesh, key, meta, nearest) {
    if (!meta) {
        console.log('[depth-image] bindFrameTexture skip (no meta)', key);
        return;
    }
    const make = nearest ? makeScalarTexture : makeEncodedTexture;
    const uniforms = mesh.material.uniforms;
    const has = hasImageFrame(meta.id);
    console.log('[depth-image] bindFrameTexture', key, meta.id, 'hasFrame=', has, 'nearest=', nearest);
    try {
        if (has) {
            make(meta, takeImageFrame(meta.id))
                .then((tex) => {
                    uniforms[key].value = tex;
                    console.log('[depth-image] bound texture', key, meta.id, tex.image?.width, tex.image?.height);
                })
                .catch((e) => console.error('[depth-image] texture failed', key, meta.id, e));
        } else {
            registerImageFrameConsumer(meta.id, (frame) => {
                make(meta, frame)
                    .then((tex) => {
                        uniforms[key].value = tex;
                        console.log('[depth-image] bound texture (late)', key, meta.id, tex.image?.width, tex.image?.height);
                    })
                    .catch((e) => console.error('[depth-image] texture failed (late)', key, meta.id, e));
            });
        }
    } catch (e) {
        console.error('[depth-image] bindFrameTexture threw', key, meta.id, e);
    }
}

export async function createDepthImage(ent, _opts) {
    try {
        console.log(
            '[depth-image] createDepthImage',
            ent.id,
            JSON.stringify({
                frame: ent.frame,
                mesh: ent.mesh,
                depth: ent.depth,
                image: ent.image,
                segmentation: ent.segmentation,
                customFragment: !!ent.shader?.fragment,
                customVertex: !!ent.shader?.vertex,
            })
        );

        const frame = ent.frame || {};
        const mesh = ent.mesh || {};
        const u = ent.uniforms || {};
        const worldScale = mesh.world_scale ?? 1.0;
        const cam = mesh.camera || null;
        let width;
        let height;
        if (cam) {
            // Pinhole mode: size the plane to the camera-frame footprint at the
            // clamp upper bound so the scene bounds match the rendered surface
            // (the shader derives the true positions from UV + intrinsics).
            const depthScale = u.u_depth_scale ?? 1.0;
            const depthOffset = u.u_depth_offset ?? 0.0;
            const depthMax = Math.abs(u.u_depth_max ?? 1.0) || 1.0;
            const zRef = Math.max(Math.abs((depthMax - depthOffset) * depthScale), 1e-6);
            width = (frame.width || 1) / (cam.fx || 1.0) * zRef;
            height = (frame.height || 1) / (cam.fy || 1.0) * zRef;
        } else {
            width = (frame.width || 1) * worldScale;
            height = (frame.height || 1) * worldScale;
        }
        const segU = Math.max(1, Math.round(mesh.segments_u || 1));
        const segV = Math.max(1, Math.round(mesh.segments_v || 1));

        const geometry = new THREE.PlaneGeometry(width, height, segU, segV);
        // Depth samples live at pixel centers.  Remap the plane's UVs so each
        // vertex sits on its pixel center: the rasterizer then interpolates
        // smoothly between adjacent depth samples instead of flat, nearest
        // blocks.
        {
            const pos = geometry.attributes.position;
            const uv = geometry.attributes.uv;
            const depthW = segU + 1;
            const depthH = segV + 1;
            for (let i = 0; i < uv.count; i++) {
                const gi = Math.round((pos.getX(i) / width + 0.5) * segU);
                const gj = Math.round((pos.getY(i) / height + 0.5) * segV);
                uv.setXY(i, (gi + 0.5) / depthW, (gj + 0.5) / depthH);
            }
            uv.needsUpdate = true;
        }
        const material = new THREE.ShaderMaterial({
            vertexShader: ent.shader?.vertex || buildDepthVertex(),
            fragmentShader: ent.shader?.fragment || buildDepthFragment(),
            uniforms: buildDepthUniforms(ent),
            depthWrite: true,
            side: THREE.DoubleSide,
        });
        // Light the plain surface with the shared scene-lighting default for now
        // (per-scene config plumbing is optional; this makes the plain mode lit).
        setLightUniforms(material.uniforms, parseLighting(DEFAULT_LIGHTING));
        const meshObj = new THREE.Mesh(geometry, material);

        bindFrameTexture(meshObj, 'uDepth', ent.depth, true);
        bindFrameTexture(meshObj, 'uSegMask', ent.segmentation, true);
        bindFrameTexture(meshObj, 'uImage0', ent.image, false);

        tagEntity(meshObj, ent);
        console.log(
            '[depth-image] createDepthImage done',
            ent.id,
            'geometry',
            JSON.stringify(geometry.parameters)
        );
        return meshObj;
    } catch (e) {
        console.error('[depth-image] createDepthImage threw', ent.id, e);
        throw e;
    }
}

// Structural changes (mesh resolution, texture metadata, shader source) rebuild.
export function updateDepthImage(_mesh, _ent, _prev) {
    return false;
}

// Merge a partial `{ uniforms: {...} }` patch (the `depth_image_update` message).
export function applyDepthImageUniforms(mesh, patch) {
    const material = mesh && mesh.material;
    if (!material || !material.uniforms) return false;
    for (const [name, value] of Object.entries(patch || {})) {
        const uniform = material.uniforms[name];
        if (!uniform) continue;
        if (name === 'u_color' && Array.isArray(value)) {
            uniform.value.fromArray(value);
        } else if (name === 'u_selected_segments' && Array.isArray(value)) {
            uniform.value = value.slice(0, MAX_SELECTED_SEGMENTS);
        } else {
            uniform.value = value;
        }
    }
    return true;
}

// Re-light an existing depth surface from the scene config's lighting wire block
// (falls back to the shared default when absent). Used by `three-view.js` when
// `scene_config` re-pushes.
export function applyDepthImageLighting(mesh, wireLighting) {
    const mat = mesh && mesh.material;
    if (!mat || !mat.uniforms) return false;
    setLightUniforms(mat.uniforms, parseLighting(wireLighting));
    return true;
}
