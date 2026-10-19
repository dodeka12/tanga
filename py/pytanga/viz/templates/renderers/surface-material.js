// Surface material factory — turns `ent.style.surface` into a THREE material.
//
// Semantics (mirror py/pytanga/viz/surface):
//   - no surface            → the caller's `fallbackMaterial`
//   - textures only (≥1)    → a ShaderMaterial sampling the FIRST texture with
//                              the standard texture-map surface color (lit by
//                              the shared scene lighting)
//   - shader                → a ShaderMaterial running the custom GLSL program
//   - shader + textures     → the same, with every texture bound to its
//                              declared `uniform` sampler

import * as THREE from 'three';
import { buildSurfaceFragment, buildSurfaceVertex } from './surface-shader.js';
import { makeEncodedTexture } from './image.js';
import { peekImageFrame, registerImageFrameConsumer } from '../image-frames.js';
import {
    DEFAULT_LIGHTING,
    MAX_LIGHTS,
    parseHexColor,
    parseLighting,
    setLightUniforms,
} from './shader-lighting.js';

const WRAP_MODES = {
    repeat: THREE.RepeatWrapping,
    clamp: THREE.ClampToEdgeWrapping,
    mirror: THREE.MirroredRepeatWrapping,
};

function _wrapMode(value) {
    return WRAP_MODES[value] ?? THREE.RepeatWrapping;
}

function _applyTextureWrapping(texture, tex) {
    texture.wrapS = _wrapMode(tex.wrap_s);
    texture.wrapT = _wrapMode(tex.wrap_t);
    texture.repeat.set(tex.repeat_u ?? 1, tex.repeat_v ?? 1);
    texture.offset.set(tex.offset_u ?? 0, tex.offset_v ?? 0);
    texture.needsUpdate = true;
}

function _uniformValue(value) {
    if (Array.isArray(value) && value.length === 2) return new THREE.Vector2(value[0], value[1]);
    if (Array.isArray(value) && value.length === 3) return new THREE.Vector3(value[0], value[1], value[2]);
    if (Array.isArray(value) && value.length === 4) return new THREE.Vector4(value[0], value[1], value[2], value[3]);
    return value;
}

function _seedUniforms(uniforms, values) {
    for (const [name, value] of Object.entries(values || {})) {
        uniforms[name] = { value: _uniformValue(value) };
    }
}

function _lightUniforms() {
    return {
        uLightCount: { value: 0 },
        uLightDir: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uLightColor: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uAmbientColor: { value: new THREE.Vector3() },
    };
}

function _fallbackTexture() {
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

function _textureSlots(textures) {
    const slots = {};
    for (const tex of textures || []) {
        slots[tex.uniform] = { value: _fallbackTexture() };
    }
    return slots;
}

function _bindTexture(slot, tex) {
    if (!slot || !tex || tex.source === 'url' || tex.source === 'tiled') return;
    const apply = (texture) => {
        slot.value = texture;
        _applyTextureWrapping(texture, tex);
    };
    // Peek (not take) so the same texture id can be shared across several
    // surface entities without the first consumer removing it.
    const frame = peekImageFrame(tex.id);
    if (frame) {
        makeEncodedTexture(tex, frame)
            .then(apply)
            .catch((e) => console.error('[surface-material] texture failed', tex.id, e));
    } else {
        registerImageFrameConsumer(tex.id, (late) => {
            makeEncodedTexture(tex, late)
                .then(apply)
                .catch((e) => console.error('[surface-material] texture failed (late)', tex.id, e));
        });
    }
}

export function bindSurfaceTextures(material, textures) {
    if (!material || !material.uniforms) return;
    for (const tex of textures || []) {
        const slot = material.uniforms[tex.uniform];
        if (slot) _bindTexture(slot, tex);
    }
}

export function applySurfaceMaterialLighting(material, wireLighting) {
    if (!material || !material.uniforms || !material.uniforms.uAmbientColor) return false;
    setLightUniforms(material.uniforms, parseLighting(wireLighting));
    return true;
}

// Merge a partial `{ name: value }` patch into a surface ShaderMaterial's
// uniforms in place (the `surface_update` message), so shader parameters change
// without rebuilding the mesh.  Array values are re-wrapped as vector types.
export function applySurfaceMaterialUniforms(mesh, patch) {
    if (!mesh || !patch) return false;
    let changed = false;
    mesh.traverse((child) => {
        const material = child && child.material;
        if (!material || !material.uniforms) return;
        for (const [name, value] of Object.entries(patch)) {
            if (!material.uniforms[name]) continue;
            material.uniforms[name].value = _uniformValue(value);
            changed = true;
        }
    });
    return changed;
}

export function createSurfaceMaterial(ent, { fallbackMaterial } = {}) {
    const surface = ent.style && ent.style.surface;
    if (!surface) return fallbackMaterial;

    // Surface materials are opaque: the entity's canonical "shell" opacity
    // (e.g. a translucent Plane) does not apply to a textured/shader surface.
    const opacity = 1.0;
    const [r, g, b] = parseHexColor(ent.color, [1, 1, 1]);

    const hasShader = !!(surface.shader && surface.shader.fragment);
    const textures = surface.textures || [];

    if (hasShader) {
        const uniforms = {
            u_color: { value: new THREE.Vector3(r, g, b) },
            u_opacity: { value: opacity },
            ..._lightUniforms(),
            ..._textureSlots(textures),
        };
        _seedUniforms(uniforms, surface.shader.uniforms);
        setLightUniforms(uniforms, parseLighting(DEFAULT_LIGHTING));

        const material = new THREE.ShaderMaterial({
            vertexShader: surface.shader.vertex || buildSurfaceVertex(),
            fragmentShader: buildSurfaceFragment({
                userFragment: surface.shader.fragment,
                textureSamplers: textures.map((t) => t.uniform),
                sampleTexture: null,
            }),
            uniforms,
            glslVersion: THREE.GLSL3,
            transparent: opacity < 1.0,
            depthWrite: opacity >= 0.99,
            depthTest: true,
            side: THREE.DoubleSide,
        });
        bindSurfaceTextures(material, textures);
        return material;
    }

    if (textures.length) {
        const uniforms = {
            u_color: { value: new THREE.Vector3(r, g, b) },
            u_opacity: { value: opacity },
            ..._lightUniforms(),
            uTexture: { value: _fallbackTexture() },
        };
        setLightUniforms(uniforms, parseLighting(DEFAULT_LIGHTING));

        const material = new THREE.ShaderMaterial({
            vertexShader: buildSurfaceVertex(),
            fragmentShader: buildSurfaceFragment({
                userFragment: null,
                textureSamplers: ['uTexture'],
                sampleTexture: 'uTexture',
            }),
            uniforms,
            glslVersion: THREE.GLSL3,
            transparent: opacity < 1.0,
            depthWrite: opacity >= 0.99,
            depthTest: true,
            side: THREE.DoubleSide,
        });
        // Only the first texture drives the standard texture map.
        _bindTexture(uniforms.uTexture, textures[0]);
        return material;
    }

    return fallbackMaterial;
}

