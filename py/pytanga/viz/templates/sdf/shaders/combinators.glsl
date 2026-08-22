// SDF Boolean/combinator helpers — ported from inigo quilez's reference.
//
// Hard combinators fold two scalar distances with exact sign preservation:
//   · opUnion        → min(a, b)              (inside either)
//   · opIntersect    → max(a, b)              (inside both)
//   · opSubtract     → max(a, -b)             (inside a, not inside b)
//
// Smooth combinators return vec2(d, h) where d is the blended distance and h
// is the blend/material factor IQ uses to drive material-ID mixing.
//
// This file is concatenated with sdf_common.glsl; it must not contain main(),
// nor a `#version`/`precision` directive (the host shader supplies them).

// ── Hard combinators ────────────────────────────────────────

float opUnion(float d1, float d2) {
    return min(d1, d2);
}

float opSubtract(float d1, float d2) {
    return max(d1, -d2);
}

float opIntersect(float d1, float d2) {
    return max(d1, d2);
}

// ── Smooth combinators (vec2: x = distance, y = blend factor) ──

vec2 opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return vec2(mix(d2, d1, h) - k * h * (1.0 - h), h);
}

vec2 opSmoothSubtract(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 + d1) / k, 0.0, 1.0);
    return vec2(mix(d2, -d1, h) + k * h * (1.0 - h), h);
}

vec2 opSmoothIntersect(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return vec2(mix(d2, d1, h) + k * h * (1.0 - h), h);
}