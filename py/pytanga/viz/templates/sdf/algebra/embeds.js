// Point-embedding GLSL snippet registry (Phase 7).
//
// Keys are shared with Python `algebra_embedding.py` (`algebra_name`). Each
// entry is the algebra's `evalPoint(vec3 p, out float a[NP])` — the
// algebra-specific map from a 3D point to the point-blade coefficients the
// backend's `M` matrix (and its `point_ids`) expects. The point is always the
// *outer-product (OPNS)* point, fixed per algebra; the MV's `opns` flag selects
// the product (op vs ip), never the point embedding.
//
// `NP` is the point-vector size. `snippet` is emitted once per distinct algebra
// by `eval.js` (Phase 8), deduped by identity. `gradient` is the per-algebra
// closed-form `vec3 grad = …` contraction of `h[NP]` (the `Mᵀg` matvec result)
// with the point `p` — i.e. the point Jacobian `∂a/∂p` folded into `h` (Phase
// 13). It is inlined into each algebra leaf after `h` is computed.

export const embedFuncs = new Map([
    ['e3', {
        NP: 3,
        snippet: `
void evalPointE3(vec3 p, out float a[3]) {
    a[0] = p.x;
    a[1] = p.y;
    a[2] = p.z;
}`,
        gradient: `vec3 grad = vec3(h[0], h[1], h[2]);`,
    }],
    ['p3', {
        NP: 4,
        snippet: `
void evalPointP3(vec3 p, out float a[4]) {
    a[0] = p.x;
    a[1] = p.y;
    a[2] = p.z;
    a[3] = 1.0;
}`,
        gradient: `vec3 grad = vec3(h[0], h[1], h[2]);`,
    }],
    ['n3', {
        NP: 5,
        snippet: `
void evalPointN3(vec3 p, out float a[5]) {
    float rho2 = dot(p, p);
    a[0] = p.x;
    a[1] = p.y;
    a[2] = p.z;
    a[3] = 0.5 * (rho2 - 1.0);
    a[4] = 0.5 * (rho2 + 1.0);
}`,
        gradient: `vec3 grad = vec3(h[0] + p.x * (h[3] + h[4]), h[1] + p.y * (h[3] + h[4]), h[2] + p.z * (h[3] + h[4]));`,
    }],
    ['pga3', {
        NP: 7,
        snippet: `
void evalPointPGA3(vec3 p, out float a[7]) {
    a[0] = 1.0;
    a[1] = -p.z;
    a[2] = p.y;
    a[3] = -p.x;
    a[4] = -p.z;
    a[5] = p.y;
    a[6] = -p.x;
}`,
        gradient: `vec3 grad = vec3(-h[3] - h[6], h[2] + h[5], -h[1] - h[4]);`,
    }],
]);
