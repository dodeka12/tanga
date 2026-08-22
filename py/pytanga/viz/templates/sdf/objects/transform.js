// Local-space transform expression for an SDF node.
//
// A node's `transform` places its primitive in world space. To evaluate the
// primitive (which expects LOCAL coordinates), we build the inverse transform
// as an inline GLSL expression: translate by `-position`, then rotate by
// `-angle` (via the shared `rotationAxisAngle` helper from `sdf_common.glsl`).

export function transformExpr(transform, p = 'p') {
    const pos = transform?.position || [0, 0, 0];
    let expr = `(${p} - vec3(${pos[0]}, ${pos[1]}, ${pos[2]}))`;
    if (transform?.rotation) {
        const axis = transform.rotation.axis;
        const angle = transform.rotation.angle;
        expr = `rotationAxisAngle(normalize(vec3(${axis[0]}, ${axis[1]}, ${axis[2]})), ${-angle}) * ${expr}`;
    }
    return expr;
}

export function floatParam(value) {
    return String(Number(value));
}