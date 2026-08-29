// Analytic ray-intersection entry point for the per-object ray proxy.
//
// The host fragment shader (in `ray.js`) calls `intersectRay` to find the
// nearest positive hit distance along the ray and `normalAt` to compute the
// surface normal at a hit point.  Phase 7 adds the quadric intersection here;
// the default is a unit-sphere fallback so the framework renders before that
// lands.

float intersectRay(vec3 ro, vec3 rd) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - 1.0;
    float h = b * b - c;
    if (h < 0.0) return -1.0;
    float t = -b - sqrt(h);
    if (t < 0.0) t = -b + sqrt(h);
    return t < 0.0 ? -1.0 : t;
}

vec3 normalAt(vec3 p) {
    return normalize(p);
}
