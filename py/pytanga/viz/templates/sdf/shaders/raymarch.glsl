// Raymarch fragment body — the final stage concatenated after `sdf_common`,
// `primitives`, and `combinators`. Contains the Phase 2 hardcoded `map()`, the
// `opacityOf()` step stub (replaced by Phase 12), the gradient normal, IQ-style
// shading, and `main()`.
//
// Uses three.js ShaderMaterial GLSL3 conventions: `gl_FragColor` (three maps it
// to its `pc_fragColor` out variable), and NO `#version`/`precision` directive
// (the host shader prepends them).

uniform vec2 uResolution;
uniform vec3 uCameraPosition;
uniform mat4 uCameraWorldMatrix;
uniform mat4 uCameraProjectionMatrixInverse;
uniform float uCameraNear;
uniform float uCameraFar;

// ── Phase 2 hardcoded test surface ─────────────────────────
// A unit sphere at the origin; later phases replace this with the composed
// global SDF (Phase 5) and the algebra evaluator (Phase 8).

float map(vec3 p) {
    return sdSphere(p, 1.0);
}

// ── Opacity transfer (step stub) ───────────────────────────
// The call site and its `step` default are fixed now so Phase 12 only swaps
// this snippet for `linear`/`sigmoid` without touching the raymarch body.

float opacityOf(float d) {
    return d < 0.0 ? 1.0 : 0.0;
}

// ── Gradient normal (tetrahedral) ──────────────────────────

vec3 calcNormal(vec3 p) {
    const float e = 0.5773;
    vec2 k = vec2(1.0, -1.0);
    return normalize(
        k.xyy * map(p + k.xyy * e) +
        k.yyx * map(p + k.yyx * e) +
        k.yxy * map(p + k.yxy * e) +
        k.xxx * map(p + k.xxx * e)
    );
}

// ── IQ-style shading ───────────────────────────────────────

float softShadow(vec3 ro, vec3 rd) {
    float res = 1.0;
    float t = 0.02;
    for (int i = 0; i < 32; i++) {
        float h = map(ro + rd * t);
        res = min(res, 8.0 * h / t);
        t += clamp(h, 0.02, 0.5);
        if (h < 0.001 || t > 20.0) break;
    }
    return clamp(res, 0.0, 1.0);
}

vec3 shade(vec3 ro, vec3 rd, vec3 p, vec3 n) {
    vec3 albedo = vec3(0.7, 0.6, 0.5);  // Phase 2 fixed albedo
    vec3 lightDir = normalize(vec3(10.0, 20.0, 10.0));
    float amb = 0.45;
    float dif = max(dot(n, lightDir), 0.0) * 0.8;
    float sh = softShadow(p + n * 0.01, lightDir);
    vec3 col = albedo * (amb + dif * sh) * (0.5 + 0.5 * n.y);

    // Fog for depth cueing.
    float dist = length(p - ro);
    float fog = 1.0 - exp(-0.05 * dist);
    vec3 bg = vec3(0.10, 0.10, 0.18);
    col = mix(col, bg, fog);
    return col;
}

void main() {
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 ndc = (2.0 * fragCoord - uResolution) / uResolution.y;

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
        float d = map(p);
        if (d < SDF_EPSILON) {
            hit = true;
            break;
        }
        t += d;
        if (t > maxDist) break;
    }

    vec3 col;
    if (hit) {
        vec3 p = ro + rd * t;
        vec3 n = calcNormal(p);
        col = shade(ro, rd, p, n);
        col *= opacityOf(map(p));
    } else {
        col = vec3(0.10, 0.10, 0.18);
    }

    gl_FragColor = vec4(col, 1.0);
}