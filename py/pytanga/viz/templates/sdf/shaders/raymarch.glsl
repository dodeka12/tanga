// Raymarch fragment body — the final stage concatenated after `sdf_common`,
// `primitives`, `combinators`, and the host-injected `map` + material table
// preamble. Contains the gradient normal, IQ-style shading with per-object
// material lookup, and `main()`.
//
// Contracts injected by the host assembler (sdf_viewer.js) BEFORE this body:
//   · `vec2 map(vec3 p)`            — returns (distance, materialId) for the
//                                     composed global SDF.
//   · `vec4 materialColor(float m)` — resolves the per-object color/opacity.
//
// Uses three.js ShaderMaterial GLSL3 conventions: a declared `out vec4`
// fragment output (GLSL ES 3.0 has no `gl_FragColor`), and no
// `#version`/`precision` directive (the host shader prepends them).

uniform vec2 uResolution;
uniform vec3 uCameraPosition;
uniform mat4 uCameraWorldMatrix;
uniform mat4 uCameraProjectionMatrixInverse;
uniform float uCameraNear;
uniform float uCameraFar;

// GLSL ES 3.0 fragment output (there is no `gl_FragColor` in WebGL2).
out vec4 fragColor;

// ── Gradient normal (tetrahedral) ──────────────────────────

vec3 calcNormal(vec3 p) {
    // Finite-difference step. Must be small relative to surface features (thin
    // cylinders, ring tubes) so the gradient samples stay on the same surface;
    // `0.5773` (1/√3) is the *tetrahedral vertex coefficient*, not a step, and
    // is ~1000× too large — it made normals/lighting look patchy and per-object.
    const float e = 0.001;
    vec2 k = vec2(1.0, -1.0);
    return normalize(
        k.xyy * map(p + k.xyy * e).x +
        k.yyx * map(p + k.yyx * e).x +
        k.yxy * map(p + k.yxy * e).x +
        k.xxx * map(p + k.xxx * e).x
    );
}

// ── IQ-style shading ───────────────────────────────────────
//
// Known limitation: softShadow marches the merged `map()`, so it only sees the
// distance to the nearest *boundary* — it cannot tell a solid occluder from the
// wall/rim of a subtracted (CSG) hole. A `subtract` volume can therefore cast a
// faint penumbra even though a hole has no material to block light (e.g. the
// cylinder bored through the `composed.py` bead). A correct fix would
// trace the shadow ray against a solid-only distance field (excluding
// subtractive volumes); deferred as a known limitation.

float softShadow(vec3 ro, vec3 rd) {
    float res = 1.0;
    float t = 0.02;
    for (int i = 0; i < 32; i++) {
        float h = map(ro + rd * t).x;
        res = min(res, 8.0 * h / t);
        t += clamp(h, 0.02, 0.5);
        if (h < 0.001 || t > 20.0) break;
    }
    return clamp(res, 0.0, 1.0);
}

vec3 shade(vec3 ro, vec3 rd, vec3 p, vec3 n, float matId) {
    vec3 albedo = materialColor(matId).rgb;
    float surfaceOpacity = materialColor(matId).a;

    // Ambient term + the directional-light set (uniforms declared by the host's
    // `lightPreamble`; `uLightColor` already includes each light's intensity).
    vec3 col = albedo * uAmbientColor;
    for (int i = 0; i < MAX_LIGHTS; i++) {
        if (i >= uLightCount) break;
        vec3 L = normalize(uLightDir[i]);
        float dif = max(dot(n, L), 0.0);
        float sh = softShadow(p + n * 0.01, L);
        col += albedo * uLightColor[i] * dif * sh;
    }
    col *= (0.5 + 0.5 * n.y);

    // Fog for depth cueing.
    float dist = length(p - ro);
    float fog = 1.0 - exp(-0.05 * dist);
    vec3 bg = vec3(0.10, 0.10, 0.18);
    col = mix(col, bg, fog);

    // Per-object surface opacity (the material table's `opacity` alpha).
    col *= surfaceOpacity;
    return col;
}

void main() {
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 ndc = (2.0 * fragCoord - uResolution) / uResolution;

    // Reconstruct the world-space ray from the shared camera (camera parity).
    vec4 clip = vec4(ndc, 1.0, 1.0);
    vec4 eye = uCameraProjectionMatrixInverse * clip;
    eye /= eye.w;
    vec3 ro = uCameraPosition;
    vec3 rd = normalize((uCameraWorldMatrix * eye).xyz - ro);

    float maxDist = min(uCameraFar, MAX_DIST);
    float t = uCameraNear;
    bool hit = false;
    for (int i = 0; i < 256; i++) {
        vec3 p = ro + rd * t;
        vec2 m = map(p);
        float d = m.x;
        if (d < SDF_EPSILON) {
            hit = true;
            break;
        }
        t += d;
        if (t > maxDist) break;
    }

    vec3 bg = vec3(0.10, 0.10, 0.18);
    vec3 col;
    if (hit) {
        vec3 p = ro + rd * t;
        vec3 n = calcNormal(p);
        float matId = map(p).y;
        col = shade(ro, rd, p, n, matId);
    } else {
        col = bg;
    }

    // Depth-composited shader overlays (grid, …): each overlay is drawn over
    // the surface/background only when its plane is in front of the hit.
    col = applyOverlays(col, ro, rd, t, hit, maxDist);

    fragColor = vec4(col, 1.0);
}