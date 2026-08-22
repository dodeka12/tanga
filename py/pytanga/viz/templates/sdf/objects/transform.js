// Local-space transform expression for an SDF node.
//
// A node's `transform` places its primitive in world space. To evaluate the
// primitive (which expects LOCAL coordinates), we build the inverse transform
// as an inline GLSL expression: translate by `-position`, then rotate by
// `-angle` (via the shared `rotationAxisAngle` helper from `sdf_common.glsl`).

export function transformExpr(transform, p = 'p') {
    const pos = transform?.position || [0, 0, 0];
    let expr = `(${p} - vec3(${floatParam(pos[0])}, ${floatParam(pos[1])}, ${floatParam(pos[2])}))`;
    if (transform?.rotation) {
        const axis = transform.rotation.axis;
        const angle = transform.rotation.angle;
        expr = `rotationAxisAngle(normalize(vec3(${floatParam(axis[0])}, ${floatParam(axis[1])}, ${floatParam(axis[2])})), ${floatParam(-angle)}) * ${expr}`;
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