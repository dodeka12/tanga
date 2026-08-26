// Per-object SDF proxy fragment body — the final stage concatenated after
// `sdf_common`, `primitives`, `combinators`, the light preamble, and the
// host-injected single-object `float map(vec3 p)`. Marches a ray through the
// proxy box in local space, shades the surface with the shared directional
// lighting model, and writes `gl_FragDepth` so the standard depth buffer
// occludes it against meshes and other SDF proxies.
//
// Uses three.js ShaderMaterial GLSL3 conventions: a declared `out vec4`
// fragment output (no `gl_FragColor`) and no `#version`/`precision` directive
// (the host shader prepends them). Exactly one `main()`.

uniform vec4 uMaterial[MAX_GROUP_MEMBERS];
uniform float uOpacity;
uniform int uMaxSteps;
uniform float uSoftShadows;
uniform float uAntialias;
uniform vec3 uBoundHalf;
uniform mat4 uModelMatrix;
uniform mat4 uProjectionMatrix;
uniform vec3 uHover;

in vec3 vLocalPos;
flat in vec3 vCameraLocal;

out vec4 fragColor;

// ── Gradient normal (tetrahedral) ──────────────────────────

vec3 calcNormal(vec3 p) {
    const float e = 0.001;
    vec2 k = vec2(1.0, -1.0);
    return normalize(
        k.xyy * map(p + k.xyy * e).x +
        k.yyx * map(p + k.yyx * e).x +
        k.yxy * map(p + k.yxy * e).x +
        k.xxx * map(p + k.xxx * e).x
    );
}

// ── Soft self-shadow ───────────────────────────────────────

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

// ── IQ-style shading (single object) ───────────────────────

vec3 shade(vec3 p, vec3 n, vec3 ro, vec4 mat) {
    vec3 col = mat.rgb * uAmbientColor;
    for (int i = 0; i < MAX_LIGHTS; i++) {
        if (i >= uLightCount) break;
        vec3 L = normalize(uLightDir[i]);
        float dif = max(dot(n, L), 0.0);
        float sh = 1.0;
        if (uSoftShadows > 0.5) {
            sh = softShadow(p + n * 0.01, L);
        }
        col += mat.rgb * uLightColor[i] * dif * sh;
    }
    col *= (0.5 + 0.5 * n.y);

    // Fog for depth cueing (matches the fullscreen viewer's look).
    float dist = length(p - ro);
    float fog = 1.0 - exp(-0.05 * dist);
    vec3 bg = vec3(0.10, 0.10, 0.18);
    col = mix(col, bg, fog);

    // Emissive-style hover glow (black = none), set by the interaction layer.
    col += uHover;

    return col;
}

void main() {
    vec3 ro = vCameraLocal;
    vec3 rd = normalize(vLocalPos - ro);

    // Ray-box intersection with the local-space AABB [-uBoundHalf, +uBoundHalf],
    // so the march is bounded by the proxy volume (not the whole viewport).
    vec3 invDir = 1.0 / rd;
    vec3 t0 = (-uBoundHalf - ro) * invDir;
    vec3 t1 = (uBoundHalf - ro) * invDir;
    vec3 tmin = min(t0, t1);
    vec3 tmax = max(t0, t1);
    float tNear = max(max(tmin.x, tmin.y), tmin.z);
    float tFar = min(min(tmax.x, tmax.y), tmax.z);
    tNear = max(tNear, 0.0);
    if (tFar <= tNear) discard;

    float t = tNear;
    float res = tFar; // closest signed distance the ray passes the surface by
    bool hit = false;
    float m = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        if (i >= uMaxSteps) break;
        vec3 p = ro + rd * t;
        vec2 dm = map(p);
        res = min(res, dm.x);
        if (dm.x < SDF_EPSILON) {
            hit = true;
            m = dm.y;
            break;
        }
        t += dm.x;
        if (t > tFar) break;
    }
    // One-pixel silhouette edge scale: how far `t` moves across a screen pixel.
    // Euclidean derivative matches the AA'd overlays in sdf/overlays/factory.js.
    float edgePx = length(vec2(dFdx(t), dFdy(t)));
    float aa = 1.0 - smoothstep(0.0, max(edgePx, 1e-6), res);
    if (!hit) {
        if (uAntialias < 0.5 || aa < 0.001) discard;
        // Near-miss: emit a faint flat edge so the silhouette blends out over
        // the background. No valid surface point/normal exists here, so skip
        // shading and use the object's (slot-0) material colour directly.
        fragColor = vec4(uMaterial[0].rgb, uMaterial[0].a * uOpacity * aa);
        gl_FragDepth = 1.0; // far depth: the edge never occludes anything
        return;
    }

    vec3 p = ro + rd * t;
    vec3 n = calcNormal(p);
    vec4 mat = uMaterial[int(clamp(m, 0.0, float(MAX_GROUP_MEMBERS - 1)))];
    vec3 col = shade(p, n, ro, mat);

    // Write the hit's clip-space depth so occlusion against meshes and other
    // SDF proxies is handled by the standard depth buffer. three.js's WebGL2
    // depth range is [0, 1] (NDC z = clip.z / clip.w remapped).
    vec4 clip = uProjectionMatrix * viewMatrix * uModelMatrix * vec4(p, 1.0);
    float ndc = clip.z / clip.w;
    gl_FragDepth = ndc * 0.5 + 0.5;

    fragColor = vec4(col, mat.a * uOpacity);
}
