// Analytic ray/quadric intersection for the per-object ray proxy.
//
// The quadric is `xᵀ Q x = 0` with Q a symmetric 4×4 matrix (uniform
// `uQuadric`).  Substituting the ray `p = ro + t·rd` (homogeneous `[p, 1]`)
// yields the quadratic `a t² + b t + c = 0`; the nearest positive root is the
// hit and the surface normal is `2 A p + 2 b`, where `A` / `b` are the 3×3
// quadratic part and the linear part of Q.

uniform mat4 uQuadric;

float intersectRay(vec3 ro, vec3 rd) {
    mat3 A = mat3(uQuadric);
    vec3 b = uQuadric[3].xyz;
    float c0 = uQuadric[3].w;

    float a = dot(rd, A * rd);
    float bq = 2.0 * (dot(rd, A * ro) + dot(rd, b));
    float c = dot(ro, A * ro) + 2.0 * dot(b, ro) + c0;

    // Degenerate (tangent / asymptotic) ray: fall back to the linear root.
    if (abs(a) < 1e-7) {
        if (abs(bq) < 1e-7) return -1.0;
        return -c / bq;
    }

    float disc = bq * bq - 4.0 * a * c;
    if (disc < 0.0) return -1.0;
    float s = sqrt(disc);
    float t1 = (-bq - s) / (2.0 * a);
    float t2 = (-bq + s) / (2.0 * a);

    float t = -1.0;
    if (t1 > 0.0) t = t1;
    if (t2 > 0.0 && (t < 0.0 || t2 < t)) t = t2;
    return t;
}

vec3 normalAt(vec3 p) {
    mat3 A = mat3(uQuadric);
    vec3 b = uQuadric[3].xyz;
    return normalize(2.0 * A * p + 2.0 * b);
}
