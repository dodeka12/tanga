// Opacity transfer-function GLSL snippet registry (Phase 12).
//
// Keys are shared with Python `OpacityTransfer.value` (sdf/opacity.py). Each
// snippet is a single `opacityOf(float d, float epsilon)` function: the fixed
// call site in `raymarch.glsl` (the Phase 2 seam) is emitted here so the active
// transfer is a registry lookup with no branching.
//
// `epsilon` is the per-object falloff breadth (the per-object `opacity` value):
//   · `step`   → `epsilon` is the surface alpha (opaque on the hit band)
//   · `linear` / `sigmoid` → `epsilon` is the soft-edge breadth

export const opacityFuncs = new Map([
    ['step', {
        params: [],
        snippet: `
float opacityOf(float d, float epsilon) {
    // The ray-march loop breaks on d < SDF_EPSILON, so a hit is within that
    // (usually slightly positive) band; treat it as opaque (scaled by the
    // per-object alpha, epsilon).
    return d < SDF_EPSILON ? epsilon : 0.0;
}`,
    }],
    ['linear', {
        params: ['epsilon'],
        snippet: `
float opacityOf(float d, float epsilon) {
    float eps = max(epsilon, 1e-4);
    return clamp(1.0 - d / eps, 0.0, 1.0);
}`,
    }],
    ['sigmoid', {
        params: ['epsilon'],
        snippet: `
float opacityOf(float d, float epsilon) {
    float eps = max(epsilon, 1e-4);
    return 1.0 - 1.0 / (1.0 + exp(-d / eps));
}`,
    }],
]);
