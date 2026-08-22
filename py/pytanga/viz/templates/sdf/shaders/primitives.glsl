// SDF primitives — ported from inigo quilez's signed-distance reference.
//
// Each primitive takes the point p in the primitive's LOCAL space (the
// transform is applied by the caller before invoking these functions).
// This file is concatenated with sdf_common.glsl; it must not contain main(),
// nor a `#version`/`precision` directive (the host shader supplies them).
//
// Axis conventions (IQ reference):
//   · cylinders/cones are aligned with the +Y axis (radius in XZ, height in Y)
//   · a torus lies in the XZ plane (major ring in XZ, tube in Y)

// ── Spheres ─────────────────────────────────────────────────

// p: local point, r: radius
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

// p: local point, r: per-axis half radii
float sdEllipsoid(vec3 p, vec3 r) {
    float k0 = length(p / r);
    float k1 = length(p / (r * r));
    return k0 * (k0 - 1.0) / k1;
}

// ── Boxes ───────────────────────────────────────────────────

// p: local point, b: axis-aligned half extents
float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

// p: local point, b: axis-aligned half extents, r: corner rounding radius
float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b + vec3(r);
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}

// ── Planes / lines ──────────────────────────────────────────

// Plane with unit normal n. IQ form: distance = dot(p, n) + h, so the plane
// satisfies dot(p, n) = -h.
float sdPlane(vec3 p, vec3 n, float h) {
    return dot(p, n) + h;
}

// Infinite line (zero radius) segment between a and b.
float sdSegment(vec3 p, vec3 a, vec3 b) {
    vec3 pa = p - a;
    vec3 ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

// Two-point capsule with hemispherical caps (radii ra, rb).
float sdCapsule(vec3 p, vec3 a, vec3 b, float ra, float rb) {
    vec3 pa = p - a;
    vec3 ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h) - mix(ra, rb, h);
}

// ── Cylinders / cones ───────────────────────────────────────

// Infinite cylinder along +Y, radius r.
float sdCylinder(vec3 p, float r) {
    return length(p.xz) - r;
}

// Capped cylinder along +Y with half-height h and radius r.
float sdCappedCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

// Infinite cone around +Y with opening angle a (radians), apex at the origin.
float sdCone(vec3 p, float a) {
    return length(p.xz) - p.y * tan(a);
}

// Capped cone along +Y: apex radius r1 at the bottom, base radius r2 at the
// top, and half-height h. IQ canonical form.
float sdCappedCone(vec3 p, float h, float r1, float r2) {
    vec2 q = vec2(length(p.xz), p.y);
    vec2 k1 = vec2(r2, h);
    vec2 k2 = vec2(r2 - r1, 2.0 * h);
    vec2 ca = vec2(q.x - min(q.x, (q.y < 0.0) ? r1 : r2), abs(q.y) - h);
    vec2 cb = q - k1 + k2 * clamp(dot(k1 - q, k2) / dot(k2, k2), 0.0, 1.0);
    float s = (cb.x < 0.0 && ca.y < 0.0) ? -1.0 : 1.0;
    return s * sqrt(min(dot(ca, ca), dot(cb, cb)));
}

// ── Torus ───────────────────────────────────────────────────

// Torus in the XZ plane: major radius t.x, minor (tube) radius t.y.
float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}