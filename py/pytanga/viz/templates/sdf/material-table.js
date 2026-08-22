// Material table (Phase 5) — per-object color/opacity upload + GLSL sampler.
//
// Serialized objects carry `color` (CSS hex) and `opacity`. We pack them into
// a fixed-size `uniform vec4 uMaterial[]` (v1; texture escalation later) and
// emit a `materialColor(float matId)` GLSL function so the raymarch body can
// resolve the hit object's albedo + opacity by material id.

export function parseHexColor(hex, fallback = [0.7, 0.6, 0.5]) {
    if (typeof hex !== 'string') return fallback;
    const m = /^#?([0-9a-fA-F]{6})$/.exec(hex.trim());
    if (!m) return fallback;
    const n = parseInt(m[1], 16);
    return [
        ((n >> 16) & 255) / 255,
        ((n >> 8) & 255) / 255,
        (n & 255) / 255,
    ];
}

// A fixed compile-time capacity so the uniform array is sized without a
// runtime texture. Escalation to a texture is a later optimization.
export const MAX_SDF_OBJECTS = 64;

// Declaration preamble injected before the raymarch body. The host sets the
// `uMaterial` uniform values every frame from `rows`.
export const materialPreamble = `
const int MAX_SDF_OBJECTS = ${MAX_SDF_OBJECTS};
uniform vec4 uMaterial[MAX_SDF_OBJECTS];
uniform int uMaterialCount;
`;

// GLSL: resolve hit material id (0-based float) to a vec4(color, opacity).
export const materialColorSrc = `
vec4 materialColor(float m) {
    int i = int(m + 0.5);
    if (i < 0 || i >= uMaterialCount) return vec4(0.0);
    return uMaterial[i];
}
`;

// Build the per-object color/opacity rows (in serialization order) and the
// matching THREE uniform array values.
export function buildMaterialRows(objects) {
    return objects.map((obj) => {
        const [r, g, b] = parseHexColor(obj.color);
        const opacity = typeof obj.opacity === 'number' ? obj.opacity : 1.0;
        return [r, g, b, opacity];
    });
}

// Pad the per-object rows up to the fixed uniform-array capacity. The shader
// declares `uMaterial[MAX_SDF_OBJECTS]`, so the uploaded array must have that
// many elements — otherwise three.js's `flatten` walks past the end of the
// array and throws while calling `.toArray()` on an undefined slot.
export function padMaterialRows(rows) {
    const padded = rows.slice();
    while (padded.length < MAX_SDF_OBJECTS) padded.push([0, 0, 0, 0]);
    return padded;
}