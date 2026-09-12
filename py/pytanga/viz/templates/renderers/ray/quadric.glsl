// Analytic ray/quadric intersection for the per-object ray proxy.
//
// The quadric is `xᵀ Q x = 0` with Q a symmetric 4×4 matrix (uniform
// `uQuadric`).  Substituting the ray `p = ro + t·rd` (homogeneous `[p, 1]`)
// yields the quadratic `a t² + b t + c = 0`; the nearest root inside the proxy
// box `[tMin, tMax]` is the hit and the surface normal is `2 A p + 2 b`, where
// `A` / `b` are the 3×3 quadratic part and the linear part of Q.

uniform mat4 uQuadric;

float intersectRay(vec3 ro, vec3 rd, float tMin, float tMax) {
    mat3 A = mat3(uQuadric);
    vec3 b = uQuadric[3].xyz;
    float c0 = uQuadric[3].w;

    float a = dot(rd, A * rd);
    float bq = 2.0 * (dot(rd, A * ro) + dot(rd, b));
    float c = dot(ro, A * ro) + 2.0 * dot(b, ro) + c0;

    // Degenerate (tangent / asymptotic) ray: fall back to the linear root.
    if (abs(a) < 1e-7) {
        if (abs(bq) < 1e-7) return -1.0;
        float t = -c / bq;
        return (t >= tMin && t <= tMax) ? t : -1.0;
    }

    float disc = bq * bq - 4.0 * a * c;
    if (disc < 0.0) return -1.0;
    float s = sqrt(disc);
    float t1 = (-bq - s) / (2.0 * a);
    float t2 = (-bq + s) / (2.0 * a);
    if (t1 > t2) {
        float tmp = t1;
        t1 = t2;
        t2 = tmp;
    }

    // Return the nearest root inside the proxy box, not the nearest root on the
    // unbounded ray: the quadric extends outside the ±10 cube, so the closest
    // intersection can lie in front of the box while the visible one is farther
    // in.  Skipping to the in-range root keeps the clipped surface continuous.
    if (t1 >= tMin && t1 <= tMax) return t1;
    if (t2 >= tMin && t2 <= tMax) return t2;
    return -1.0;
}

vec3 normalAt(vec3 p) {
    mat3 A = mat3(uQuadric);
    vec3 b = uQuadric[3].xyz;
    return normalize(2.0 * A * p + 2.0 * b);
}
