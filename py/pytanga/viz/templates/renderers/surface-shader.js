// Surface shader — vertex/fragment GLSL assembly for textured and custom-shaded
// solid surfaces.  Pure GLSL string building (Node-testable, mirrors
// image-shader.js / depth-shader.js).
//
// Custom fragment contract (documented for users):
//   - The host declares the varyings `vUv`, `vNormal`, `vWorldPosition`,
//     `vLocalPos`, the uniforms `u_color` / `u_opacity`, the texture samplers
//     listed in `textureSamplers`, and the scene-lighting preamble
//     (`MAX_LIGHTS`, `uLightCount`, `uLightDir[]`, `uLightColor[]`,
//     `uAmbientColor`) plus a `tangaLight(albedo, n, p)` helper.
//   - The fragment must define
//     `vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p)`, which the host
//     `main()` calls.  `baseColor` is `u_color` for a custom shader, or the
//     sampled first texture for the standard texture map.

import { lightPreamble } from './shader-lighting.js';

export function buildSurfaceVertex() {
    return `
out vec3 vLocalPos;
out vec3 vNormal;
out vec3 vWorldPosition;
out vec2 vUv;

void main() {
    vUv = uv;
    vLocalPos = position;
    vNormal = normalize(normalMatrix * normal);
    vec4 worldPosition = modelMatrix * vec4(position, 1.0);
    vWorldPosition = worldPosition.xyz;
    gl_Position = projectionMatrix * viewMatrix * worldPosition;
}`;
}

// The standard texture-map surface color: light the sampled albedo with the
// scene's global ambient + directional lights (shared with custom shaders).
export function buildStandardTextureSurfaceColor() {
    return `
vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p) {
    return tangaLight(baseColor, n, p);
}`;
}

export function buildSurfaceFragment({
    userFragment = null,
    textureSamplers = [],
    sampleTexture = null,
} = {}) {
    const samplerDecls = textureSamplers
        .map((name) => `uniform sampler2D ${name};`)
        .join('\n');
    const baseColorExpr = sampleTexture
        ? `texture2D(${sampleTexture}, vUv).rgb`
        : 'u_color';
    const surfaceColorBody = userFragment || buildStandardTextureSurfaceColor();

    return `
in vec3 vLocalPos;
in vec3 vNormal;
in vec3 vWorldPosition;
in vec2 vUv;

out vec4 fragColor;

${lightPreamble}

uniform vec3 u_color;
uniform float u_opacity;

${samplerDecls}

vec3 tangaLight(vec3 albedo, vec3 n, vec3 p) {
    vec3 col = albedo * uAmbientColor;
    for (int i = 0; i < MAX_LIGHTS; i++) {
        if (i >= uLightCount) break;
        vec3 L = normalize(uLightDir[i]);
        float dif = max(dot(n, L), 0.0);
        col += albedo * uLightColor[i] * dif;
    }
    return col;
}

${surfaceColorBody}

void main() {
    vec3 baseColor = ${baseColorExpr};
    vec3 n = normalize(vNormal);
    vec3 p = vWorldPosition;
    fragColor = vec4(surfaceColor(baseColor, n, p), u_opacity);
}`;
}
