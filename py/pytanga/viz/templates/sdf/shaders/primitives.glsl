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

// ── Partial disk / regular polygon ──────────────────────────

const float SDF_PI = 3.141592653589793;

// Capped sector (partial disk): a slab of half-height h and radius r, swept
// over `angle` radians, symmetric about the local +Z axis in the XZ plane
// (Y up).  This matches THREE.CylinderGeometry(thetaStart=-angle/2,
// thetaLength=angle), whose theta=0 vertex sits on +Z.  Use for 0 < angle < 2π;
// the full disk (2π) is a plain capped cylinder.
float sdPartialDisk(vec3 p, float h, float r, float angle) {
    float a = 0.5 * angle;
    vec2 c = vec2(sin(a), cos(a));
    vec2 q = p.xz;                       // q.x = p.x, q.y = p.z (IQ pie on +Y)
    q.x = abs(q.x);
    float l = length(q) - r;
    float m = length(q - c * clamp(dot(q, c), 0.0, r));
    float pie = max(l, sign(c.y * q.x - c.x * q.y) * m);
    return max(abs(p.y) - h, pie);
}

// Regular n-gon slab: a slab of half-height h, circumradius r, n sides, with a
// vertex on +Z (matching THREE.CylinderGeometry(radialSegments=n)).
float sdRegularPolygon(vec3 p, float h, float r, float n) {
    float an = SDF_PI / n;
    vec2 acs = vec2(cos(an), sin(an));
    // IQ's folding places the vertex on +X; rotate the XZ frame by -90° so the
    // vertex lands on +Z.  Only the vertex axis is reflected (valid for all n).
    vec2 q = vec2(p.z, -p.x);
    q.y = abs(q.y);
    float bn = mod(atan(q.y, q.x), 2.0 * an) - an;
    q = length(q) * vec2(cos(bn), abs(sin(bn)));
    q -= r * acs;
    q.y += clamp(-q.y, 0.0, r * acs.y);
    float d = length(q) * sign(q.x);
    return max(abs(p.y) - h, d);
}