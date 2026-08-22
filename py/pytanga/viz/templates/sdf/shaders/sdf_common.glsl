#version 300 es
// SDF shared constants + rotation helpers (inigo quilez reference).
//
// This header is concatenated (never compiled standalone) into the raymarch
// program. It must not contain a main().

precision highp float;

// Small surface accuracy for the sphere-tracing loop.
float SDF_EPSILON = 0.0005;
// Hard clip distance for the ray march (overridden per-camera by cameraFar).
float MAX_DIST = 1000.0;

// ── IQ rotation helpers ─────────────────────────────────────

// Rotate around an arbitrary normalized axis.
mat3 rotationAxisAngle(vec3 axis, float angle) {
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    return mat3(
        oc * axis.x * axis.x + c,
        oc * axis.x * axis.y - axis.z * s,
        oc * axis.x * axis.z + axis.y * s,
        oc * axis.x * axis.y + axis.z * s,
        oc * axis.y * axis.y + c,
        oc * axis.y * axis.z - axis.x * s,
        oc * axis.x * axis.z - axis.y * s,
        oc * axis.y * axis.z + axis.x * s,
        oc * axis.z * axis.z + c
    );
}

// Rotate around the X axis.
mat3 rotationX(float angle) {
    float s = sin(angle);
    float c = cos(angle);
    return mat3(
        1.0, 0.0, 0.0,
        0.0, c, -s,
        0.0, s, c
    );
}

// Rotate around the Y axis.
mat3 rotationY(float angle) {
    float s = sin(angle);
    float c = cos(angle);
    return mat3(
        c, 0.0, s,
        0.0, 1.0, 0.0,
        -s, 0.0, c
    );
}

// Rotate around the Z axis.
mat3 rotationZ(float angle) {
    float s = sin(angle);
    float c = cos(angle);
    return mat3(
        c, -s, 0.0,
        s, c, 0.0,
        0.0, 0.0, 1.0
    );
}