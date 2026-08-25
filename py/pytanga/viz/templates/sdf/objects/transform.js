// Local-space transform expression for an SDF node.
//
// A node's `transform` places its primitive in world space: the serializer
// emits an axis-angle pair `(axis, angle)` that rotates the LOCAL frame onto
// the world frame (a +angle rotation maps local → world). To evaluate the
// primitive — which expects LOCAL coordinates — we must apply the *inverse*,
// i.e. a −angle rotation, to the world point after translating by `-position`.
//
// IQ's `rotationAxisAngle(axis, θ)` already negates the angle internally: it
// returns the transpose of the standard Rodrigues matrix, so it rotates a
// point by −θ around `axis`. To obtain a −angle rotation we therefore pass
// **+angle** (not −angle).

export function transformExpr(transform, p = 'p') {
    const pos = transform?.position || [0, 0, 0];
    let expr = `(${p} - vec3(${floatParam(pos[0])}, ${floatParam(pos[1])}, ${floatParam(pos[2])}))`;
    if (transform?.rotation) {
        const axis = transform.rotation.axis;
        const angle = transform.rotation.angle;
        expr = `rotationAxisAngle(normalize(vec3(${floatParam(axis[0])}, ${floatParam(axis[1])}, ${floatParam(axis[2])})), ${floatParam(angle)}) * ${expr}`;
    }
    return expr;
}

export function floatParam(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return '0.0';
    const s = String(n);
    // GLSL ES 3.0 has no implicit int → float conversion, so integral values
    // must carry a `.0` suffix (`3` is an int literal, `3.0` is a float).
    return /[.eE]/.test(s) ? s : `${s}.0`;
}