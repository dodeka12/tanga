// Analytic ray-intersection entry point for the per-object ray proxy.
//
// The host fragment shader (in `ray.js`) calls `intersectRay` to find the
// nearest hit distance inside the proxy box `[tMin, tMax]` and `normalAt` to
// compute the surface normal at a hit point.  Phase 7 adds the quadric
// intersection here; the default is a unit-sphere fallback so the framework
// renders before that lands.

float intersectRay(vec3 ro, vec3 rd, float tMin, float tMax) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - 1.0;
    float h = b * b - c;
    if (h < 0.0) return -1.0;
    float s = sqrt(h);
    float t1 = -b - s;
    float t2 = -b + s;
    if (t1 >= tMin && t1 <= tMax) return t1;
    if (t2 >= tMin && t2 <= tMax) return t2;
    return -1.0;
}

vec3 normalAt(vec3 p) {
    return normalize(p);
}
