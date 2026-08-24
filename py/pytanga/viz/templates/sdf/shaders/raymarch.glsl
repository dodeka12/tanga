// Raymarch fragment body — the final stage concatenated after `sdf_common`,
// `primitives`, `combinators`, and the host-injected `map` + material table
// preamble. Contains the `opacityOf()` step stub (replaced by Phase 12), the
// gradient normal, IQ-style shading with per-object material lookup, and
// `main()`.
//
// Contracts injected by the host assembler (sdf_viewer.js) BEFORE this body:
//   · `vec2 map(vec3 p)`            — returns (distance, materialId) for the
//                                     composed global SDF (Phase 5) or the
//                                     `M·a → distOf` evaluator (Phase 8).
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

// ── Opacity transfer (call site; the function is injected by the host) ──
// The `opacityOf(float d, float epsilon)` function is emitted by the host
// assembler (`sdf_viewer.js`) from `algebra/opacities.js` — the active transfer
// (`step`/`linear`/`sigmoid`) is a registry lookup, never a shader branch. The
// Phase 2 call site is fixed here; only the injected snippet changes.

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

// ── Gradient magnitude (tetrahedral, unnormalized) ──────────
//
// The *norm* of the field gradient at `p` — the same tetrahedral stencil as
// `calcNormal`, but without normalization. Used to scale the sphere-tracing
// step for non-1-Lipschitz (algebraic) fields, where `d` alone overshoots.

float calcGradientNorm(vec3 p) {
    const float e = 0.001;
    vec2 k = vec2(1.0, -1.0);
    vec3 g =
        k.xyy * map(p + k.xyy * e).x +
        k.yyx * map(p + k.yyx * e).x +
        k.yxy * map(p + k.yxy * e).x +
        k.xxx * map(p + k.xxx * e).x;
    return length(g) / (4.0 * e);
}

// ── IQ-style shading ───────────────────────────────────────
//
// Known limitation: softShadow marches the merged `map()`, so it only sees the
// distance to the nearest *boundary* — it cannot tell a solid occluder from the
// wall/rim of a subtracted (CSG) hole. A `subtract` volume can therefore cast a
// faint penumbra even though a hole has no material to block light (e.g. the
// cylinder bored through the `demo_sdf_composed.py` bead). A correct fix would
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

    // Per-object surface opacity (the per-object `opacity` is ε: the surface
    // alpha for `step`, the soft-edge breadth for `linear`/`sigmoid`).
    col *= opacityOf(map(p).x, surfaceOpacity);
    return col;
}

// ── Volumetric density (per-object exponential falloff + hard cutoff) ──
//
// For a soft `mv_sdf` object (`falloff > 0`), the density outside the core is
// σ(d) = exp(−d/falloff)/falloff  (Beer–Lambert), hard-clipped to zero beyond
// `max_distance` (default `5·falloff`). `d` is the thickness-shifted distance
// already returned by the algebra leaf. Analytic/hard objects have `falloff ==
// 0` → no density (they stay hard surfaces).

float mapDensity(float d, float matIdF) {
    int matId = int(matIdF + 0.5);
    if (matId < 0 || matId >= uMaterialCount) return 0.0;
    float falloff = u_ObjectParams[matId].z;
    if (falloff <= 0.0) return 0.0;
    float cutoff = u_ObjectParams[matId].w;
    if (cutoff <= 0.0) cutoff = 5.0 * falloff;
    if (d <= 0.0 || d >= cutoff) return 0.0;
    return exp(-d / falloff) / falloff;
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
    float transmittance = 1.0;
    float haloMatId = -1.0;
    float maxSigma = 0.0;
    for (int i = 0; i < 256; i++) {
        vec3 p = ro + rd * t;
        vec2 m = map(p);
        float d = m.x;
        float sigma = mapDensity(d, m.y);
        if (sigma > maxSigma) {
            maxSigma = sigma;
            haloMatId = m.y;
        }
        transmittance *= exp(-sigma * d);
        if (d < SDF_EPSILON) {
            hit = true;
            break;
        }
        // Analytic objects are proper SDFs (|∇d| = 1), so step `d` directly.
        // Algebraic (`mv_sdf`) objects are not 1-Lipschitz (|∇d| can exceed 1
        // and even grow), so step `d / max(|∇d|, 1)` — the local first-order
        // distance to the surface — to avoid overshooting the thin surface.
        // The per-object `u_ObjectParams.w` is `max_distance >= 0` for algebraic
        // objects and the sentinel `-1` for analytic ones.
        float stepSize = d;
        int matId = int(m.y + 0.5);
        if (matId >= 0 && matId < uMaterialCount && u_ObjectParams[matId].w > -0.5) {
            stepSize = d / max(calcGradientNorm(p), 1.0);
        }
        t += stepSize;
        if (t > maxDist || transmittance < 0.01) break;
    }

    vec3 bg = vec3(0.10, 0.10, 0.18);
    vec3 col;
    if (hit) {
        vec3 p = ro + rd * t;
        vec3 n = calcNormal(p);
        float matId = map(p).y;
        col = shade(ro, rd, p, n, matId);
    } else {
        // Soft halo for a grazing ray (passed through a soft object's density
        // but missed its core): blend the object's color by the absorbed amount.
        float opacity = 1.0 - transmittance;
        if (opacity > 0.0 && haloMatId >= 0.0) {
            vec3 haloColor = materialColor(haloMatId).rgb;
            col = mix(bg, haloColor, opacity);
        } else {
            col = bg;
        }
    }

    // Depth-composited shader overlays (grid, …): each overlay is drawn over
    // the surface/background only when its plane is in front of the hit.
    col = applyOverlays(col, ro, rd, t, hit, maxDist);

    fragColor = vec4(col, 1.0);
}