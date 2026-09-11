import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { Line2 } from 'three/addons/lines/Line2.js';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { LineGeometry } from 'three/addons/lines/LineGeometry.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';

window.__tanga_sdf_shaders = {"common": "// SDF shared constants + rotation helpers (inigo quilez reference).\n//\n// Concatenated (never compiled standalone) into the raymarch shader. It must\n// not contain a main(), nor a `#version`/`precision` directive \u2014 the host\n// assembles a single shader and three.js prepends GLSL3 `#version 300 es` and\n// `precision highp float;`.\n\n// Small surface accuracy for the sphere-tracing loop.\nconst float SDF_EPSILON = 0.0005;\n// Fallback hard clip distance for the ray march (the camera far is preferred).\nconst float MAX_DIST = 1000.0;\n\n// \u2500\u2500 IQ rotation helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n// Rotate around an arbitrary normalized axis.\nmat3 rotationAxisAngle(vec3 axis, float angle) {\n    float s = sin(angle);\n    float c = cos(angle);\n    float oc = 1.0 - c;\n    return mat3(\n        oc * axis.x * axis.x + c,\n        oc * axis.x * axis.y - axis.z * s,\n        oc * axis.x * axis.z + axis.y * s,\n        oc * axis.x * axis.y + axis.z * s,\n        oc * axis.y * axis.y + c,\n        oc * axis.y * axis.z - axis.x * s,\n        oc * axis.x * axis.z - axis.y * s,\n        oc * axis.y * axis.z + axis.x * s,\n        oc * axis.z * axis.z + c\n    );\n}\n\n// Rotate around the X axis.\nmat3 rotationX(float angle) {\n    float s = sin(angle);\n    float c = cos(angle);\n    return mat3(\n        1.0, 0.0, 0.0,\n        0.0, c, -s,\n        0.0, s, c\n    );\n}\n\n// Rotate around the Y axis.\nmat3 rotationY(float angle) {\n    float s = sin(angle);\n    float c = cos(angle);\n    return mat3(\n        c, 0.0, s,\n        0.0, 1.0, 0.0,\n        -s, 0.0, c\n    );\n}\n\n// Rotate around the Z axis.\nmat3 rotationZ(float angle) {\n    float s = sin(angle);\n    float c = cos(angle);\n    return mat3(\n        c, -s, 0.0,\n        s, c, 0.0,\n        0.0, 0.0, 1.0\n    );\n}", "primitives": "// SDF primitives \u2014 ported from inigo quilez's signed-distance reference.\n//\n// Each primitive takes the point p in the primitive's LOCAL space (the\n// transform is applied by the caller before invoking these functions).\n// This file is concatenated with sdf_common.glsl; it must not contain main(),\n// nor a `#version`/`precision` directive (the host shader supplies them).\n//\n// Axis conventions (IQ reference):\n//   \u00b7 cylinders/cones are aligned with the +Y axis (radius in XZ, height in Y)\n//   \u00b7 a torus lies in the XZ plane (major ring in XZ, tube in Y)\n\n// \u2500\u2500 Spheres \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n// p: local point, r: radius\nfloat sdSphere(vec3 p, float r) {\n    return length(p) - r;\n}\n\n// p: local point, r: per-axis half radii\nfloat sdEllipsoid(vec3 p, vec3 r) {\n    float k0 = length(p / r);\n    float k1 = length(p / (r * r));\n    return k0 * (k0 - 1.0) / k1;\n}\n\n// \u2500\u2500 Boxes \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n// p: local point, b: axis-aligned half extents\nfloat sdBox(vec3 p, vec3 b) {\n    vec3 q = abs(p) - b;\n    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);\n}\n\n// p: local point, b: axis-aligned half extents, r: corner rounding radius\nfloat sdRoundBox(vec3 p, vec3 b, float r) {\n    vec3 q = abs(p) - b + vec3(r);\n    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;\n}\n\n// \u2500\u2500 Planes / lines \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n// Plane with unit normal n. IQ form: distance = dot(p, n) + h, so the plane\n// satisfies dot(p, n) = -h.\nfloat sdPlane(vec3 p, vec3 n, float h) {\n    return dot(p, n) + h;\n}\n\n// Infinite line (zero radius) segment between a and b.\nfloat sdSegment(vec3 p, vec3 a, vec3 b) {\n    vec3 pa = p - a;\n    vec3 ba = b - a;\n    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);\n    return length(pa - ba * h);\n}\n\n// Two-point capsule with hemispherical caps (radii ra, rb).\nfloat sdCapsule(vec3 p, vec3 a, vec3 b, float ra, float rb) {\n    vec3 pa = p - a;\n    vec3 ba = b - a;\n    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);\n    return length(pa - ba * h) - mix(ra, rb, h);\n}\n\n// \u2500\u2500 Cylinders / cones \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n// Infinite cylinder along +Y, radius r.\nfloat sdCylinder(vec3 p, float r) {\n    return length(p.xz) - r;\n}\n\n// Capped cylinder along +Y with half-height h and radius r.\nfloat sdCappedCylinder(vec3 p, float h, float r) {\n    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);\n    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));\n}\n\n// Infinite cone around +Y with opening angle a (radians), apex at the origin.\nfloat sdCone(vec3 p, float a) {\n    return length(p.xz) - p.y * tan(a);\n}\n\n// Capped cone along +Y: apex radius r1 at the bottom, base radius r2 at the\n// top, and half-height h. IQ canonical form.\nfloat sdCappedCone(vec3 p, float h, float r1, float r2) {\n    vec2 q = vec2(length(p.xz), p.y);\n    vec2 k1 = vec2(r2, h);\n    vec2 k2 = vec2(r2 - r1, 2.0 * h);\n    vec2 ca = vec2(q.x - min(q.x, (q.y < 0.0) ? r1 : r2), abs(q.y) - h);\n    vec2 cb = q - k1 + k2 * clamp(dot(k1 - q, k2) / dot(k2, k2), 0.0, 1.0);\n    float s = (cb.x < 0.0 && ca.y < 0.0) ? -1.0 : 1.0;\n    return s * sqrt(min(dot(ca, ca), dot(cb, cb)));\n}\n\n// \u2500\u2500 Torus \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n// Torus in the XZ plane: major radius t.x, minor (tube) radius t.y.\nfloat sdTorus(vec3 p, vec2 t) {\n    vec2 q = vec2(length(p.xz) - t.x, p.y);\n    return length(q) - t.y;\n}\n\n// \u2500\u2500 Partial disk / regular polygon \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\nconst float SDF_PI = 3.141592653589793;\n\n// Capped sector (partial disk): a slab of half-height h and radius r, swept\n// over `angle` radians, symmetric about the local +Z axis in the XZ plane\n// (Y up).  This matches THREE.CylinderGeometry(thetaStart=-angle/2,\n// thetaLength=angle), whose theta=0 vertex sits on +Z.  Use for 0 < angle < 2\u03c0;\n// the full disk (2\u03c0) is a plain capped cylinder.\nfloat sdPartialDisk(vec3 p, float h, float r, float angle) {\n    float a = 0.5 * angle;\n    vec2 c = vec2(sin(a), cos(a));\n    vec2 q = p.xz;                       // q.x = p.x, q.y = p.z (IQ pie on +Y)\n    q.x = abs(q.x);\n    float l = length(q) - r;\n    float m = length(q - c * clamp(dot(q, c), 0.0, r));\n    float pie = max(l, sign(c.y * q.x - c.x * q.y) * m);\n    return max(abs(p.y) - h, pie);\n}\n\n// Regular n-gon slab: a slab of half-height h, circumradius r, n sides, with a\n// vertex on +Z (matching THREE.CylinderGeometry(radialSegments=n)).\nfloat sdRegularPolygon(vec3 p, float h, float r, float n) {\n    float an = SDF_PI / n;\n    vec2 acs = vec2(cos(an), sin(an));\n    // IQ's folding places the vertex on +X; rotate the XZ frame by -90\u00b0 so the\n    // vertex lands on +Z.  Only the vertex axis is reflected (valid for all n).\n    vec2 q = vec2(p.z, -p.x);\n    q.y = abs(q.y);\n    float bn = mod(atan(q.y, q.x), 2.0 * an) - an;\n    q = length(q) * vec2(cos(bn), abs(sin(bn)));\n    q -= r * acs;\n    q.y += clamp(-q.y, 0.0, r * acs.y);\n    float d = length(q) * sign(q.x);\n    return max(abs(p.y) - h, d);\n}", "combinators": "// SDF Boolean/combinator helpers \u2014 ported from inigo quilez's reference.\n//\n// Hard combinators fold two scalar distances with exact sign preservation:\n//   \u00b7 opUnion        \u2192 min(a, b)              (inside either)\n//   \u00b7 opIntersect    \u2192 max(a, b)              (inside both)\n//   \u00b7 opSubtract     \u2192 max(a, -b)             (inside a, not inside b)\n//\n// Smooth combinators return vec2(d, h) where d is the blended distance and h\n// is the blend/material factor IQ uses to drive material-ID mixing.\n//\n// This file is concatenated with sdf_common.glsl; it must not contain main(),\n// nor a `#version`/`precision` directive (the host shader supplies them).\n\n// \u2500\u2500 Hard combinators \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\nfloat opUnion(float d1, float d2) {\n    return min(d1, d2);\n}\n\nfloat opSubtract(float d1, float d2) {\n    return max(d1, -d2);\n}\n\nfloat opIntersect(float d1, float d2) {\n    return max(d1, d2);\n}\n\nfloat opXor(float d1, float d2) {\n    // Symmetric difference: inside exactly one of the two, outside both.\n    return max(min(d1, d2), -max(d1, d2));\n}\n\n// \u2500\u2500 Smooth combinators (vec2: x = distance, y = blend factor) \u2500\u2500\n\nvec2 opSmoothUnion(float d1, float d2, float k) {\n    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);\n    return vec2(mix(d2, d1, h) - k * h * (1.0 - h), h);\n}\n\nvec2 opSmoothSubtract(float d1, float d2, float k) {\n    float h = clamp(0.5 - 0.5 * (d2 + d1) / k, 0.0, 1.0);\n    return vec2(mix(d2, -d1, h) + k * h * (1.0 - h), h);\n}\n\nvec2 opSmoothIntersect(float d1, float d2, float k) {\n    float h = clamp(0.5 - 0.5 * (d2 - d1) / k, 0.0, 1.0);\n    return vec2(mix(d2, d1, h) + k * h * (1.0 - h), h);\n}", "proxy": "// Per-object SDF proxy fragment body \u2014 the final stage concatenated after\n// `sdf_common`, `primitives`, `combinators`, the light preamble, and the\n// host-injected single-object `float map(vec3 p)`. Marches a ray through the\n// proxy box in local space, shades the surface with the shared directional\n// lighting model, and writes `gl_FragDepth` so the standard depth buffer\n// occludes it against meshes and other SDF proxies.\n//\n// Uses three.js ShaderMaterial GLSL3 conventions: a declared `out vec4`\n// fragment output (no `gl_FragColor`) and no `#version`/`precision` directive\n// (the host shader prepends them). Exactly one `main()`.\n\nuniform vec4 uMaterial[MAX_GROUP_MEMBERS];\nuniform float uOpacity;\nuniform int uMaxSteps;\nuniform float uSoftShadows;\nuniform float uAntialias;\nuniform vec3 uBoundHalf;\nuniform mat4 uModelMatrix;\nuniform mat4 uProjectionMatrix;\nuniform vec3 uHover;\n\nin vec3 vLocalPos;\nflat in vec3 vCameraLocal;\n\nout vec4 fragColor;\n\n// \u2500\u2500 Gradient normal (tetrahedral) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\nvec3 calcNormal(vec3 p) {\n    const float e = 0.001;\n    vec2 k = vec2(1.0, -1.0);\n    return normalize(\n        k.xyy * map(p + k.xyy * e).x +\n        k.yyx * map(p + k.yyx * e).x +\n        k.yxy * map(p + k.yxy * e).x +\n        k.xxx * map(p + k.xxx * e).x\n    );\n}\n\n// \u2500\u2500 Soft self-shadow \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\nfloat softShadow(vec3 ro, vec3 rd) {\n    float res = 1.0;\n    float t = 0.02;\n    for (int i = 0; i < 32; i++) {\n        float h = map(ro + rd * t).x;\n        res = min(res, 8.0 * h / t);\n        t += clamp(h, 0.02, 0.5);\n        if (h < 0.001 || t > 20.0) break;\n    }\n    return clamp(res, 0.0, 1.0);\n}\n\n// \u2500\u2500 IQ-style shading (single object) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\nvec3 shade(vec3 p, vec3 n, vec3 ro, vec4 mat) {\n    vec3 col = mat.rgb * uAmbientColor;\n    for (int i = 0; i < MAX_LIGHTS; i++) {\n        if (i >= uLightCount) break;\n        vec3 L = normalize(uLightDir[i]);\n        float dif = max(dot(n, L), 0.0);\n        float sh = 1.0;\n        if (uSoftShadows > 0.5) {\n            sh = softShadow(p + n * 0.01, L);\n        }\n        col += mat.rgb * uLightColor[i] * dif * sh;\n    }\n    col *= (0.5 + 0.5 * n.y);\n\n    // Fog for depth cueing (matches the fullscreen viewer's look).\n    float dist = length(p - ro);\n    float fog = 1.0 - exp(-0.05 * dist);\n    vec3 bg = vec3(0.10, 0.10, 0.18);\n    col = mix(col, bg, fog);\n\n    // Emissive-style hover glow (black = none), set by the interaction layer.\n    col += uHover;\n\n    return col;\n}\n\nvoid main() {\n    vec3 ro = vCameraLocal;\n    vec3 rd = normalize(vLocalPos - ro);\n\n    // Ray-box intersection with the local-space AABB [-uBoundHalf, +uBoundHalf],\n    // so the march is bounded by the proxy volume (not the whole viewport).\n    vec3 invDir = 1.0 / rd;\n    vec3 t0 = (-uBoundHalf - ro) * invDir;\n    vec3 t1 = (uBoundHalf - ro) * invDir;\n    vec3 tmin = min(t0, t1);\n    vec3 tmax = max(t0, t1);\n    float tNear = max(max(tmin.x, tmin.y), tmin.z);\n    float tFar = min(min(tmax.x, tmax.y), tmax.z);\n    tNear = max(tNear, 0.0);\n    if (tFar <= tNear) discard;\n\n    float t = tNear;\n    float res = tFar;   // closest signed distance the ray passes the surface by\n    float tRes = tNear; // march distance at that closest approach (edge shading)\n    bool hit = false;\n    float m = 0.0;\n    for (int i = 0; i < MAX_STEPS; i++) {\n        if (i >= uMaxSteps) break;\n        vec3 p = ro + rd * t;\n        vec2 dm = map(p);\n        if (dm.x < res) {\n            res = dm.x;\n            tRes = t;\n        }\n        if (dm.x < SDF_EPSILON) {\n            hit = true;\n            m = dm.y;\n            break;\n        }\n        t += dm.x;\n        if (t > tFar) break;\n    }\n    // One-pixel silhouette edge scale: the local-space pixel footprint, taken\n    // from the smooth interpolated proxy-face position `vLocalPos`. Do NOT use\n    // `fwidth`/`dFdx` of the min-distance (`t`/`tRes`): the argmin's position\n    // jumps across feature boundaries, producing spurious diagonal/radial lines.\n    float pixelSize = max(length(dFdx(vLocalPos)), length(dFdy(vLocalPos)));\n    float aa = 1.0 - smoothstep(0.0, max(pixelSize, 1e-6), res);\n    if (!hit) {\n        if (uAntialias < 0.5 || aa < 0.001) discard;\n        // Near-miss: shade the closest-approach point so the faded edge matches\n        // the lit surface (no bright halo), then fade it out over ~1px.\n        vec3 p0 = ro + rd * tRes;\n        vec3 n0 = calcNormal(p0);\n        float m0 = map(p0).y;\n        vec4 mat0 = uMaterial[int(clamp(m0, 0.0, float(MAX_GROUP_MEMBERS - 1)))];\n        vec3 col0 = shade(p0, n0, ro, mat0);\n        fragColor = vec4(col0, mat0.a * uOpacity * aa);\n        gl_FragDepth = 1.0; // far depth: the edge never occludes anything\n        return;\n    }\n\n    vec3 p = ro + rd * t;\n    vec3 n = calcNormal(p);\n    vec4 mat = uMaterial[int(clamp(m, 0.0, float(MAX_GROUP_MEMBERS - 1)))];\n    vec3 col = shade(p, n, ro, mat);\n\n    // Write the hit's clip-space depth so occlusion against meshes and other\n    // SDF proxies is handled by the standard depth buffer. three.js's WebGL2\n    // depth range is [0, 1] (NDC z = clip.z / clip.w remapped).\n    vec4 clip = uProjectionMatrix * viewMatrix * uModelMatrix * vec4(p, 1.0);\n    float ndc = clip.z / clip.w;\n    gl_FragDepth = ndc * 0.5 + 0.5;\n\n    fragColor = vec4(col, mat.a * uOpacity);\n}\n"};

function sendLog() {}
function sendEvent() {}

// Tanga Viewer — Pure style-diff helper (no DOM, no THREE).
// Decides whether a style change requires rebuilding an entity's mesh rather
// than updating it in place.  Only `color` and `opacity` are cheaply
// applicable in place; any other style field change requires a rebuild so the
// per-kind renderer re-reads every style parameter.

const CHEAP_STYLE_FIELDS = new Set(['color', 'opacity']);

/**
 * Return true when the style of *ent* differs from *prev* in any field other
 * than the cheap, in-place-updatable fields (`color`, `opacity`).
 *
 * `ent.style` and `prev.style` are the resolved style dicts emitted by the
 * serializer; values may be nested objects (e.g. dash patterns, texture
 * labels), so the comparison is a deep JSON equality.
 *
 * @param {object|undefined|null} ent   Merged entity dict (with `.style`).
 * @param {object|undefined|null} prev  Previously applied entity dict.
 * @returns {boolean}
 */
function styleNeedsRebuild(ent, prev) {
    if (!ent || !prev) return false;
    const newStyle = ent.style || {};
    const oldStyle = prev.style || {};
    const keys = new Set([...Object.keys(newStyle), ...Object.keys(oldStyle)]);
    for (const key of keys) {
        if (CHEAP_STYLE_FIELDS.has(key)) continue;
        const a = JSON.stringify(newStyle[key] ?? null);
        const b = JSON.stringify(oldStyle[key] ?? null);
        if (a !== b) return true;
    }
    return false;
}

// Shared utilities for Tanga entity/operator renderers.
// Phase 5: Used by per-entity modules and the factory dispatcher.

/**
 * Create a MeshPhongMaterial with sensible defaults for Tanga entities.
 *
 * Critical: depthWrite is disabled for translucent materials (opacity < 0.99)
 * to prevent depth-sorting artifacts.
 */
function makeMaterial(color, opacity = 1.0, doubleSided = false) {
    const c = typeof color === 'string' ? new THREE.Color(color) : color;
    return new THREE.MeshPhongMaterial({
        color: c,
        opacity,
        transparent: opacity < 1.0,
        depthWrite: opacity >= 0.99,
        side: doubleSided ? THREE.DoubleSide : THREE.FrontSide,
    });
}

// ── Fat lines (screen-space width) ──────────────────────────
//
// THREE.Line + LineBasicMaterial cannot vary their width: WebGL caps line
// width at 1px on most platforms.  For axes/grid overlays we instead use
// three.js `Line2` fat lines, whose `linewidth` is expressed in
// screen-space pixels (worldUnits: false) and therefore stays constant
// on screen regardless of zoom.

function _lineResolution() {
    const pr = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;
    const w = (typeof window !== 'undefined' ? window.innerWidth : 1) * pr;
    const h = (typeof window !== 'undefined' ? window.innerHeight : 1) * pr;
    return new THREE.Vector2(Math.max(1, w), Math.max(1, h));
}

/**
 * Create a LineMaterial for a three.js `Line2` fat line.
 *
 * @param {string|THREE.Color} color
 * @param {number} opacity - 0..1
 * @param {number} lineWidth - line width in screen-space pixels
 * @returns {THREE.ShaderMaterial}
 */
const _lineMaterials = new Set();

function makeLineMaterial(color, opacity = 1.0, lineWidth = 1.0, options = {}) {
    const c = typeof color === 'string' ? new THREE.Color(color) : color;
    const material = new LineMaterial({
        color: c,
        linewidth: Math.max(0.1, lineWidth),
        worldUnits: false,
        transparent: opacity < 1.0,
        opacity,
        depthWrite: opacity >= 0.99,
        resolution: _lineResolution(),
        vertexColors: !!options.vertexColors,
    });
    if (options.dashed) {
        material.dashed = true;
        material.dashSize = options.dashSize ?? 4;
        material.gapSize = options.gapSize ?? 2;
        material.dashScale = options.dashScale ?? 1;
    }
    _lineMaterials.add(material);
    return material;
}

/**
 * Recompute the screen resolution for every registered LineMaterial.
 * Called on window resize / screenshot capture so screen-space line widths
 * stay correct when the drawing buffer size changes.
 */
function updateLineResolutions() {
    const res = _lineResolution();
    for (const m of _lineMaterials) {
        m.resolution.copy(res);
    }
}

function _flattenPoints(points) {
    const out = [];
    for (const p of points) out.push(p.x, p.y, p.z);
    return out;
}

function _flattenSegments(segments) {
    const out = [];
    for (const [a, b] of segments) out.push(a.x, a.y, a.z, b.x, b.y, b.z);
    return out;
}

/**
 * Create a `Line2` fat line through the given points.
 *
 * @param {THREE.Vector3[]} points
 * @param {string|THREE.Color} color
 * @param {number} opacity
 * @param {number} lineWidth - screen-space pixel width
 * @returns {Line2}
 */
function makeFatLine(points, color, opacity = 1.0, lineWidth = 1.0) {
    const material = makeLineMaterial(color, opacity, lineWidth);
    const geometry = new LineGeometry();
    geometry.setPositions(_flattenPoints(points));
    return new Line2(geometry, material);
}

/**
 * Create a `Line2` fat line reusing an existing LineMaterial.
 *
 * @param {THREE.Vector3[]} points
 * @param {THREE.ShaderMaterial} material - a LineMaterial
 * @returns {Line2}
 */
function makeFatLineWithMaterial(points, material) {
    const geometry = new LineGeometry();
    geometry.setPositions(_flattenPoints(points));
    return new Line2(geometry, material);
}

/**
 * Create a `LineSegments2` fat line from independent start/end segment pairs.
 *
 * @param {[THREE.Vector3, THREE.Vector3][]} segments
 * @param {string|THREE.Color} color
 * @param {number} opacity
 * @param {number} lineWidth - screen-space pixel width
 * @returns {LineSegments2}
 */
function _finalizeSegmentsLine(geometry, material) {
    const line = new LineSegments2(geometry, material);
    if (material.dashed) line.computeLineDistances();
    return line;
}

function makeFatSegments(segments, color, opacity = 1.0, lineWidth = 1.0) {
    const material = makeLineMaterial(color, opacity, lineWidth);
    return makeFatSegmentsWithMaterial(segments, material);
}

/**
 * Create a `LineSegments2` fat line reusing an existing LineMaterial.
 *
 * @param {[THREE.Vector3, THREE.Vector3][]} segments
 * @param {THREE.ShaderMaterial} material - a LineMaterial
 * @returns {LineSegments2}
 */
function makeFatSegmentsWithMaterial(segments, material) {
    const geometry = new LineSegmentsGeometry();
    geometry.setPositions(_flattenSegments(segments));
    return _finalizeSegmentsLine(geometry, material);
}

/**
 * Create a `LineSegments2` fat line from flat [x,y,z, x,y,z, ...] pair data.
 *
 * @param {number[]|Float32Array} flatPositions - consecutive start/end pairs
 * @param {string|THREE.Color} color
 * @param {number} opacity
 * @param {number} lineWidth - screen-space pixel width
 * @returns {LineSegments2}
 */
function makeFatSegmentsFromFlat(flatPositions, color, opacity = 1.0, lineWidth = 1.0) {
    const material = makeLineMaterial(color, opacity, lineWidth);
    const geometry = new LineSegmentsGeometry();
    geometry.setPositions(flatPositions);
    return _finalizeSegmentsLine(geometry, material);
}

/**
 * Create a `LineSegments2` fat line from flat positions reusing a material.
 *
 * @param {number[]|Float32Array} flatPositions - consecutive start/end pairs
 * @param {THREE.ShaderMaterial} material - a LineMaterial
 * @returns {LineSegments2}
 */
function makeFatSegmentsFromFlatWithMaterial(flatPositions, material) {
    const geometry = new LineSegmentsGeometry();
    geometry.setPositions(flatPositions);
    return _finalizeSegmentsLine(geometry, material);
}

/**
 * Create a `LineSegments2` fat line with per-segment start/end colors.
 *
 * @param {number[]|Float32Array} flatPositions - consecutive start/end pairs
 * @param {number[]|Float32Array} flatColors - flat [r,g,b, r,g,b, ...] per vertex
 * @param {number} opacity
 * @param {number} lineWidth - screen-space pixel width
 * @returns {LineSegments2}
 */
function makeFatSegmentsColored(flatPositions, flatColors, opacity = 1.0, lineWidth = 1.0) {
    const material = makeLineMaterial('#ffffff', opacity, lineWidth, { vertexColors: true });
    const geometry = new LineSegmentsGeometry();
    geometry.setPositions(flatPositions);
    geometry.setColors(flatColors);
    return _finalizeSegmentsLine(geometry, material);
}

/**
 * Create a quaternion that rotates the Y-axis to point along the given direction.
 * Used to orient cylinders (lines), cones (direction arrows), and planes.
 */
function rotationFromDirection(dx, dy, dz) {
    const dir = new THREE.Vector3(dx, dy, dz).normalize();
    const up = new THREE.Vector3(0, 1, 0);
    return new THREE.Quaternion().setFromUnitVectors(up, dir);
}

/**
 * Create a quaternion that rotates the Z-axis to point along the given normal.
 * Used to orient toruses (circles) and planes.
 */
function rotationFromNormal(nx, ny, nz) {
    const normal = new THREE.Vector3(nx, ny, nz).normalize();
    return new THREE.Quaternion().setFromUnitVectors(
        new THREE.Vector3(0, 0, 1), normal
    );
}

/**
 * Tag a mesh with entity metadata for click detection and debugging.
 */
function tagEntity(mesh, ent) {
    // Preserve any renderer-specific userData (e.g. an SDF proxy's `sdfKind`)
    // while tagging the standard entity id/kind/data.
    const prev = mesh.userData || {};
    mesh.userData = { ...prev, entityId: ent.id, kind: ent.kind, data: ent };
}

/**
 * Parse a color from an entity dict, using the style object if available.
 * Falls back to flat ent.color, then the provided fallback.
 */
function parseColor(ent, fallback = '#ffffff') {
    if (ent.color) return ent.color;
    return fallback;
}

/**
 * Read a rendering parameter, preferring ent.style.* (Phase 4c) over flat ent.*.
 *
 * @param {object} ent - The entity JSON dict.
 * @param {string} key - The camelCase key (e.g. "size", "tubeRadius").
 * @param {*} fallback - Default value if neither source has the key.
 * @returns {*}
 */
function styleParam(ent, key, fallback) {
    if (ent.style && ent.style[key] !== undefined) return ent.style[key];
    if (ent[key] !== undefined) return ent[key];
    return fallback;
}

/**
 * Numeric equality within a small absolute tolerance.
 */
function approxEqual(a, b, eps = 1e-9) {
    return Math.abs(a - b) < eps;
}

/**
 * Apply the common, non-structural style fields (opacity, color, scale) to a
 * mesh and its children.  Used by the shared update dispatcher and by
 * per-entity updaters so the mutations are defined in one place.
 */
function applyStyleUpdate(mesh, ent) {
    const opacity = styleParam(ent, 'opacity', undefined);
    if (opacity !== undefined) {
        mesh.traverse((child) => {
            if (child.material && child.material.opacity !== undefined) {
                child.material.opacity = opacity;
                child.material.transparent = opacity < 1.0;
                child.material.depthWrite = opacity >= 0.99;
                child.material.needsUpdate = true;
            }
        });
    }

    const color = styleParam(ent, 'color', null);
    if (color) {
        const c = new THREE.Color(color);
        mesh.traverse((child) => {
            if (child.material && child.material.color) {
                child.material.color.copy(c);
            }
        });
    }

    if (ent.scale) {
        mesh.scale.set(ent.scale[0], ent.scale[1], ent.scale[2]);
    }
}

/**
 * Return true when an entity whose geometry derives directly from its fields
 * must be rebuilt rather than updated in place.
 *
 * ``prev`` is the previously applied merged entity dict (may be undefined for
 * a brand-new entity; callers invoking this on an in-place path always have it).
 */
function entityRequiresRebuild(ent, prev) {
    if (ent.kind === 'PointPath') return true;
    // SDF proxies: only structural changes (tree/sdfKind) rebuild the shader;
    // member-transform changes (an SdfGroup) and style-only changes are applied
    // in place by updateSdfProxy (which also resizes the proxy box).
    if (ent.kind === 'sdf') {
        if (!prev) return false;
        if (ent.sdfKind !== prev.sdfKind) return true;
        if (JSON.stringify(ent.tree) !== JSON.stringify(prev.tree)) return true;
        return false;
    }
    // Axes/grids are drawn fresh (axis line + CSS2D value labels; many grid
    // segments) and their geometry derives from many fields, so rebuild whenever
    // their content changes — e.g. a live time axis whose ticks move each frame.
    if (ent.kind === 'Axis' || ent.kind === 'Axes2D' || ent.kind === 'Axes3D') return true;
    if (ent.kind === 'Grid') return true;
    if (ent.radius !== undefined && (!prev || !approxEqual(ent.radius, prev.radius))) return true;
    if (ent.alignCenter !== undefined && (!prev || !approxEqual(ent.alignCenter, prev.alignCenter))) return true;
    if (ent.extent !== undefined && (!prev || !approxEqual(ent.extent, prev.extent))) return true;
    if (ent.length !== undefined && (!prev || !approxEqual(ent.length, prev.length))) return true;
    if (ent.tubeRadius !== undefined && (!prev || !approxEqual(ent.tubeRadius, prev.tubeRadius))) return true;
    if (ent.angle !== undefined && (!prev || !approxEqual(ent.angle, prev.angle))) return true;
    if (ent.span_u !== undefined || ent.span_v !== undefined) {
        const a = JSON.stringify([ent.span_u ?? null, ent.span_v ?? null]);
        const b = JSON.stringify([prev?.span_u ?? null, prev?.span_v ?? null]);
        if (!prev || a !== b) return true;
    }
    if (ent.arrow !== undefined) {
        const a = JSON.stringify(ent.arrow ?? null);
        const b = JSON.stringify(prev?.arrow ?? null);
        if (!prev || a !== b) return true;
    }
    // ── Creation-only geometry fields ──────────────────────────────────────
    // These are read only by the per-kind create*() renderers and are never
    // re-applied by the generic in-place update path, so a change must rebuild
    // the mesh. (`rotation` is intentionally absent: it is applied in place by
    // updateEntityMesh for meshes that carry a top-level Euler triple, keeping
    // rotation-only animation updates rebuild-free.)
    for (const key of ['size', 'radii', 'normal', 'axis', 'startDirection', 'point', 'pointA', 'pointB', 'origin']) {
        if (ent[key] !== undefined &&
            (!prev || JSON.stringify(ent[key]) !== JSON.stringify(prev[key]))) {
            return true;
        }
    }
    for (const key of ['radiusU', 'radiusV', 'sides', 'discRadius', 'ringCount', 'maxRadius', 'pointSize']) {
        if (ent[key] !== undefined && (!prev || !approxEqual(ent[key], prev[key]))) {
            return true;
        }
    }
    // Motor nests its rotor/translator parameters; compare them structurally.
    if (ent.rotor !== undefined || ent.translator !== undefined) {
        if (!prev ||
            JSON.stringify(ent.rotor ?? null) !== JSON.stringify(prev.rotor ?? null) ||
            JSON.stringify(ent.translator ?? null) !== JSON.stringify(prev.translator ?? null)) {
            return true;
        }
    }
    if (ent.kind !== undefined && ent.kind !== prev?.kind) return true;
    // Any style field other than color/opacity must rebuild, so the per-kind
    // renderer re-reads every style parameter (size, thickness, wireframe,
    // dash patterns, texture labels, double-sided, …).
    if (styleNeedsRebuild(ent, prev)) return true;
    return false;
}

/**
 * Create a 3D arrow group (cylinder shaft + cone head) oriented along a direction.
 *
 * @param {THREE.Color|string} color
 * @param {number} opacity
 * @param {number[]} vec - Direction vector [x, y, z].
 * @param {number} length - Total arrow length.
 * @param {number[]} origin - Start point [x, y, z].
 * @returns {THREE.Group}
 */
function createArrow(color, opacity, vec, length, origin) {
    const g = new THREE.Group();
    const sl = length * 0.75, sr = 0.06;
    const hl = length * 0.25, hr = 0.15;
    const col = typeof color === 'string' ? new THREE.Color(color) : color;
    const shaft = new THREE.Mesh(
        new THREE.CylinderGeometry(sr, sr, sl, 8, 1),
        makeMaterial(col, opacity)
    );
    shaft.position.y = sl / 2;
    g.add(shaft);
    const head = new THREE.Mesh(
        new THREE.ConeGeometry(hr, hl, 8, 1),
        makeMaterial(col, opacity)
    );
    head.position.y = sl + hl / 2;
    g.add(head);
    const d = new THREE.Vector3(vec[0], vec[1], vec[2]).normalize();
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d)
    );
    g.position.set(origin[0], origin[1], origin[2]);
    return g;
}

/**
 * Build the shared rotor visualization (disc arc, outer torus, and axis line)
 * in local coordinates with the rotation axis along local +Z. Callers rotate
 * and position the returned group.
 */
function buildRotorVisual(color, opacity, lineWidth, angle, discRadius) {
    const col = typeof color === 'string' ? new THREE.Color(color) : color;
    const dr = discRadius;
    const absA = Math.abs(angle);
    const segs = Math.max(8, Math.ceil(absA / (Math.PI / 32)));
    const g = new THREE.Group();

    // Disc arc swept by the rotation angle
    g.add(
        new THREE.Mesh(
            new THREE.RingGeometry(dr * 0.15, dr, segs, 1, 0, absA),
            new THREE.MeshBasicMaterial({
                color: col,
                opacity: opacity * 0.8,
                transparent: true,
                side: THREE.DoubleSide,
                depthWrite: false,
            })
        )
    );

    // Outer torus (full circle)
    g.add(
        new THREE.Mesh(
            new THREE.TorusGeometry(dr, 0.03, 16, 64),
            makeMaterial(col, opacity * 0.5)
        )
    );

    // Axis line
    const al = dr * 1.6;
    g.add(
        makeFatLine(
            [new THREE.Vector3(0, 0, -al), new THREE.Vector3(0, 0, al)],
            col,
            opacity,
            lineWidth
        )
    );

    return g;
}

/**
 * Add a wireframe overlay to a parent mesh/group using ``WireframeGeometry``
 * and ``LineSegments`` (solid or dashed).
 *
 * @param {THREE.Mesh|THREE.Group} parent - The parent to attach the overlay to.
 * @param {THREE.BufferGeometry} geometry - The geometry whose edges to render.
 * @param {THREE.Color|string} color - Wireframe color.
 * @param {object|null} dashPattern - Dash config dict with ``dash_size``,
 *     ``gap_size``, ``scale``, or ``null`` for solid lines.
 */
function addWireframeOverlay(parent, geometry, color, dashPattern, opacity = 1.0) {
    const wireGeo = new THREE.WireframeGeometry(geometry);
    const flatPositions = wireGeo.attributes.position.array;
    const useDash = dashPattern && dashPattern.dash_size > 0;
    const material = makeLineMaterial(
        color,
        opacity,
        1.0,
        useDash
            ? {
                dashed: true,
                dashSize: dashPattern.dash_size,
                gapSize: dashPattern.gap_size,
                dashScale: dashPattern.scale || 1.0,
            }
            : {}
    );
    const lines = makeFatSegmentsFromFlatWithMaterial(flatPositions, material);
    parent.add(lines);
}

/**
 * Create a group of concentric expanding rings (for Dilator types).
 *
 * @param {THREE.Color|string} color
 * @param {number} opacity
 * @param {number} count - Number of rings.
 * @param {number} maxR - Max ring radius.
 * @param {number[]} origin - Center position [x, y, z].
 * @returns {THREE.Group}
 */
function createDilatorRings(color, opacity, count, maxR, origin) {
    const g = new THREE.Group();
    const minR = 0.3;
    const col = typeof color === 'string' ? new THREE.Color(color) : color;
    for (let i = 0; i < count; i++) {
        const t = count > 1 ? i / (count - 1) : 0.5;
        const r = minR + t * (maxR - minR);
        const torus = new THREE.Mesh(
            new THREE.TorusGeometry(r, 0.02, 8, 64),
            makeMaterial(col, opacity * (0.4 + 0.6 * t))
        );
        torus.rotation.x = i % 2 === 0 ? 0 : Math.PI / 2;
        g.add(torus);
    }
    g.position.set(origin[0], origin[1], origin[2]);
    return g;
}

// ── Texture Label Utilities ──────────────────────────────────

/**
 * Check whether a string contains $...$ (inline) or $$...$$ (display)
 * math delimiters.  Used to decide between plain-text and mixed
 * rendering modes.
 *
 * A single unpaired ``$`` is treated as plain text (no mixed mode).
 *
 * @param {string} text
 * @returns {boolean}
 */
function hasMathDelimiters(text) {
    // Must have at least one pair of $$ or $
    return /\$\$/.test(text) || /\$[^$]+\$/.test(text);
}

/**
 * Render text (plain or with ``$...$`` / ``$$...$$`` KaTeX delimiters)
 * onto a canvas via a DOM element + ``html2canvas`` capture.
 *
 * @param {CanvasRenderingContext2D} ctx - Target canvas 2D context.
 * @param {string} text - Text with optional ``$`` / ``$$`` KaTeX delimiters.
 * @param {number} width - Target canvas width.
 * @param {number} height - Target canvas height.
 * @param {number} fontSize - Font size in px for plain text portions.
 * @param {string} color - CSS text color.
 * @returns {Promise<void>}
 */
async function renderToCanvas(ctx, text, width, height, fontSize, color) {
    if (typeof html2canvas === 'undefined') {
        throw new Error('html2canvas not available');
    }

    const div = document.createElement('div');
    div.style.position = 'absolute';
    div.style.left = '0px';
    div.style.top = '0px';
    div.style.width = width + 'px';
    div.style.height = height + 'px';
    div.style.display = 'flex';
    div.style.flexDirection = 'column';
    div.style.alignItems = 'center';
    div.style.justifyContent = 'center';
    div.style.color = color;
    div.style.fontFamily = 'sans-serif';
    div.style.fontSize = fontSize + 'px';
    div.style.lineHeight = '1.5';
    div.style.padding = '20px';
    div.style.boxSizing = 'border-box';
    div.style.background = 'transparent';
    div.style.overflow = 'hidden';
    div.innerHTML = text;

    document.body.appendChild(div);

    try {
        if (typeof renderMathInElement !== 'undefined') {
            renderMathInElement(div, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        }

        const capture = await html2canvas(div, {
            backgroundColor: null,
            scale: 1,
            width: width,
            height: height,
        });
        ctx.drawImage(capture, 0, 0);
    } finally {
        document.body.removeChild(div);
    }
}

/**
 * Render plain text centered on the canvas.
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {string} text
 * @param {number} width
 * @param {number} height
 * @param {number} fontSize
 * @param {string} color
 */
function drawPlainText(ctx, text, width, height, fontSize, color) {
    ctx.fillStyle = color;
    ctx.font = `${fontSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, width / 2, height / 2);
}

/**
 * Create a THREE.CanvasTexture from a label string and texture label style.
 *
 * Two modes:
 * - Text contains ``$...$`` / ``$$...$$`` delimiters: rendered via DOM +
 *   ``renderMathInElement`` + ``html2canvas`` capture.
 * - Plain text: drawn directly on canvas with ``ctx.fillText()``.
 *
 * Returns ``null`` if text is falsy or rendering fails.
 *
 * @param {string|null|undefined} text - The label content.
 * @param {object} style - TextureLabelStyle dict from the entity's style.
 *        Expected keys: repeat_u, repeat_v, offset_u, offset_v,
 *        background, resolution, color, font_size.
 * @returns {Promise<THREE.CanvasTexture|null>}
 */
async function createTextureLabel(text, style) {
    if (!text) return null;

    const color = style.color || '#000000';
    const s = style.scale || 1.0;
    const a = style.aspect || 1.0;
    const repeatU = style.repeat_u || 1;
    const repeatV = style.repeat_v || 1;

    // Cell size: each tile gets contentW×contentH pixels.
    // Larger resolution = sharper, larger scale = larger text.
    const baseW = style.resolution || 512;
    const contentW = Math.floor(baseW / repeatU);
    const contentH = Math.floor(baseW / repeatV / 2);

    // Scale/aspect applied to font size, not canvas size.
    // scale=2 → text is 2× larger, aspect=0.5 → half as tall.
    const scaledFontSize = Math.round((style.font_size || 48) * s);

    const canvas = document.createElement('canvas');
    canvas.width = contentW;
    canvas.height = contentH;
    const ctx = canvas.getContext('2d');

    // Background fill
    const bg = (style.background && style.background !== 'transparent')
        ? style.background
        : '#ffffff';
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, contentW, contentH);

    // Apply aspect as vertical canvas scale so content is compressed
    // taller or shorter relative to the cell height.
    ctx.save();
    if (a !== 1.0) {
        ctx.translate(0, contentH * (1 - a) / 2);
        ctx.scale(1, a);
    }

    try {
        if (hasMathDelimiters(text)) {
            if (typeof html2canvas === 'undefined') {
                // Math delimiters are present but html2canvas (which rasterizes
                // the KaTeX DOM into the canvas) is unavailable.  Fall back to
                // drawing the raw source text so the label is not silently
                // dropped — plain text renders without html2canvas.
                drawPlainText(ctx, text, contentW, contentH, scaledFontSize, color);
            } else {
                await renderToCanvas(ctx, text, contentW, contentH, scaledFontSize, color);
            }
        } else {
            drawPlainText(ctx, text, contentW, contentH, scaledFontSize, color);
        }
    } catch (err) {
        console.warn('createTextureLabel: rendering failed', err);
        sendLog('warn', 'createTextureLabel: rendering failed', { source: 'utils.js', data: { error: String(err) } });
        ctx.restore();
        return null;
    }
    ctx.restore();

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;

    if (repeatU > 1 || repeatV > 1) {
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(repeatU, repeatV);
    }

    const offsetU = style.offset_u;
    const offsetV = style.offset_v;
    if (offsetU || offsetV) {
        texture.offset.set(offsetU || 0, offsetV || 0);
    }

    return texture;
}

// Point / HPoint renderer — renders as a small sphere.
// Phase 5: Per-entity module, reads from ent.style.* via styleParam().

function createPoint(ent) {
    const color = parseColor(ent, '#ff4444');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const size = styleParam(ent, 'size', 0.08);
    const pos = ent.position || [0, 0, 0];

    const geometry = new THREE.SphereGeometry(size, 16, 16);
    const material = makeMaterial(color, opacity);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(pos[0], pos[1], pos[2]);
    tagEntity(mesh, ent);
    return mesh;
}

// CrossHairPointStyle renderer — renders a 3D crosshair (three orthogonal cylinders)
// instead of a sphere.  Phase 8b: extended style example.

function createCrossHairPoint(ent) {
    const color = parseColor(ent, '#ff4444');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const size = styleParam(ent, 'size', 0.3);
    const armThickness = styleParam(ent, 'arm_thickness', size * 0.15);
    const pos = ent.position || [0, 0, 0];

    const group = new THREE.Group();
    const material = makeMaterial(color, opacity);

    // Three orthogonal arms (X, Y, Z)
    const directions = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ];

    for (const [dx, dy, dz] of directions) {
        // Cylinder centered at origin, extending ±size along direction
        const cylGeo = new THREE.CylinderGeometry(armThickness, armThickness, size * 2, 6, 1);
        const cyl = new THREE.Mesh(cylGeo, material);

        // Orient cylinder along direction
        const dir = new THREE.Vector3(dx, dy, dz).normalize();
        const quat = new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 1, 0), dir
        );
        cyl.setRotationFromQuaternion(quat);

        group.add(cyl);
    }

    group.position.set(pos[0], pos[1], pos[2]);
    tagEntity(group, ent);
    return group;
}

// Direction renderer — rendered as a 3D arrow (cylinder shaft + cone head).
// Phase 5: Per-entity module.

function createDirection(ent) {
    const color = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const vec = ent.vector || [0, 0, 1];
    const length = styleParam(ent, 'length', 2.0);
    const origin = ent.origin || [0, 0, 0];

    const group = new THREE.Group();

    // Arrow shaft
    const shaftLength = length * 0.75;
    const shaftRadius = 0.04;
    const shaftGeo = new THREE.CylinderGeometry(shaftRadius, shaftRadius, shaftLength, 8, 1);
    const shaftMat = makeMaterial(color, opacity);
    const shaft = new THREE.Mesh(shaftGeo, shaftMat);
    shaft.position.y = shaftLength / 2;
    group.add(shaft);

    // Arrow head
    const headLength = length * 0.25;
    const headRadius = 0.10;
    const headGeo = new THREE.ConeGeometry(headRadius, headLength, 8, 1);
    const headMat = makeMaterial(color, opacity);
    const head = new THREE.Mesh(headGeo, headMat);
    head.position.y = shaftLength + headLength / 2;
    group.add(head);

    group.setRotationFromQuaternion(rotationFromDirection(vec[0], vec[1], vec[2]));
    group.position.set(origin[0], origin[1], origin[2]);

    tagEntity(group, ent);
    return group;
}

function updateDirection(mesh, ent, prev) {
    const vec = ent.vector || prev?.vector || [0, 0, 1];
    const origin = ent.origin || prev?.origin || [0, 0, 0];

    mesh.setRotationFromQuaternion(rotationFromDirection(vec[0], vec[1], vec[2]));
    mesh.position.set(origin[0], origin[1], origin[2]);

    applyStyleUpdate(mesh, ent);

    if (ent.length !== undefined && prev && !approxEqual(ent.length, prev.length)) return false;
    return true;
}

// Line renderer — draws a straight segment from `origin` to
// `origin + normalize(direction) * length`.
//
// `length` is a content field: `0` means "infinite line → use the style's
// default length".  Rendering dispatches on the style type:
//   - `LineStyle` (default) → three.js `Line2` fat line; `thickness` is a
//     screen-space pixel width.
//   - `CylinderLineStyle`   → solid `CylinderGeometry`; `thickness` is the
//     cylinder radius in world units.
// Phase 5: Per-entity module.

function isCylinderStyle(ent) {
    return !!(ent.style && ent.style.style_type === 'CylinderLineStyle');
}

function resolveLineLength(ent) {
    // `0` is the "infinite line" sentinel → fall back to the style default.
    return ent.length ? ent.length : styleParam(ent, 'length', 20.0);
}

function createLine(ent) {
    const color = parseColor(ent, '#44ff44');
    const opacity = styleParam(ent, 'opacity', 0.8);
    const length = resolveLineLength(ent);
    const origin = ent.origin || [0, 0, 0];
    const dir = ent.direction || [1, 0, 0];

    const d = new THREE.Vector3(dir[0], dir[1], dir[2]).normalize();
    const start = new THREE.Vector3(origin[0], origin[1], origin[2]);
    const end = start.clone().addScaledVector(d, length);

    if (isCylinderStyle(ent)) {
        const thickness = styleParam(ent, 'thickness', 0.03);
        const geometry = new THREE.CylinderGeometry(thickness, thickness, length, 8, 1);
        const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
        mesh.setRotationFromQuaternion(rotationFromDirection(d.x, d.y, d.z));
        mesh.position.set(
            origin[0] + d.x * length / 2,
            origin[1] + d.y * length / 2,
            origin[2] + d.z * length / 2
        );
        tagEntity(mesh, ent);
        return mesh;
    }

    const thickness = styleParam(ent, 'thickness', 1.0);
    const line = makeFatLine([start, end], color, opacity, thickness);
    tagEntity(line, ent);
    return line;
}

function updateLine(mesh, ent, prev) {
    // Switching between fat-line and cylinder rendering requires a rebuild.
    if (prev && isCylinderStyle(ent) !== isCylinderStyle(prev)) return false;

    const length = resolveLineLength(ent);
    // A length change alters the segment geometry; cheaper to rebuild.
    if (prev && !approxEqual(length, resolveLineLength(prev))) return false;

    const origin = ent.origin || prev?.origin || [0, 0, 0];
    const dir = ent.direction || prev?.direction || [1, 0, 0];
    const d = new THREE.Vector3(dir[0], dir[1], dir[2]).normalize();

    if (isCylinderStyle(ent)) {
        mesh.setRotationFromQuaternion(rotationFromDirection(d.x, d.y, d.z));
        mesh.position.set(
            origin[0] + d.x * length / 2,
            origin[1] + d.y * length / 2,
            origin[2] + d.z * length / 2
        );
    } else {
        const start = new THREE.Vector3(origin[0], origin[1], origin[2]);
        const end = start.clone().addScaledVector(d, length);
        mesh.geometry.setPositions([start.x, start.y, start.z, end.x, end.y, end.z]);
        const thickness = styleParam(ent, 'thickness', 1.0);
        if (mesh.material && mesh.material.linewidth !== undefined) {
            mesh.material.linewidth = Math.max(0.1, thickness);
        }
    }
    applyStyleUpdate(mesh, ent);
    return true;
}

// Plane renderer — rendered as a double-sided translucent quad
// with optional wireframe overlay.
// Phase 5: Per-entity module.

/**
 * Build the quad geometry for a plane entity.
 *
 * When ``ent.span_u`` / ``ent.span_v`` are present, returns a parallelogram
 * quad (two triangles) whose corners are ``point``, ``point + span_u``,
 * ``point + span_u + span_v`` and ``point + span_v`` — already in world space,
 * so the mesh must not be repositioned/reoriented.  Otherwise returns ``null``
 * and the caller falls back to the default square of half-side ``extent``
 * centred at the origin (positioned/oriented from ``point``/``normal``).
 */
function _planeGeometry(ent) {
    const spanU = ent.span_u;
    const spanV = ent.span_v;
    if (!Array.isArray(spanU) || !Array.isArray(spanV)) {
        return null;
    }
    const p = new THREE.Vector3(...(ent.point || [0, 0, 0]));
    const u = new THREE.Vector3(...spanU);
    const v = new THREE.Vector3(...spanV);
    // `point` is the plane *centre* (consistent with the non-span renderer
    // path and the label anchor), so the corners sit ±u/2 ±v/2 around it.
    const a = p.clone().addScaledVector(u, -0.5).addScaledVector(v, -0.5);
    const b = a.clone().add(u);
    const c = a.clone().add(u).add(v);
    const d = a.clone().add(v);
    const positions = new Float32Array([
        a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z,
        a.x, a.y, a.z, c.x, c.y, c.z, d.x, d.y, d.z,
    ]);
    const uvs = new Float32Array([0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1]);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
    geometry.computeVertexNormals();
    return geometry;
}

async function createPlane(ent) {
    const color = parseColor(ent, '#4488ff');
    const opacity = styleParam(ent, 'opacity', 0.3);
    const extent = ent.extent ?? styleParam(ent, 'extent', 10.0);
    const point = ent.point || [0, 0, 0];
    const normal = ent.normal || [0, 0, 1];

    const spanGeometry = _planeGeometry(ent);
    const geometry = spanGeometry || new THREE.PlaneGeometry(extent * 2, extent * 2);
    const material = makeMaterial(color, opacity, true);
    const mesh = new THREE.Mesh(geometry, material);

    if (spanGeometry) {
        // Vertices are already in world space (from point + span_u/span_v).
    } else {
        mesh.position.set(point[0], point[1], point[2]);
        mesh.setRotationFromQuaternion(rotationFromNormal(normal[0], normal[1], normal[2]));
    }

    // ── Texture label ──
    const texLabel = ent.style?.texture_label;
    if (texLabel && texLabel.text) {
        // Plane defaults: no offset
        if (texLabel.offset_v === undefined) texLabel.offset_v = 0.0;
        // Default background to entity color so the label blends in
        if (!texLabel.background || texLabel.background === 'transparent') {
            texLabel.background = color;
        }

        const texture = await createTextureLabel(texLabel.text, texLabel);
        if (texture) {
            // Apply align mode
            const align = texLabel.align || 'stretch';
            switch (align) {
                case 'fit':
                    texture.wrapS = THREE.ClampToEdgeWrapping;
                    texture.wrapT = THREE.ClampToEdgeWrapping;
                    texture.repeat.set(1, 1);
                    break;
                case 'repeat':
                    texture.wrapS = THREE.RepeatWrapping;
                    texture.wrapT = THREE.RepeatWrapping;
                    texture.repeat.set(
                        texLabel.repeat_u || 1,
                        texLabel.repeat_v || 1
                    );
                    break;
                case 'stretch':
                default:
                    texture.wrapS = THREE.ClampToEdgeWrapping;
                    texture.wrapT = THREE.ClampToEdgeWrapping;
                    texture.repeat.set(1, 1);
                    break;
            }
            material.map = texture;
            material.color.set(0xffffff);
            material.needsUpdate = true;
        }
    }

    // Wireframe overlay
    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            spanGeometry || new THREE.PlaneGeometry(extent * 2, extent * 2),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}

// Arc renderer — renders an arcing cylinder (partial torus) centered on
// `origin`, in the plane perpendicular to `axis`, sweeping `angle` radians
// from `startDirection`.  When `ent.arrow` is set (and the arc is not a full
// turn), a cone arrow tip is drawn at the arc's end.
// Phase 5: Per-entity module.

const TWO_PI = 2 * Math.PI;

function resolveArcRadius(ent) {
    return Math.max(ent.radius || 1.0, 0.001);
}

function resolveTubeRadius(ent) {
    return Math.max(ent.tubeRadius || 0.05, 0.001);
}

function resolveAngle(ent) {
    return THREE.MathUtils.clamp(ent.angle ?? TWO_PI, 0, TWO_PI);
}

function orientArc(group, ent) {
    const axis = ent.axis || [0, 0, 1];
    const startDirection = ent.startDirection || [1, 0, 0];
    const origin = ent.origin || [0, 0, 0];

    // Rotate the torus so its plane normal (+Z) aligns with `axis`, then
    // rotate around the axis so the torus's local +X (arc angle 0) lands on
    // `startDirection`.
    const qAxis = rotationFromNormal(axis[0], axis[1], axis[2]);
    const xPrime = new THREE.Vector3(1, 0, 0).applyQuaternion(qAxis);
    const qStart = new THREE.Quaternion().setFromUnitVectors(
        xPrime,
        new THREE.Vector3(startDirection[0], startDirection[1], startDirection[2]).normalize()
    );
    group.quaternion.copy(qStart.multiply(qAxis));
    group.position.set(origin[0], origin[1], origin[2]);
}

function createArc(ent) {
    const color = parseColor(ent, '#ffcc44');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const radius = resolveArcRadius(ent);
    const tubeRadius = resolveTubeRadius(ent);
    const angle = resolveAngle(ent);

    const group = new THREE.Group();
    const torus = new THREE.Mesh(
        new THREE.TorusGeometry(radius, tubeRadius, 16, 64, angle),
        makeMaterial(color, opacity)
    );
    group.add(torus);

    orientArc(group, ent);

    // Wireframe overlay
    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            group,
            new THREE.TorusGeometry(radius * 1.005, tubeRadius, 16, 64, angle),
            wfColor,
            dash,
            wfOpacity
        );
    }

    // Arrow tip (cone) at the arc's end — only for a genuine partial arc.
    const arrow = ent.arrow;
    if (arrow && angle < TWO_PI) {
        // Local torus coordinates: arc starts at +X, sweeps CCW in the XY
        // plane; the end point and forward tangent follow from the angle.
        const endPoint = new THREE.Vector3(
            radius * Math.cos(angle),
            radius * Math.sin(angle),
            0
        );
        const tangent = new THREE.Vector3(-Math.sin(angle), Math.cos(angle), 0);
        const cone = new THREE.Mesh(
            new THREE.ConeGeometry(arrow.radius, arrow.length, 16, 1),
            makeMaterial(color, opacity)
        );
        cone.setRotationFromQuaternion(rotationFromDirection(tangent.x, tangent.y, tangent.z));
        cone.position.copy(endPoint).addScaledVector(tangent, arrow.length / 2);
        group.add(cone);
    }

    tagEntity(group, ent);
    return group;
}

function updateArc(mesh, ent, prev) {
    // Any structural change alters the swept geometry; cheaper to rebuild.
    if (prev && !approxEqual(resolveArcRadius(ent), resolveArcRadius(prev))) return false;
    if (prev && !approxEqual(resolveTubeRadius(ent), resolveTubeRadius(prev))) return false;
    if (prev && !approxEqual(resolveAngle(ent), resolveAngle(prev))) return false;

    const a = ent.arrow || null;
    const b = prev?.arrow || null;
    if (!!a !== !!b) return false;
    if (
        a && b &&
        (!approxEqual(a.length, b.length) || !approxEqual(a.radius, b.radius))
    ) return false;

    orientArc(mesh, ent);
    applyStyleUpdate(mesh, ent);
    return true;
}

// Circle renderer — rendered as a torus with optional wireframe overlay.
// Phase 5: Per-entity module.

function createCircle(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);
    const tubeRadius = styleParam(ent, 'tubeRadius', 0.03);
    const wireframe = styleParam(ent, 'wireframe', false);

    const wireframeOnly = wireframe && opacity === 0;

    const geometry = new THREE.TorusGeometry(radius, tubeRadius, 16, 64);
    const mesh = wireframeOnly
        ? new THREE.Group()
        : new THREE.Mesh(geometry, makeMaterial(color, opacity));

    mesh.position.set(center[0], center[1], center[2]);

    if (ent.normal) {
        mesh.setRotationFromQuaternion(
            rotationFromNormal(ent.normal[0], ent.normal[1], ent.normal[2])
        );
    }

    // Wireframe overlay
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.TorusGeometry(radius * 1.005, tubeRadius, 16, 64),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}

// Cylinder renderer — renders a solid cylinder oriented along `axis`, spanning
// `length` with cross-section `radius`.  `alignCenter` positions `origin` along
// the length (0 = start/base point, 0.5 = center).
// Phase 4: Per-entity module.

function resolveCylinderLength(ent) {
    return Math.max(ent.length || 1.0, 0.001);
}

function resolveCylinderRadius(ent) {
    return Math.max(ent.radius || 0.1, 0.001);
}

function resolveAlignCenter(ent) {
    return ent.alignCenter ?? 0.0;
}

function createCylinder(ent) {
    const color = parseColor(ent, '#44aaff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const radius = resolveCylinderRadius(ent);
    const length = resolveCylinderLength(ent);
    const origin = ent.origin || [0, 0, 0];
    const axis = ent.axis || [0, 0, 1];
    const alignCenter = resolveAlignCenter(ent);

    const geometry = new THREE.CylinderGeometry(radius, radius, length, 24, 1);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));

    const d = new THREE.Vector3(axis[0], axis[1], axis[2]).normalize();
    mesh.setRotationFromQuaternion(rotationFromDirection(d.x, d.y, d.z));
    // CylinderGeometry is centered at its own origin.  `alignCenter` is the
    // fraction of `length` where `origin` sits (0 = start, 0.5 = center), so
    // the center is offset by (0.5 - alignCenter) * length along the axis.
    const offset = length * (0.5 - alignCenter);
    mesh.position.set(
        origin[0] + d.x * offset,
        origin[1] + d.y * offset,
        origin[2] + d.z * offset
    );

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.CylinderGeometry(radius * 1.005, radius * 1.005, length, 24, 1),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}

function updateCylinder(mesh, ent, prev) {
    // A radius/length/align change alters the geometry; cheaper to rebuild.
    if (prev && !approxEqual(resolveCylinderLength(ent), resolveCylinderLength(prev))) return false;
    if (prev && !approxEqual(resolveCylinderRadius(ent), resolveCylinderRadius(prev))) return false;
    if (prev && !approxEqual(resolveAlignCenter(ent), resolveAlignCenter(prev))) return false;

    const origin = ent.origin || prev?.origin || [0, 0, 0];
    const axis = ent.axis || prev?.axis || [0, 0, 1];
    const length = resolveCylinderLength(ent);
    const offset = length * (0.5 - resolveAlignCenter(ent));

    const d = new THREE.Vector3(axis[0], axis[1], axis[2]).normalize();
    mesh.setRotationFromQuaternion(rotationFromDirection(d.x, d.y, d.z));
    mesh.position.set(
        origin[0] + d.x * offset,
        origin[1] + d.y * offset,
        origin[2] + d.z * offset
    );

    applyStyleUpdate(mesh, ent);
    return true;
}

// Box renderer — a solid box, optionally rotated via an Euler triple.
// Phase 4: Per-entity module.

function createBox(ent) {
    const color = parseColor(ent, '#88ccff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const center = ent.center || [0, 0, 0];
    const size = ent.size || [1, 1, 1];

    const geometry = new THREE.BoxGeometry(size[0], size[1], size[2]);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
    mesh.position.set(center[0], center[1], center[2]);
    if (ent.rotation) {
        mesh.rotation.set(ent.rotation[0], ent.rotation[1], ent.rotation[2]);
    }

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.BoxGeometry(size[0] * 1.005, size[1] * 1.005, size[2] * 1.005),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}

// Disk renderer — a flat, circular slab oriented along `normal`.
// Phase 4: Per-entity module.

function createDisk(ent) {
    const color = parseColor(ent, '#ff8844');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);
    const thickness = Math.max(styleParam(ent, 'thickness', 0.02), 0.001);
    const normal = ent.normal || [0, 0, 1];

    const geometry = new THREE.CylinderGeometry(radius, radius, thickness, 48, 1);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
    mesh.position.set(center[0], center[1], center[2]);
    mesh.setRotationFromQuaternion(
        rotationFromDirection(normal[0], normal[1], normal[2])
    );

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.CylinderGeometry(radius * 1.005, radius * 1.005, thickness, 48, 1),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}

// Ellipse renderer — a flat, filled ellipse oriented along `normal`.
// Phase 4: Per-entity module.

function createEllipse(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const center = ent.center || [0, 0, 0];
    const radiusU = Math.max(ent.radiusU || 1.0, 0.001);
    const radiusV = Math.max(ent.radiusV || 0.5, 0.001);
    const normal = ent.normal || [0, 0, 1];

    const geometry = new THREE.CircleGeometry(1, 64);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity, true));
    mesh.position.set(center[0], center[1], center[2]);
    mesh.scale.set(radiusU, radiusV, 1);
    mesh.setRotationFromQuaternion(rotationFromNormal(normal[0], normal[1], normal[2]));

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        const wfGeo = new THREE.CircleGeometry(1.005, 64);
        wfGeo.scale(radiusU, radiusV, 1);
        addWireframeOverlay(mesh, wfGeo, wfColor, dash, wfOpacity);
    }

    tagEntity(mesh, ent);
    return mesh;
}

// Ellipsoid renderer — a unit sphere scaled by per-axis radii.
// Phase 4: Per-entity module.

function createEllipsoid(ent) {
    const color = parseColor(ent, '#ffaa00');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const center = ent.center || [0, 0, 0];
    const radii = ent.radii || [1, 1, 1];

    const geometry = new THREE.SphereGeometry(1, 32, 32);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
    mesh.position.set(center[0], center[1], center[2]);
    mesh.scale.set(radii[0], radii[1], radii[2]);
    if (ent.rotation) {
        mesh.rotation.set(ent.rotation[0], ent.rotation[1], ent.rotation[2]);
    }

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        const wfGeo = new THREE.SphereGeometry(1.005, 24, 24);
        wfGeo.scale(radii[0], radii[1], radii[2]);
        addWireframeOverlay(mesh, wfGeo, wfColor, dash, wfOpacity);
    }

    tagEntity(mesh, ent);
    return mesh;
}

// PartialDisk renderer — a flat, pie-shaped slab oriented along `normal`.
// Phase 4: Per-entity module.

/**
 * Build a quaternion that maps local +Y to `normal` and local +Z to
 * `inPlane`. `inPlane` is assumed perpendicular to `normal`.
 */
function rotationFromAxes(normal, inPlane) {
    const y = new THREE.Vector3(...normal).normalize();
    const z = new THREE.Vector3(...inPlane).normalize();
    const x = new THREE.Vector3().crossVectors(y, z).normalize();
    const zOrtho = new THREE.Vector3().crossVectors(x, y).normalize();
    const m = new THREE.Matrix4().makeBasis(x, y, zOrtho);
    return new THREE.Quaternion().setFromRotationMatrix(m);
}

function createPartialDisk(ent) {
    const color = parseColor(ent, '#ffcc44');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);
    const thickness = Math.max(styleParam(ent, 'thickness', 0.02), 0.001);
    const normal = ent.normal || [0, 0, 1];
    const startDirection = ent.startDirection || [1, 0, 0];
    const angle = Math.min(Math.max(ent.angle ?? 2 * Math.PI, 0.0), 2 * Math.PI);

    // The sector is symmetric about its bisector (matching the SDF primitive,
    // which is symmetric about local +Z). The bisector is `startDirection`
    // rotated by half the sweep about `normal`.
    const n = new THREE.Vector3(...normal).normalize();
    const s = new THREE.Vector3(...startDirection).normalize();
    const bisector = s.clone().multiplyScalar(Math.cos(angle / 2)).add(
        new THREE.Vector3().crossVectors(n, s).multiplyScalar(Math.sin(angle / 2))
    );

    const geometry = new THREE.CylinderGeometry(
        radius, radius, thickness, 48, 1, false, -angle / 2, angle
    );
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
    mesh.position.set(center[0], center[1], center[2]);
    mesh.setRotationFromQuaternion(rotationFromAxes(normal, bisector));

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.CylinderGeometry(
                radius * 1.005, radius * 1.005, thickness, 48, 1, false,
                -angle / 2, angle
            ),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}

// RegularPolygon renderer — a flat, regular n-gon prism oriented along `normal`.
// Phase 4: Per-entity module.

function createRegularPolygon(ent) {
    const color = parseColor(ent, '#44ffaa');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);
    const sides = Math.max(Math.floor(ent.sides || 6), 3);
    const thickness = Math.max(styleParam(ent, 'thickness', 0.02), 0.001);
    const normal = ent.normal || [0, 0, 1];
    const angle = ent.angle || 0.0;

    // CylinderGeometry with `radialSegments = sides` yields a regular n-gon.
    const geometry = new THREE.CylinderGeometry(radius, radius, thickness, sides, 1);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
    mesh.position.set(center[0], center[1], center[2]);
    mesh.setRotationFromQuaternion(
        rotationFromDirection(normal[0], normal[1], normal[2])
    );
    if (angle) {
        mesh.rotateY(angle);
    }

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.CylinderGeometry(radius * 1.005, radius * 1.005, thickness, sides, 1),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}

// Sphere renderer — rendered as a sphere with optional wireframe overlay.
// Phase 5: Per-entity module.

async function createSphere(ent) {
    const color = parseColor(ent, '#ffaa00');
    const opacity = styleParam(ent, 'opacity', 0.4);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);

    const geometry = new THREE.SphereGeometry(radius, 32, 32);
    const doubleSided = styleParam(ent, 'double_sided', false);
    const material = makeMaterial(color, opacity, doubleSided);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(center[0], center[1], center[2]);

    // ── Texture label ──
    const texLabel = ent.style?.texture_label;
    if (texLabel && texLabel.text) {
        // Default background to entity color so the label blends in
        if (!texLabel.background || texLabel.background === 'transparent') {
            texLabel.background = color;
        }
        const texture = await createTextureLabel(texLabel.text, texLabel);
        if (texture) {
            material.map = texture;
            // Set material color to white so the texture's own colors
            // pass through unmodified (MeshPhongMaterial multiplies
            // material.color * texture pixel values).
            material.color.set(0xffffff);
            material.needsUpdate = true;
        }
    }

    // Wireframe overlay
    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.SphereGeometry(radius * 1.005, 24, 24),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}

// Space renderer — rendered as box edges bounding the visible space.
// Phase 5: Per-entity module.

function createSpace(ent) {
    const color = parseColor(ent, '#888888');
    const opacity = styleParam(ent, 'opacity', 0.15);
    const extent = ent.extent ?? styleParam(ent, 'extent', 10.0);

    const geometry = new THREE.BoxGeometry(extent * 2, extent * 2, extent * 2);
    const edges = new THREE.EdgesGeometry(geometry);
    const flatPositions = edges.attributes.position.array;

    const box = makeFatSegmentsFromFlat(flatPositions, color, opacity, 1.0);

    tagEntity(box, ent);
    return box;
}

// PointPair renderer — two spheres connected by a line.
// Phase 6: Moved from inline factory.js to dedicated operator module.

function createPointPair(ent) {
    const color = parseColor(ent, '#44ff44');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const col = new THREE.Color(color);
    const g = new THREE.Group();

    // Place the group at the midpoint so that child positions are relative
    // to the midpoint (consistent with all other entity renderers).
    const pa = ent.pointA || [0, 0, 0];
    const pb = ent.pointB || [0, 0, 0];
    const mid = [(pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, (pa[2] + pb[2]) / 2];
    g.position.set(mid[0], mid[1], mid[2]);

    const sz = ent.pointSize || 0.06;
    const wireframe = styleParam(ent, 'wireframe', false);
    const wfColor = styleParam(ent, 'wireframe_color', null);
    const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
    const dash = wireframe ? styleParam(ent, 'wireframe_dash', null) : null;

    for (const pt of [pa, pb]) {
        const gm = new THREE.Mesh(
            new THREE.SphereGeometry(sz, 16, 16),
            makeMaterial(col, opacity)
        );
        // Positions relative to midpoint
        gm.position.set(pt[0] - mid[0], pt[1] - mid[1], pt[2] - mid[2]);

        // Wireframe overlay on each point sphere
        if (wireframe) {
            addWireframeOverlay(
                gm,
                new THREE.SphereGeometry(sz * 1.005, 16, 16),
                wfColor || col,
                dash,
                wfOpacity
            );
        }

        g.add(gm);
    }

    const lineThickness = styleParam(ent, 'line_thickness', 1);
    const start = new THREE.Vector3(
        pa[0] - mid[0], pa[1] - mid[1], pa[2] - mid[2]
    );
    const end = new THREE.Vector3(
        pb[0] - mid[0], pb[1] - mid[1], pb[2] - mid[2]
    );
    g.add(makeFatLine([start, end], col, opacity, lineThickness));
    return g;
}

// Inversion renderer — wireframe sphere at the inversion center.
// Phase 6: Moved from inline factory.js to dedicated operator module.

function createInversion(ent) {
    const color = parseColor(ent, '#cc88ff');
    const opacity = styleParam(ent, 'opacity', 0.4);
    const o = ent.center || [0, 0, 0];
    const r = ent.radius || 2.0;
    const col = new THREE.Color(color);
    const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(r, 32, 32),
        new THREE.MeshBasicMaterial({
            color: col,
            wireframe: true,
            opacity,
            transparent: true,
        })
    );
    mesh.position.set(o[0], o[1], o[2]);
    return mesh;
}

// Rotor renderer — disc arc, outer torus, and axis line.
// Phase 6: Moved from inline factory.js to dedicated operator module.

function createRotor(ent) {
    const color = parseColor(ent, '#ff8844');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const lineWidth = styleParam(ent, 'line_thickness', 1);
    const axis = ent.axis || [0, 0, 1];
    const angle = ent.angle ?? 0;
    const dr = ent.discRadius || 1.5;

    const g = buildRotorVisual(color, opacity, lineWidth, angle, dr);
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(axis[0], axis[1], axis[2]).normalize()
        )
    );
    return g;
}

// Translator renderer — arrow (cylinder shaft + cone head).
// Phase 6: Moved from inline factory.js to dedicated operator module.

function createTranslator(ent) {
    const color = parseColor(ent, '#44aaff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const vec = ent.vector || [1, 0, 0];
    const len = ent.length || 3.0;
    return createArrow(color, opacity, vec, len, ent.origin || [0, 0, 0]);
}

// Dilator renderer — concentric expanding rings.
// Phase 6: Moved from inline factory.js to dedicated operator module.

function createDilator(ent) {
    return createDilatorRings(
        parseColor(ent, '#ffcc44'),
        styleParam(ent, 'opacity', 0.6),
        ent.ringCount || 4,
        ent.maxRadius || 3.0,
        ent.origin || [0, 0, 0]
    );
}

// Motor renderer — general rotor (displaced axis) + translation arrow along it.
// Phase 6: Moved from inline factory.js to dedicated operator module.

function createMotor(ent) {
    const color = parseColor(ent, '#ff66cc');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const lineWidth = styleParam(ent, 'line_thickness', 1);
    const r = ent.rotor || {};
    const t = ent.translator || {};
    const axis = r.axis || [0, 0, 1];
    const angle = r.angle ?? 0;
    const origin = r.origin || [0, 0, 0];
    const tv = t.vector || [0, 0, 0];
    const tm = Math.sqrt(tv[0] ** 2 + tv[1] ** 2 + tv[2] ** 2);
    const dr = ent.discRadius || 1.5;

    const g = new THREE.Group();

    // General rotor: rotor visualization displaced to its axis origin.
    const rotorG = buildRotorVisual(color, opacity, lineWidth, angle, dr);
    rotorG.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(axis[0], axis[1], axis[2]).normalize()
        )
    );
    rotorG.position.set(origin[0], origin[1], origin[2]);
    g.add(rotorG);

    // Translation arrow along the axis (screw pitch).
    if (tm > 0) {
        g.add(createArrow(color, opacity, tv, tm, origin));
    }

    return g;
}

// GeneralRotor renderer — a rotor displaced from the origin.
// Phase 6: Moved from inline factory.js to dedicated operator module.

function createGeneralRotor(ent) {
    const color = parseColor(ent, '#ff9966');
    const opacity = styleParam(ent, 'opacity', 0.6);
    const lineWidth = styleParam(ent, 'line_thickness', 1);
    const axis = ent.axis || [0, 0, 1];
    const angle = ent.angle ?? 0;
    const dr = ent.discRadius || 1.5;
    const origin = ent.origin || [0, 0, 0];

    const g = buildRotorVisual(color, opacity, lineWidth, angle, dr);
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(axis[0], axis[1], axis[2]).normalize()
        )
    );
    g.position.set(origin[0], origin[1], origin[2]);
    return g;
}

// ReflectionLine renderer — cylinder oriented along the reflection direction.
// Phase 6: Moved from inline factory.js to dedicated operator module.

function createReflectionLine(ent) {
    const color = parseColor(ent, '#aaccff');
    const opacity = styleParam(ent, 'opacity', 0.6);
    const dir = ent.direction || [0, 0, 1];
    const len = ent.length || 5.0;
    const thick = ent.thickness || 0.04;
    const col = new THREE.Color(color);
    const g = new THREE.Group();
    const cg = new THREE.CylinderGeometry(thick, thick, len, 8, 1);
    g.add(new THREE.Mesh(cg, makeMaterial(col, opacity)));
    const d = new THREE.Vector3(dir[0], dir[1], dir[2]).normalize();
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d)
    );
    return g;
}

// ReflectionPlane renderer — mirror plane with normal arrow.
// Phase 6: Moved from inline factory.js to dedicated operator module.

function createReflectionPlane(ent) {
    const color = parseColor(ent, '#88ccff');
    const opacity = styleParam(ent, 'opacity', 0.35);
    const col = new THREE.Color(color);
    const n = ent.normal || [0, 0, 1];
    const ext = ent.extent ?? 5;
    const g = new THREE.Group();
    const pg = new THREE.PlaneGeometry(ext * 2, ext * 2);
    const pm = new THREE.MeshPhongMaterial({
        color: col,
        opacity,
        transparent: true,
        depthWrite: false,
        side: THREE.DoubleSide,
        emissive: col,
        emissiveIntensity: 0.15,
    });
    g.add(new THREE.Mesh(pg, pm));
    const al = ext * 0.3;
    const arrowG = createArrow(color, 0.8, n, al, [0, 0, 0]);
    g.add(arrowG);
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(n[0], n[1], n[2]).normalize()
        )
    );
    return g;
}

// ReflectionPoint renderer — wireframe sphere at the reflection point.
// Phase 6: Moved from inline factory.js to dedicated operator module.

function createReflectionPoint(ent) {
    const color = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 0.5);
    const o = ent.center || [0, 0, 0];
    const r = ent.radius || 1.0;
    const col = new THREE.Color(color);
    const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(r, 32, 32),
        new THREE.MeshBasicMaterial({
            color: col,
            wireframe: true,
            opacity,
            transparent: true,
        })
    );
    mesh.position.set(o[0], o[1], o[2]);
    return mesh;
}

// PointPath renderer — renders connected line segments from an ordered
// list of 3D points with optional per-vertex colors.
// Uses three.js Line2 (LineSegments2) fat lines so `line_thickness` is
// honored as a screen-space pixel width.

/**
 * Create a fat line for a PointPath entity JSON dict.
 *
 * ent.points: [[x,y,z], ...]
 * ent.colors: ["#ff0000", null, "#00ff00", ...]  — null = use uniform fallback
 * ent.color: "#ffffff"  — uniform fallback color
 * ent.opacity: 1.0
 * ent.line_thickness: 2  — screen-space pixel width
 */
function createPointPath(ent) {
    const points = ent.points || [];
    if (points.length < 2) {
        // Need at least 2 points for a line segment
        return new THREE.Group();
    }

    const perPointColors = ent.colors || [];
    const uniformColor = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const lineWidth = styleParam(ent, 'line_thickness', 2);

    // Determine if we should use per-vertex colors
    const hasAnyVertexColor = perPointColors.some(
        (c) => c !== null && c !== undefined
    );

    // Build segment pairs: each consecutive pair of points forms one segment
    // For n points we have n-1 segments, so 2*(n-1) positions.
    const n = points.length;
    const numVertices = (n - 1) * 2;
    const positions = new Float32Array(numVertices * 3);
    let vertexColors = null;
    if (hasAnyVertexColor) {
        vertexColors = new Float32Array(numVertices * 3);
    }

    for (let i = 0; i < n - 1; i++) {
        const p0 = points[i];
        const p1 = points[i + 1];
        const vi = i * 2;

        // Vertex i*2
        positions[vi * 3] = p0[0];
        positions[vi * 3 + 1] = p0[1];
        positions[vi * 3 + 2] = p0[2];

        // Vertex i*2 + 1
        positions[(vi + 1) * 3] = p1[0];
        positions[(vi + 1) * 3 + 1] = p1[1];
        positions[(vi + 1) * 3 + 2] = p1[2];

        if (hasAnyVertexColor) {
            const c0 = _resolveColor(perPointColors[i], uniformColor);
            const c1 = _resolveColor(perPointColors[i + 1], uniformColor);
            vertexColors[vi * 3] = c0.r;
            vertexColors[vi * 3 + 1] = c0.g;
            vertexColors[vi * 3 + 2] = c0.b;
            vertexColors[(vi + 1) * 3] = c1.r;
            vertexColors[(vi + 1) * 3 + 1] = c1.g;
            vertexColors[(vi + 1) * 3 + 2] = c1.b;
        }
    }

    const line = hasAnyVertexColor
        ? makeFatSegmentsColored(positions, vertexColors, opacity, lineWidth)
        : makeFatSegmentsFromFlat(positions, uniformColor, opacity, lineWidth);
    tagEntity(line, ent);
    return line;
}

function updatePointPath(_mesh, _ent, _prev) {
    // The fat-line geometry is rebuilt from ``points``/``colors``, so an
    // in-place update is never correct.  Returning false forces the caller
    // to dispose and recreate the mesh from the current frame's data.
    return false;
}

/**
 * Resolve a per-point color to an {r, g, b} object (0-1 range).
 * If the color is null/undefined, returns the parsed uniform color.
 */
function _resolveColor(colorHex, uniformColor) {
    if (colorHex === null || colorHex === undefined) {
        return uniformColor;
    }
    return new THREE.Color(colorHex);
}

// Axis renderer — a coordinate axis line with optional value labels and a
// name label placed along the axis.  No tick marks are drawn.

/**
 * Parse a Python-style float format specifier (e.g. ".2f") into a number of
 * decimal places.  Returns 1 for unrecognised formats.
 */
function _parseDecimals(fmt) {
    const m = /^\.(\d+)f$/.exec(fmt);
    return m ? parseInt(m[1], 10) : 1;
}

/**
 * Compute a normalized vector perpendicular to `v`.
 * The result is deterministic (no randomness).
 */
function perpendicularTo(v) {
    const x = Math.abs(v.x), y = Math.abs(v.y), z = Math.abs(v.z);
    if (x <= y && x <= z) {
        return new THREE.Vector3(0, -v.z, v.y).normalize();
    }
    if (y <= x && y <= z) {
        return new THREE.Vector3(-v.z, 0, v.x).normalize();
    }
    return new THREE.Vector3(-v.y, v.x, 0).normalize();
}

/**
 * Draw a single coordinate axis into `group`.
 *
 * `axis` is a JSON dict with the same shape as a standalone Axis entity:
 * `start`, `end`, `majorInterval`, `showValueLabels`, `valueFormat`,
 * `valueStart`, `valueStep`, `label`, and a resolved `style` (plus optional
 * flat `color`/`opacity`).
 *
 * The value labels are controlled by ``axis.style.value_style`` (a
 * ``LabelStyle`` dict with ``font_size``, ``color``, ``align``,
 * ``offset_2d`` and ``offset_local``) and ``axis.showValueLabels``.
 * The name label is controlled by ``axis.style.label_style`` (a
 * ``LabelStyle`` dict with ``along``, ``align``, ``offset_2d``,
 * ``font_size``, ``color`` and ``rotation``).
 * These are shared by `createAxis`, `createAxes2D`, and `createAxes3D` so
 * every axis is drawn identically.  `offset_local` is applied in the axis
 * local frame: x = along the axis, y = perpendicular (label separation),
 * z = binormal (``cross(dir, perp)``).
 */
function addAxis(group, axis) {
    const start = new THREE.Vector3(...(axis.start || [0, 0, 0]));
    const end = new THREE.Vector3(...(axis.end || [1, 0, 0]));
    const dir = end.clone().sub(start);
    const length = dir.length();
    if (length < 1e-9) return;
    dir.normalize();

    const color = parseColor(axis, '#888888');
    const colorHex = typeof color === 'string' ? color : '#' + color.getHexString();
    const opacity = styleParam(axis, 'opacity', 0.9);
    const lineWidth = styleParam(axis, 'line_thickness', 1);
    const major = Math.abs(axis.majorInterval || 1.0);

    // Value-label style (LabelStyle dict embedded in the resolved Axis style).
    const valueStyle = (axis.style && axis.style.value_style) || {};
    const showValueLabels = axis.showValueLabels !== false;

    const valueFormat = axis.valueFormat || '.1f';
    const decimals = _parseDecimals(valueFormat);
    const valueLabelSize = valueStyle.font_size ?? 12;
    const valueLabelColor = valueStyle.color ?? colorHex;
    const valueStart = axis.valueStart != null ? axis.valueStart : 0.0;
    const valueStep = axis.valueStep != null ? axis.valueStep : 1.0;

    const perp = perpendicularTo(dir);
    const binormal = new THREE.Vector3().crossVectors(dir, perp).normalize();

    // Baseline perpendicular separation between the axis line and its value
    // labels.  Zero so that with no explicit offset the label centre lies
    // exactly on the axis; use LabelStyle.offset_local to move it further.
    const valueLabelOffset = 0.0;

    // 3D label offset in the axis local frame:
    //   [0] along the axis, [1] perpendicular separation, [2] binormal.
    const offLocal = valueStyle.offset_local || [0, 0, 0];

    function addSegment(a, b) {
        const line = makeFatLine([a, b], color, opacity, lineWidth);
        group.add(line);
        return line;
    }

    function formatValue(value) {
        if (Number.isInteger(value)) return String(value);
        return value.toFixed(decimals);
    }

    function makeLabel(text, opts = {}) {
        const {
            bold = false,
            fontSize = 12,
            fontColor = colorHex,
            align = null,
            offset = null,
            rotation = 0,
        } = opts;

        const content = document.createElement('div');
        content.textContent = text;
        content.style.color = fontColor;
        content.style.fontSize = Math.round(fontSize * (bold ? 1.15 : 1.0)) + 'px';
        content.style.fontFamily = 'sans-serif';
        if (bold) content.style.fontWeight = 'bold';
        content.style.textShadow = '0 0 4px rgba(0,0,0,0.8)';
        content.style.pointerEvents = 'none';
        content.style.whiteSpace = 'nowrap';

        const ax = align ? align[0] : 0.5;
        const ay = align ? align[1] : 0.5;
        const ox = offset ? offset[0] : 0;
        const oy = offset ? offset[1] : 0;
        const tx = (0.5 - ax) * 100;
        const ty = (0.5 - ay) * 100;
        content.style.transformOrigin = `${ax * 100}% ${ay * 100}%`;
        content.style.transform = `translate(${ox}px, ${oy}px) translate(${tx}%, ${ty}%) rotate(${rotation}deg)`;

        // CSS2DRenderer repositions the element it wraps each frame, so the
        // styled content must be nested inside an outer element.  Otherwise
        // the align/offset transform on `content` would be overwritten.
        const wrapper = document.createElement('div');
        wrapper.style.pointerEvents = 'none';
        wrapper.appendChild(content);
        return new CSS2DObject(wrapper);
    }

    // Axis line
    addSegment(start, end);

    function placeValueLabel(p, text) {
        const labelPos = p.clone()
            .addScaledVector(dir, offLocal[0] || 0)
            .addScaledVector(perp, (offLocal[1] || 0) + valueLabelOffset)
            .addScaledVector(binormal, offLocal[2] || 0);
        const label = makeLabel(text, {
            fontSize: valueLabelSize,
            fontColor: valueLabelColor,
            align: valueStyle.align || null,
            offset: valueStyle.offset_2d || null,
            rotation: valueStyle.rotation || 0,
        });
        label.position.copy(labelPos);
        group.add(label);
    }

    // Value labels: an explicit tick list (position, label) takes precedence
    // over the uniform `majorInterval` spacing, enabling non-uniform scales.
    const ticks = axis.ticks;
    if (showValueLabels && Array.isArray(ticks) && ticks.length > 0) {
        for (const tick of ticks) {
            const t = tick[0];
            const text = tick[1] != null ? String(tick[1]) : '';
            placeValueLabel(start.clone().addScaledVector(dir, t), text);
        }
    } else if (showValueLabels && major > 0) {
        const count = Math.floor(length / major);
        for (let i = 1; i <= count; i++) {
            const t = i * major;
            const value = valueStart + i * major * valueStep;
            placeValueLabel(start.clone().addScaledVector(dir, t), formatValue(value));
        }
    }

    // Axis name label, anchored along the axis via `along` (default 0.5, the
    // midpoint) and hanging below it by default.
    if (axis.label) {
        const nameStyle = (axis.style && axis.style.label_style) || {};
        const along = nameStyle.along != null ? nameStyle.along : 0.5;
        const anchor = start.clone().addScaledVector(dir, length * along);
        const label = makeLabel(axis.label, {
            bold: true,
            fontSize: nameStyle.font_size ?? 12,
            fontColor: nameStyle.color ?? colorHex,
            align: nameStyle.align || [0.5, 0.0],
            offset: nameStyle.offset_2d || [0, 10],
            rotation: nameStyle.rotation || 0,
        });
        label.position.copy(anchor);
        group.add(label);
    }
}

/**
 * Create a standalone Axis entity (one line with its own style).
 */
function createAxis(ent) {
    const group = new THREE.Group();
    addAxis(group, ent);
    return group;
}

// Axes2D renderer — a group of coordinate axes in a 2D plane.
// Each axis half is drawn via the shared `addAxis` base so all axes
// render identically.

function createAxes2D(ent) {
    const group = new THREE.Group();
    for (const axis of ent.axes || []) {
        addAxis(group, axis);
    }
    tagEntity(group, ent);
    return group;
}

// Axes3D renderer — a group of coordinate axes in 3D space.
// Each axis half is drawn via the shared `addAxis` base so all axes
// render identically.

function createAxes3D(ent) {
    const group = new THREE.Group();
    for (const axis of ent.axes || []) {
        addAxis(group, axis);
    }
    tagEntity(group, ent);
    return group;
}

// Grid renderer — a coordinate grid in a UV plane.
// Draws lines parallel to dir_u and dir_v across the given ranges.
// range_u / range_v are [min, max] pairs relative to `origin`.

function createGrid(ent) {
    const group = new THREE.Group();

    const origin = new THREE.Vector3(...(ent.origin || [0, 0, 0]));
    const dirU = new THREE.Vector3(...(ent.dir_u || [1, 0, 0])).normalize();
    const dirV = new THREE.Vector3(...(ent.dir_v || [0, 1, 0])).normalize();

    const rangeU = ent.range_u || [0, 5];
    const rangeV = ent.range_v || [0, 5];
    const minU = Math.min(rangeU[0], rangeU[1]);
    const maxU = Math.max(rangeU[0], rangeU[1]);
    const minV = Math.min(rangeV[0], rangeV[1]);
    const maxV = Math.max(rangeV[0], rangeV[1]);
    const extentU = maxU - minU;
    const extentV = maxV - minV;

    const intervalU = Math.abs(ent.interval_u ?? 1.0);
    const intervalV = Math.abs(ent.interval_v ?? 1.0);

    const color = parseColor(ent, '#555555');
    const opacity = styleParam(ent, 'opacity', 0.5);
    const lineWidth = styleParam(ent, 'line_thickness', 1);
    const material = makeLineMaterial(color, opacity, lineWidth);

    // Corner of the grid rectangle in UV space.
    const corner = origin.clone()
        .addScaledVector(dirU, minU)
        .addScaledVector(dirV, minV);

    function addLine(a, b) {
        const line = makeFatLineWithMaterial([a, b], material);
        group.add(line);
    }

    // Lines parallel to dir_u (positioned along dir_v).
    if (Array.isArray(ent.line_positions_v)) {
        for (const vp of ent.line_positions_v) {
            const a = origin.clone()
                .addScaledVector(dirU, minU)
                .addScaledVector(dirV, vp);
            const b = a.clone().addScaledVector(dirU, extentU);
            addLine(a, b);
        }
    } else {
        const vSteps = Math.floor(extentV / intervalV);
        for (let i = 0; i <= vSteps; i++) {
            const t = i * intervalV;
            const a = corner.clone().addScaledVector(dirV, t);
            const b = a.clone().addScaledVector(dirU, extentU);
            addLine(a, b);
        }
    }

    // Lines parallel to dir_v (positioned along dir_u).
    if (Array.isArray(ent.line_positions_u)) {
        for (const up of ent.line_positions_u) {
            const a = origin.clone()
                .addScaledVector(dirU, up)
                .addScaledVector(dirV, minV);
            const b = a.clone().addScaledVector(dirV, extentV);
            addLine(a, b);
        }
    } else {
        const uSteps = Math.floor(extentU / intervalU);
        for (let i = 0; i <= uSteps; i++) {
            const t = i * intervalU;
            const a = corner.clone().addScaledVector(dirU, t);
            const b = a.clone().addScaledVector(dirV, extentV);
            addLine(a, b);
        }
    }

    tagEntity(group, ent);
    return group;
}

// VizGroup renderer — an empty THREE.Group container (no geometry).
// Scene-graph group nodes carry only a transform + parent/child structure.

function createVizGroup(ent) {
    const group = new THREE.Group();
    tagEntity(group, ent);
    return group;
}

// Entity renderer factory — thin dispatcher importing from per-entity
// and per-operator modules.  Phase 5+6 refactoring complete.

/**
 * Create a Three.js Object3D for a given entity JSON dict.
 * Dispatches to the appropriate per-entity renderer.
 */
async function createEntityMesh(ent) {
    let mesh;

    switch (ent.kind) {
        // ── Per-entity renderers (Phase 5) ──
        case 'Point':
        case 'HPoint':
            if (ent.style?.style_type === 'CrossHairPointStyle') {
                mesh = createCrossHairPoint(ent);
            } else {
                mesh = createPoint(ent);
            }
            break;
        case 'Direction':
            mesh = createDirection(ent);
            break;
        case 'Line':
            mesh = createLine(ent);
            break;
        case 'Plane':
            mesh = await createPlane(ent);
            break;
        case 'Circle':
            mesh = createCircle(ent);
            break;
        case 'Arc':
            mesh = createArc(ent);
            break;
        case 'Sphere':
            mesh = await createSphere(ent);
            break;
        case 'Cylinder':
            mesh = createCylinder(ent);
            break;
        case 'Disk':
            mesh = createDisk(ent);
            break;
        case 'PartialDisk':
            mesh = createPartialDisk(ent);
            break;
        case 'Box':
            mesh = createBox(ent);
            break;
        case 'Ellipsoid':
            mesh = createEllipsoid(ent);
            break;
        case 'Ellipse':
            mesh = createEllipse(ent);
            break;
        case 'RegularPolygon':
            mesh = createRegularPolygon(ent);
            break;
        case 'Space':
            mesh = createSpace(ent);
            break;

        // ── Operators (inline until Phase 6 refactoring) ──
        case 'PointPair':
            mesh = createPointPair(ent);
            break;
        case 'Inversion':
            mesh = createInversion(ent);
            break;
        case 'Rotor':
            mesh = createRotor(ent);
            break;
        case 'Translator':
            mesh = createTranslator(ent);
            break;
        case 'Dilator':
            mesh = createDilator(ent);
            break;
        case 'Motor':
            mesh = createMotor(ent);
            break;
        case 'GeneralRotor':
            mesh = createGeneralRotor(ent);
            break;
        case 'ReflectionLine':
            mesh = createReflectionLine(ent);
            break;
        case 'ReflectionPlane':
            mesh = createReflectionPlane(ent);
            break;
        case 'ReflectionPoint':
            mesh = createReflectionPoint(ent);
            break;

        case 'PointPath':
            mesh = createPointPath(ent);
            break;

        case 'Axis':
            mesh = createAxis(ent);
            break;
        case 'Axes2D':
            mesh = createAxes2D(ent);
            break;
        case 'Axes3D':
            mesh = createAxes3D(ent);
            break;
        case 'Grid':
            mesh = createGrid(ent);
            break;

        case 'VizGroup':
            mesh = createVizGroup(ent);
            break;

        case 'sdf':
            mesh = await createSdfProxy(ent);
            break;

        default:
            console.warn(`Unknown entity kind: ${ent.kind}`);
            sendLog('warn', `Unknown entity kind: ${ent.kind}`, { source: 'factory.js' });
            return null;
    }

    if (mesh) {
        tagEntity(mesh, ent);
    }
    return mesh;
}

function updateEntityMesh(mesh, ent, prev) {
    // Route to the co-located, kind-specific updater when one exists; these
    // handle bespoke placement (e.g. Line's segment midpoint) and return false
    // when the geometry must be rebuilt instead of updated in place.
    switch (ent.kind) {
        case 'sdf':
            // Structural (tree/bound/sdfKind) changes rebuild the shader;
            // transform/style changes are applied in place by updateSdfProxy.
            if (entityRequiresRebuild(ent, prev)) return false;
            return updateSdfProxy(mesh, ent, prev);
        case 'Line':
            return updateLine(mesh, ent, prev);
        case 'PointPath':
            return updatePointPath(mesh, ent, prev);
        case 'Direction':
            return updateDirection(mesh, ent, prev);
        case 'Arc':
            return updateArc(mesh, ent, prev);
        case 'Cylinder':
            return updateCylinder(mesh, ent, prev);
        default:
            break;
    }

    // Generic in-place update: position/orientation + common style fields.
    if (ent.position) {
        mesh.position.set(ent.position[0], ent.position[1], ent.position[2]);
    }
    if (ent.center) {
        mesh.position.set(ent.center[0], ent.center[1], ent.center[2]);
    }
    if (ent.vector || ent.direction) {
        const vec = ent.vector || ent.direction;
        const origin = ent.origin || [0, 0, 0];
        mesh.position.set(origin[0], origin[1], origin[2]);
        const dir = new THREE.Vector3(vec[0], vec[1], vec[2]).normalize();
        const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
        mesh.setRotationFromQuaternion(quat);
    }
    if (ent.rotation) {
        // Top-level Euler triple (Box / Ellipsoid). Applied in place so a
        // rotation-only content update doesn't require a mesh rebuild.
        mesh.rotation.set(ent.rotation[0], ent.rotation[1], ent.rotation[2]);
    } else if (ent.rotation === null) {
        // Explicitly cleared rotation (e.g. `Box(rotation=None)`) → identity,
        // i.e. back to axis-aligned.
        mesh.rotation.set(0, 0, 0);
    }
    applyStyleUpdate(mesh, ent);

    return !entityRequiresRebuild(ent, prev);
}

function removeEntityMesh(mesh) {
    if (!mesh) return;
    // Detach nested CSS2D label elements before removing from the scene so
    // they don't linger as ghost labels. Object3D.remove() only dispatches
    // 'removed' on the object itself, not its CSS2D descendants.
    mesh.traverse((c) => {
        if (c.isCSS2DObject && c.element && c.element.parentNode) {
            c.element.parentNode.removeChild(c.element);
        }
    });
    if (mesh.parent) mesh.parent.remove(mesh);
    mesh.traverse((c) => {
        if (c.geometry) c.geometry.dispose();
        if (c.material) {
            if (Array.isArray(c.material))
                c.material.forEach((m) => m.dispose());
            else c.material.dispose();
        }
    });
}

// Per-object SDF renderer for the standard viewer (Phase 3).
//
// Builds a bounding-volume proxy mesh: a BoxGeometry sized to the object's
// local-space AABB `bound` plus a ShaderMaterial whose fragment shader
// ray-marches that one object's distance field in local space and writes
// `gl_FragDepth`, so the standard depth buffer occludes it against meshes and
// other SDF proxies. Reuses the SDF viewer's `emitTree`, GLSL library, and
// directional-light uniform model (shared via `sdf/lighting.js`).

let _shaderParts = null;

async function _loadShaderParts() {
    if (_shaderParts) return _shaderParts;
    // Standalone HTML exports inline the GLSL as a global (there is no server
    // to fetch the .glsl files from); the live viewer fetches them instead.
    if (typeof window !== 'undefined' && window.__tanga_sdf_shaders) {
        _shaderParts = window.__tanga_sdf_shaders;
        return _shaderParts;
    }
    const base = new URL('./', import.meta.url);
    const [common, primitives, combinators, proxy] = await Promise.all([
        fetch(new URL('../sdf/shaders/sdf_common.glsl', base)).then((r) => r.text()),
        fetch(new URL('../sdf/shaders/primitives.glsl', base)).then((r) => r.text()),
        fetch(new URL('../sdf/shaders/combinators.glsl', base)).then((r) => r.text()),
        fetch(new URL('./sdf/proxy.glsl', base)).then((r) => r.text()),
    ]);
    _shaderParts = { common, primitives, combinators, proxy };
    return _shaderParts;
}

function _maxSteps(ent) {
    const v = ent.style && ent.style.max_steps;
    return typeof v === 'number' ? v : MAX_STEPS;
}

function _softShadows(ent) {
    return !ent.style || ent.style.soft_shadows !== false;
}

// Analytic edge AA is disabled by default (the silhouette fade still shows
// artifacts; revisit later). Opt back in with `SdfStyle(antialias=True)`.
function _antialias(ent) {
    return !!ent.style && ent.style.antialias === true;
}

function _anyTransparent(materials) {
    return materials.some((m) => m.w < 0.99);
}

// Compose a member's position/rotation (Euler XYZ)/scale into a world matrix,
// and return its INVERSE (the shader transforms points into the member's local
// space before evaluating its SDF).
function _memberInvTransform(member) {
    const t = member.transform || {};
    const pos = t.position || [0, 0, 0];
    const rot = t.rotation || [0, 0, 0];
    const scale = t.scale || [1, 1, 1];
    const m = new THREE.Matrix4().compose(
        new THREE.Vector3(pos[0], pos[1], pos[2]),
        new THREE.Quaternion().setFromEuler(new THREE.Euler(rot[0], rot[1], rot[2], 'XYZ')),
        new THREE.Vector3(scale[0], scale[1], scale[2]),
    );
    return m.invert();
}

// Build the per-member material table (uniform `uMaterial`, one `vec4(color,
// opacity)` per member). Single-material objects use slot 0; grouped objects
// fill one slot per member, resolving `null` color/opacity to the object's own.
function _buildMaterials(ent) {
    const [br, bg, bb] = parseHexColor(ent.color);
    const baseOpacity = typeof ent.opacity === 'number' ? ent.opacity : 1.0;
    const arr = Array.from({ length: MAX_GROUP_MEMBERS }, () => new THREE.Vector4(0, 0, 0, 1));
    const set = (i, hex, opacity) => {
        const [r, g, b] = parseHexColor(hex, [br, bg, bb]);
        arr[i].set(r, g, b, typeof opacity === 'number' ? opacity : baseOpacity);
    };
    if (ent.materials && ent.materials.length) {
        ent.materials.forEach((mat, i) => {
            if (i < MAX_GROUP_MEMBERS) set(i, mat.color, mat.opacity);
        });
    } else {
        set(0, ent.color, ent.opacity);
    }
    return arr;
}

function _buildUniforms(ent) {
    const uniforms = {
        uMaterial: { value: _buildMaterials(ent) },
        // Global opacity multiplier (1.0 normally; the interaction layer sets
        // it to `hover_opacity` on hover).
        uOpacity: { value: 1.0 },
        uMaxSteps: { value: _maxSteps(ent) },
        uSoftShadows: { value: _softShadows(ent) ? 1.0 : 0.0 },
        uAntialias: { value: _antialias(ent) ? 1.0 : 0.0 },
        uBoundHalf: { value: new THREE.Vector3() },
        uModelMatrix: { value: new THREE.Matrix4() },
        uProjectionMatrix: { value: new THREE.Matrix4() },
        uHover: { value: new THREE.Color(0x000000) },
        uLightCount: { value: 0 },
        uLightDir: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uLightColor: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uAmbientColor: { value: new THREE.Vector3() },
    };
    setLightUniforms(uniforms, parseLighting(DEFAULT_LIGHTING));

    if (ent.members) {
        // The shader declares the full array, so pad unused slots with identity.
        const invs = ent.members.map(_memberInvTransform);
        while (invs.length < MAX_GROUP_MEMBERS) invs.push(new THREE.Matrix4());
        uniforms.uMemberInvTransform = { value: invs };
    }

    return uniforms;
}

async function createSdfProxy(ent) {
    const parts = await _loadShaderParts();

    const bound = ent.bound || { min: [-1, -1, -1], max: [1, 1, 1] };
    const half = [
        (bound.max[0] - bound.min[0]) / 2,
        (bound.max[1] - bound.min[1]) / 2,
        (bound.max[2] - bound.min[2]) / 2,
    ];
    const center = [
        (bound.min[0] + bound.max[0]) / 2,
        (bound.min[1] + bound.max[1]) / 2,
        (bound.min[2] + bound.max[2]) / 2,
    ];

    const uniforms = _buildUniforms(ent);
    uniforms.uBoundHalf.value.set(half[0], half[1], half[2]);

    const material = new THREE.ShaderMaterial({
        vertexShader: buildProxyVertex(),
        fragmentShader: buildProxyFragment(ent, parts),
        uniforms,
        // Transparent when edge AA is enabled (to blend the silhouette fade) or
        // when any material is semi-transparent; opaque otherwise (the original
        // behaviour). Edge AA is disabled by default.
        transparent: _antialias(ent) || _anyTransparent(uniforms.uMaterial.value),
        depthWrite: true,
        depthTest: true,
        glslVersion: THREE.GLSL3,
        side: THREE.FrontSide,
    });

    const geometry = new THREE.BoxGeometry(half[0] * 2, half[1] * 2, half[2] * 2);
    const mesh = new THREE.Mesh(geometry, material);
    // The bound is centred at the object origin, so the box centre is [0,0,0];
    // keep the computation for hand-crafted (non-centred) bounds.
    mesh.position.set(center[0], center[1], center[2]);
    mesh.frustumCulled = true;

    // The depth write needs the live model/projection matrices in the fragment
    // shader (three.js only auto-provides them to the vertex shader).
    mesh.onBeforeRender = (_renderer, _scene, camera) => {
        material.uniforms.uModelMatrix.value.copy(mesh.matrixWorld);
        material.uniforms.uProjectionMatrix.value.copy(camera.projectionMatrix);
    };

    mesh.userData.sdfKind = ent.sdfKind || null;
    return mesh;
}

// Resize the proxy box + march bounds to a (possibly updated) `bound`. Used by
// `updateSdfProxy` so an SdfGroup can resize its proxy as members move without
// recompiling the shader.
function _resizeProxyBox(mesh, ent) {
    const bound = ent.bound || { min: [-1, -1, -1], max: [1, 1, 1] };
    const half = [
        (bound.max[0] - bound.min[0]) / 2,
        (bound.max[1] - bound.min[1]) / 2,
        (bound.max[2] - bound.min[2]) / 2,
    ];
    const center = [
        (bound.min[0] + bound.max[0]) / 2,
        (bound.min[1] + bound.max[1]) / 2,
        (bound.min[2] + bound.max[2]) / 2,
    ];
    const oldGeometry = mesh.geometry;
    mesh.geometry = new THREE.BoxGeometry(half[0] * 2, half[1] * 2, half[2] * 2);
    if (oldGeometry) oldGeometry.dispose();
    mesh.position.set(center[0], center[1], center[2]);
    mesh.material.uniforms.uBoundHalf.value.set(half[0], half[1], half[2]);
}

function updateSdfProxy(mesh, ent) {
    const mat = mesh.material;
    if (!mat || !mat.uniforms) return true;
    mat.uniforms.uMaterial.value = _buildMaterials(ent);
    mat.uniforms.uMaxSteps.value = _maxSteps(ent);
    mat.uniforms.uSoftShadows.value = _softShadows(ent) ? 1.0 : 0.0;
    mat.uniforms.uAntialias.value = _antialias(ent) ? 1.0 : 0.0;
    mat.transparent = _antialias(ent) || _anyTransparent(mat.uniforms.uMaterial.value);

    if (ent.members && mat.uniforms.uMemberInvTransform) {
        // Update each member's inverse transform uniform in place, then resize
        // the proxy box to the (recomputed) union AABB.
        const invs = mat.uniforms.uMemberInvTransform.value;
        ent.members.forEach((m, i) => {
            if (invs[i]) invs[i].copy(_memberInvTransform(m));
        });
        _resizeProxyBox(mesh, ent);
    }

    return true;
}

function disposeSdfProxy(mesh) {
    if (!mesh) return;
    if (mesh.geometry) mesh.geometry.dispose();
    if (mesh.material) mesh.material.dispose();
}

// Shared SDF lighting model (directional lights + ambient) used by both the
// fullscreen SDF viewer and the standard viewer's per-object SDF proxies, so
// both share one source of truth for the light preamble and uniform uploads.
//
// Pure module (no three.js / DOM): the light preamble is a GLSL string and the
// uniform setters operate on whatever uniform objects the caller supplies.

const MAX_LIGHTS = 8;

// Frontend defaults mirror the Python defaults (a white light from (10,20,10)
// at intensity 0.8 plus a white 0.45 ambient).
const DEFAULT_LIGHTING = {
    ambient: { color: '#ffffff', intensity: 0.45 },
    lights: [{ direction: [10, 20, 10], color: '#ffffff', intensity: 0.8 }],
};

// Declared as a JS template so `MAX_LIGHTS` has a single source of truth, then
// injected into the assembled fragment before the raymarch body.
const lightPreamble = `
const int MAX_LIGHTS = ${MAX_LIGHTS};
uniform int uLightCount;
uniform vec3 uLightDir[MAX_LIGHTS];
uniform vec3 uLightColor[MAX_LIGHTS];
uniform vec3 uAmbientColor;
`;

function parseHexColor(hex, fallback = [0.7, 0.6, 0.5]) {
    if (typeof hex !== 'string') return fallback;
    const m = /^#?([0-9a-fA-F]{6})$/.exec(hex.trim());
    if (!m) return fallback;
    const n = parseInt(m[1], 16);
    return [
        ((n >> 16) & 255) / 255,
        ((n >> 8) & 255) / 255,
        (n & 255) / 255,
    ];
}

function parseAmbient(a) {
    const [r, g, b] = parseHexColor(a && a.color);
    const i = a && typeof a.intensity === 'number' ? a.intensity : 1.0;
    return [r * i, g * i, b * i];
}

function parseLight(l) {
    const [r, g, b] = parseHexColor(l && l.color);
    const i = l && typeof l.intensity === 'number' ? l.intensity : 1.0;
    let d = (l && l.direction) || [0, 0, 1];
    const len = Math.hypot(d[0], d[1], d[2]);
    d = len > 1e-9 ? [d[0] / len, d[1] / len, d[2] / len] : [0, 0, 1];
    return { direction: d, color: [r * i, g * i, b * i] };
}

function parseLighting(wire) {
    return {
        ambient: parseAmbient((wire && wire.ambient) || DEFAULT_LIGHTING.ambient),
        lights: ((wire && wire.lights) || DEFAULT_LIGHTING.lights).map(parseLight),
    };
}

function setLightUniforms(u, lighting) {
    if (!u) return;
    u.uLightCount.value = lighting.lights.length;
    for (let i = 0; i < MAX_LIGHTS; i++) {
        const l = lighting.lights[i];
        if (l) {
            u.uLightDir.value[i].set(l.direction[0], l.direction[1], l.direction[2]);
            u.uLightColor.value[i].set(l.color[0], l.color[1], l.color[2]);
        } else {
            u.uLightDir.value[i].set(0, 0, 0);
            u.uLightColor.value[i].set(0, 0, 0);
        }
    }
    u.uAmbientColor.value.set(lighting.ambient[0], lighting.ambient[1], lighting.ambient[2]);
}

// Pure GLSL assembly for the per-object SDF proxy shader (no three.js / DOM).
//
// The proxy marches a *single* object's local-space SDF inside a bounding-box
// proxy mesh. `map()` returns `vec2(distance, materialIndex)` so grouped
// objects can shade each member with its own material; single objects use
// material slot 0 (index is always 0.0).

// Compile-time march cap. `uMaxSteps` clamps the loop at runtime so lowering
// the budget does not require a shader recompile.
const MAX_STEPS = 256;

// Compile-time cap on the number of members in an `SdfGroup`. The fold is
// unrolled per group, so this only sizes the uniform array (padded slots are
// identity and never read).
const MAX_GROUP_MEMBERS = 16;

// Smooth-blend radius default for the `smooth_*` fold modes (matches
// `sdf/composer.js`). A member with no explicit `smoothness` uses this.
const GROUP_SMOOTHNESS_DEFAULT = 0.1;

function _groupSmoothness(child) {
    const k = Number(
        child.smoothness != null ? child.smoothness : GROUP_SMOOTHNESS_DEFAULT,
    );
    return Number.isFinite(k) ? k : GROUP_SMOOTHNESS_DEFAULT;
}

function buildProxyVertex() {
    return `
out vec3 vLocalPos;
flat out vec3 vCameraLocal;

void main() {
    vLocalPos = position;
    // Camera position in the mesh's local space (same for every vertex).
    vCameraLocal = (inverse(modelMatrix) * vec4(cameraPosition, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;
}

// Fold an `SdfGroup`'s members into a single `float map(vec3 p)`. Each member
// is wrapped as `float memberI(vec3 p)` (its local-space tree) and folded with
// its combine mode; the member's runtime transform is applied via the
// `uMemberInvTransform[i]` uniform (inverse transform: point → member local).
function buildGroupMap(ent) {
    const children = (ent.tree && ent.tree.children) || [];
    const hasTransforms = !!ent.members;
    const lines = [];
    children.forEach((child, i) => {
        lines.push(`float member${i}(vec3 p) {`);
        lines.push(`    return ${emitTree(child)};`);
        lines.push('}');
    });
    lines.push('vec2 map(vec3 p) {');
    lines.push('    float d = MAX_DIST;');
    lines.push('    float m = 0.0;');
    children.forEach((child, i) => {
        const combine = (child.combine || 'union').toLowerCase();
        const k = _groupSmoothness(child);
        const local = hasTransforms
            ? `(uMemberInvTransform[${i}] * vec4(p, 1.0)).xyz`
            : 'p';
        lines.push(`    float d${i} = member${i}(${local});`);
        if (combine === 'subtract') {
            // The cut contributes no material; the material stays with `d`.
            lines.push(`    d = opSubtract(d, d${i});`);
        } else if (combine === 'intersection') {
            lines.push(`    if (d${i} > d) m = ${i}.0;`);
            lines.push(`    d = opIntersect(d, d${i});`);
        } else if (combine === 'xor') {
            lines.push(`    if (d${i} < d) m = ${i}.0;`);
            lines.push(`    d = opXor(d, d${i});`);
        } else if (combine === 'smooth_subtract') {
            // The cut contributes no material; the material stays with `d`.
            lines.push(`    vec2 sm${i} = opSmoothSubtract(d, d${i}, ${k});`);
            lines.push(`    d = sm${i}.x;`);
        } else if (combine === 'smooth_intersection') {
            lines.push(`    vec2 sm${i} = opSmoothIntersect(d, d${i}, ${k});`);
            lines.push(`    d = sm${i}.x;`);
            lines.push(`    m = mix(${i}.0, m, sm${i}.y);`);
        } else if (combine === 'smooth_union') {
            lines.push(`    vec2 sm${i} = opSmoothUnion(d, d${i}, ${k});`);
            lines.push(`    d = sm${i}.x;`);
            lines.push(`    m = mix(${i}.0, m, sm${i}.y);`);
        } else {
            lines.push(`    if (d${i} < d) m = ${i}.0;`);
            lines.push(`    d = opUnion(d, d${i});`);
        }
    });
    lines.push('    return vec2(d, m);');
    lines.push('}');
    return lines.join('\n');
}

// Assemble the proxy fragment from the fetched shader parts + the entity's
// single-object tree. `shaderParts` = { common, primitives, combinators, proxy }.
function buildProxyFragment(ent, shaderParts) {
    const { common, primitives, combinators, proxy } = shaderParts;
    const isGroup = !!(ent.tree && ent.tree.kind === 'group');

    const mapSrc = isGroup
        ? buildGroupMap(ent)
        : `vec2 map(vec3 p) {
    return vec2(${emitTree(ent.tree)}, 0.0);
}`;

    // `MAX_GROUP_MEMBERS` is sized once here; the `uMaterial` uniform itself is
    // declared in `proxy.glsl` (single source, no redefinition).
    const materialPreamble = `const int MAX_GROUP_MEMBERS = ${MAX_GROUP_MEMBERS};`;

    const transformPreamble = isGroup
        ? `uniform mat4 uMemberInvTransform[MAX_GROUP_MEMBERS];`
        : '';

    const parts = [
        common,
        primitives,
        combinators,
        lightPreamble,
        `const int MAX_STEPS = ${MAX_STEPS};`,
        materialPreamble,
        transformPreamble,
        mapSrc,
        proxy,
    ];
    return parts.filter((s) => s !== '').join('\n');
}

// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Shared camera-fit math used by the live viewer, the HTML export bootstrap,
// and (because it has no `three`/DOM dependency) the Node unit tests.  This is
// the single source of truth for the 2D ortho frustum and the finite-aspect
// computation — `view_mode.js`, `fit_camera.js`, and `js_apply_camera`
// (export) all call these, so the three can never drift apart.  Everything
// here is `three`/DOM-free; `applyOrthoFrustum` additionally mutates a camera
// object (`left`/`right`/`top`/`bottom`) but remains dependency-free.

/**
 * Return a finite aspect ratio (width / height), or NaN when the size is not
 * usable (zero, negative, or non-finite).  Callers must never write NaN into a
 * camera frustum, so they guard on this result.
 *
 * @param {number} width
 * @param {number} height
 * @returns {number}
 */
function finiteAspect(width, height) {
    const w = Number(width);
    const h = Number(height);
    if (!Number.isFinite(w) || !Number.isFinite(h) || w <= 0 || h <= 0) {
        return NaN;
    }
    return w / h;
}

/**
 * Compute the orthographic left/right/top/bottom for a 2D camera.
 *
 * @param {number} xmin
 * @param {number} xmax
 * @param {number} ymin
 * @param {number} ymax
 * @param {string} stretch  "fit" (letterbox) | "fill" | "fill_x" | "fill_y"
 * @param {number} borderPx  pixel margin (all modes)
 * @param {number} width     viewport width in CSS pixels
 * @param {number} height    viewport height in CSS pixels
 * @returns {{left:number, right:number, top:number, bottom:number}}
 */
function orthoFrustum(xmin, xmax, ymin, ymax, stretch, borderPx, width, height) {
    const extX = Math.abs(xmax - xmin) || 10;
    const extY = Math.abs(ymax - ymin) || 10;
    const w = Number(width);
    const h = Number(height);
    const bp = borderPx || 0;
    const cw = w - 2 * bp;
    const ch = h - 2 * bp;
    const mode = stretch || 'fit';

    if (mode === 'fill') {
        // Stretch-to-fill: the rectangle's width/height each fill the content
        // area (viewport inset by border_px), scaling X and Y independently
        // (non-uniform).  The camera is centered on the rectangle, so use
        // symmetric half-extents expanded back to the full viewport.
        const fX = cw > 0 ? w / cw : 1;
        const fY = ch > 0 ? h / ch : 1;
        return {
            left: -(extX / 2) * fX,
            right: (extX / 2) * fX,
            top: (extY / 2) * fY,
            bottom: -(extY / 2) * fY,
        };
    }

    // fill_x / fill_y: one axis fills the content area at a uniform scale;
    // the other keeps the aspect ratio and may over- or under-fill.
    if (mode === 'fill_x' && cw > 0 && ch > 0) {
        const fullW = extX * w / cw;
        const fullH = extX * h / cw;
        return {
            left: -fullW / 2,
            right: fullW / 2,
            top: fullH / 2,
            bottom: -fullH / 2,
        };
    }
    if (mode === 'fill_y' && cw > 0 && ch > 0) {
        const fullW = extY * w / ch;
        const fullH = extY * h / ch;
        return {
            left: -fullW / 2,
            right: fullW / 2,
            top: fullH / 2,
            bottom: -fullH / 2,
        };
    }

    // Undistorted letterboxing (fit, the default): a single
    // world-units-per-pixel scale so the full requested rectangle is
    // contained.  An optional pixel border shrinks the effective content area
    // before the fit.
    const aspect = finiteAspect(w, h);
    const safeAspect = Number.isFinite(aspect) ? aspect : 1;
    const aspectContent = (cw > 0 && ch > 0) ? (cw / ch) : safeAspect;
    const fit = Math.max(extX / aspectContent, extY);
    // Expand the fitted content frustum back to the full viewport so the
    // border appears as extra margin (still uniform scale).
    const fitFull = (bp > 0 && cw > 0 && ch > 0) ? (fit * h / ch) : fit;

    return {
        left: -fitFull * safeAspect / 2,
        right: fitFull * safeAspect / 2,
        top: fitFull / 2,
        bottom: -fitFull / 2,
    };
}

/**
 * Recompute an orthographic camera's `left`/`right`/`top`/`bottom` for the
 * given viewport size.  Recomputed from the stored fit
 * (``camera.userData._view2d``) when available; otherwise the current full
 * height is preserved.  Never writes NaN/Infinity — a corrupt frustum is
 * reset to a sane default box.
 *
 * @param {object} camera
 * @param {number} width   viewport width in CSS pixels
 * @param {number} height  viewport height in CSS pixels
 */
function applyOrthoFrustum(camera, width, height) {
    const aspect = finiteAspect(width, height);
    const v2d = camera.userData?._view2d;
    const finiteRect = v2d
        && Number.isFinite(v2d.xmin) && Number.isFinite(v2d.xmax)
        && Number.isFinite(v2d.ymin) && Number.isFinite(v2d.ymax);

    if (finiteRect) {
        const f = orthoFrustum(
            v2d.xmin, v2d.xmax, v2d.ymin, v2d.ymax,
            v2d.stretch || 'fit', v2d.border_px || 0, width, height
        );
        camera.left = f.left;
        camera.right = f.right;
        camera.top = f.top;
        camera.bottom = f.bottom;
        return;
    }

    // Fall back to preserving the current full height, but never propagate a
    // non-finite/corrupt frustum (Math.max(NaN, …) === NaN).
    const extX = Math.abs(camera.right - camera.left);
    const extY = Math.abs(camera.top - camera.bottom);
    if (!Number.isFinite(extX) || !Number.isFinite(extY) || extX <= 0 || extY <= 0) {
        const height = 10;  // sane default full height
        camera.left = -height * aspect / 2;
        camera.right = height * aspect / 2;
        camera.top = height / 2;
        camera.bottom = -height / 2;
        return;
    }

    const fit = Math.max(extX / aspect, extY);
    camera.left = -fit * aspect / 2;
    camera.right = fit * aspect / 2;
    camera.top = fit / 2;
    camera.bottom = -fit / 2;
}

// Tanga 3D Viewer — Shared scene-graph construction (live viewer + HTML export).
// Entity node construction (transform wrap + `parent_id` parenting) and
// overlay/label creation, shared by `viewer.js` and the export bootstrap so a
// render-pipeline change is made once.

function isIdentityTransform(transform) {
    if (!transform) return true;
    const p = transform.position || [0, 0, 0];
    const r = transform.rotation || [0, 0, 0];
    const s = transform.scale || [1, 1, 1];
    return p[0] === 0 && p[1] === 0 && p[2] === 0
        && r[0] === 0 && r[1] === 0 && r[2] === 0
        && s[0] === 1 && s[1] === 1 && s[2] === 1;
}

function applyTransformToObject(obj, transform) {
    if (!transform) return;
    if (transform.position) obj.position.set(transform.position[0], transform.position[1], transform.position[2]);
    if (transform.rotation) obj.rotation.set(transform.rotation[0], transform.rotation[1], transform.rotation[2]);
    if (transform.scale) obj.scale.set(transform.scale[0], transform.scale[1], transform.scale[2]);
}

function wrapWithNodeTransform(mesh, transform) {
    if (isIdentityTransform(transform)) return mesh;
    const node = new THREE.Group();
    node.add(mesh);
    applyTransformToObject(node, transform);
    return node;
}

// Build a scene-layer object: mesh → node transform wrap → parent under
// `parent_id` (or the scene) → register.  Returns the registry entry or null.
async function buildSceneObject(obj, scene, registry) {
    const mesh = await createEntityMesh(obj);
    if (!mesh) return null;

    const node = wrapWithNodeTransform(mesh, obj.transform);
    const parent = obj.parent_id ? registry.get(obj.parent_id) : null;
    if (parent && parent.obj) {
        parent.obj.add(node);
    } else {
        scene.add(node);
    }
    node.userData.parentId = obj.parent_id || null;

    const entry = { obj: node, mesh, data: { ...obj }, layer: 'scene' };
    registry.set(obj.id, entry);
    return entry;
}

// Build a label overlay as a CSS2DObject, parented under `attach_to` (or the
// legacy `parentId`) with the offset/align transform applied.  Annotation and
// title overlays are host-specific and intentionally not handled here.
function buildOverlay(obj, scene, registry) {
    if (obj.kind !== 'label') return null;
    if (!obj.text) return null;

    const div = document.createElement('div');
    div.textContent = obj.text;
    const s = obj.style || {};
    div.style.fontFamily = s.font_family || 'sans-serif';
    div.style.fontSize = (s.font_size || 14) + 'px';
    div.style.color = s.color || '#ffffff';
    div.style.backgroundColor = s.background || 'rgba(0, 0, 0, 0.6)';
    div.style.padding = '2px 6px';
    div.style.borderRadius = '3px';
    div.style.userSelect = 'none';
    div.style.whiteSpace = 'nowrap';
    if (typeof renderMathInElement !== 'undefined') {
        try {
            renderMathInElement(div, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        } catch (e) {
            console.warn('KaTeX label rendering error:', e);
            sendLog('warn', 'KaTeX label rendering error', { source: 'scene-builder.js', data: { error: String(e) } });
        }
    }

    const container = document.createElement('div');
    container.appendChild(div);
    const css2d = new CSS2DObject(container);

    const attachId = obj.attach_to ?? obj.parentId;
    if (attachId) {
        const pos = obj.position || [0, 0, 0];
        css2d.position.set(pos[0], pos[1], pos[2]);
        // CSS2DRenderer centers the container; counter that on the inner div
        // plus apply the pixel offset:
        const off2d = s.offset_2d || [0, 0];
        const align = s.align || [0.5, 0.5];
        const rotation = s.rotation || 0;
        const tx = (0.5 - align[0]) * 100;
        const ty = (0.5 - align[1]) * 100;
        div.style.transformOrigin = `${align[0] * 100}% ${align[1] * 100}%`;
        div.style.transform = `translate(${off2d[0]}px, ${off2d[1]}px) translate(${tx}%, ${ty}%) rotate(${rotation}deg)`;

        const parent = registry.get(attachId);
        if (parent && parent.obj) {
            parent.obj.add(css2d);
            parent.obj.userData._labels = parent.obj.userData._labels || [];
            parent.obj.userData._labels.push(obj.id);
            css2d.userData._parentId = attachId;
        } else {
            scene.add(css2d);
        }
    } else {
        const pos = obj.position || [0, 0, 0];
        css2d.position.set(pos[0], pos[1], pos[2]);
        scene.add(css2d);
    }

    const entry = { obj: css2d, mesh: null, data: { ...obj }, el: div, layer: 'overlay' };
    registry.set(obj.id, entry);
    return entry;
}

// Dispose and unregister: scene objects via `removeEntityMesh`; overlays via
// parent detachment + DOM removal.
function removeObject(id, registry) {
    const entry = registry.get(id);
    if (!entry) return false;

    if (entry.layer === 'scene') {
        if (entry.obj) removeEntityMesh(entry.obj);
    } else {
        if (entry.obj && entry.obj.removeFromParent) entry.obj.removeFromParent();
        if (entry.obj && entry.obj.element) entry.obj.element.remove();
        if (entry.el) entry.el.remove();
    }
    registry.delete(id);
    return true;
}

// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Shared camera auto-fit used by both the live viewer and the HTML export
// bootstrap.  The live viewer reaches this through `view_mode.js` (which
// re-exports it); the export pipeline concatenates this file directly (imports
// and `export` keywords are stripped), so both paths run the exact same
// function.

const _REFERENCE_KINDS = new Set(['Axes3D', 'Axes2D', 'Axis', 'Grid']);

/**
 * Auto-fit the camera to the scene contents.
 *
 * @param {Map<string,{obj:THREE.Object3D|null,layer:string,data?:object}>} sceneObjects
 * @param {THREE.Camera} camera
 * @param {THREE.OrbitControls} controls
 * @param {number} spaceDim  2 or 3
 * @param {number|null} width   viewport width in CSS px (falls back to window)
 * @param {number|null} height  viewport height in CSS px (falls back to window)
 */
function fitCamera(sceneObjects, camera, controls, spaceDim, width, height) {
    // ── 2D orthographic fit (top-down; contain the content box) ──
    if (spaceDim === 2) {
        const box = new THREE.Box3();
        sceneObjects.forEach(entry => {
            if (entry && entry.layer === 'scene' && entry.obj) box.expandByObject(entry.obj);
        });
        if (box.isEmpty()) return;

        const center = new THREE.Vector3();
        box.getCenter(center);
        const size = new THREE.Vector3();
        box.getSize(size);

        // Expand the content box by a small margin (10% of the max extent,
        // matching the historical 1.2 factor) and let `orthoFrustum` letterbox
        // it to the actual viewport aspect.
        const margin = Math.max(size.x, size.y, 1) * 0.1;
        const xmin = center.x - size.x / 2 - margin;
        const xmax = center.x + size.x / 2 + margin;
        const ymin = center.y - size.y / 2 - margin;
        const ymax = center.y + size.y / 2 + margin;

        const f = orthoFrustum(xmin, xmax, ymin, ymax, 'fit', 0,
            width ?? window.innerWidth, height ?? window.innerHeight);
        camera.left = f.left;
        camera.right = f.right;
        camera.top = f.top;
        camera.bottom = f.bottom;
        camera.position.set(center.x, center.y, 20);
        camera.lookAt(center.x, center.y, 0);
        camera.updateProjectionMatrix();
        controls.target.set(center.x, center.y, 0);
        controls.update();
        // Persist the fitted rectangle so resize recomputes from the original
        // fit (letterbox) rather than the current, possibly-corrupt frustum.
        camera.userData._view2d = { xmin, xmax, ymin, ymax, stretch: 'fit', border_px: 0 };
        return;
    }

    // ── 3D perspective fit ──
    // Exclude reference-frame objects (axes/grid) so the fit frames the actual
    // content; always include the origin so the view stays anchored on it.
    const content = [];
    const reference = [];
    sceneObjects.forEach(entry => {
        if (!entry || entry.layer !== 'scene' || !entry.obj) return;
        const kind = entry.data && entry.data.kind;
        if (_REFERENCE_KINDS.has(kind)) reference.push(entry.obj);
        else content.push(entry.obj);
    });

    const box = new THREE.Box3();
    if (content.length === 0 && reference.length === 0) {
        // Completely empty scene → default 10-unit cube centred at the origin.
        box.set(new THREE.Vector3(-5, -5, -5), new THREE.Vector3(5, 5, 5));
    } else {
        box.expandByPoint(new THREE.Vector3(0, 0, 0));
        const sources = content.length > 0 ? content : reference;
        for (const obj of sources) box.expandByObject(obj);
    }

    const center = new THREE.Vector3();
    box.getCenter(center);
    const size = new THREE.Vector3();
    box.getSize(size);

    // Fit the box's bounding sphere within the vertical FOV (with a small
    // margin), looking at the world origin so orbit always rotates around it.
    const radius = Math.max(0.5, 0.5 * size.length());
    const fov = ((camera && camera.fov) || 50) * Math.PI / 180;
    const distance = (radius / Math.sin(fov / 2)) * 1.1;
    const dir = new THREE.Vector3(0.6, 0.5, 0.7).normalize();

    controls.target.set(0, 0, 0);
    camera.position.set(
        center.x + dir.x * distance,
        center.y + dir.y * distance,
        center.z + dir.z * distance,
    );
    camera.lookAt(controls.target);
    camera.near = Math.max(0.01, distance * 0.001);
    camera.far = distance * 10;
    camera.updateProjectionMatrix();
    controls.update();
}

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

function transformExpr(transform, p = 'p') {
    const pos = transform?.position || [0, 0, 0];
    let expr = `(${p} - vec3(${floatParam(pos[0])}, ${floatParam(pos[1])}, ${floatParam(pos[2])}))`;
    if (transform?.rotation) {
        const axis = transform.rotation.axis;
        const angle = transform.rotation.angle;
        expr = `rotationAxisAngle(normalize(vec3(${floatParam(axis[0])}, ${floatParam(axis[1])}, ${floatParam(axis[2])})), ${floatParam(angle)}) * ${expr}`;
    }
    return expr;
}

function floatParam(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return '0.0';
    const s = String(n);
    // GLSL ES 3.0 has no implicit int → float conversion, so integral values
    // must carry a `.0` suffix (`3` is an int literal, `3.0` is a float).
    return /[.eE]/.test(s) ? s : `${s}.0`;
}

// Per-primitive-kind GLSL emitters.
//
// Each entry maps the serialized node `kind` (shared with Python
// `sdf/primitives.py`) to a function returning the GLSL call string from the
// node's local-space point expression `p` and its typed `params`.

const vec3 = (v) => `vec3(${floatParam(v[0])}, ${floatParam(v[1])}, ${floatParam(v[2])})`;
const vec2 = (v) => `vec2(${floatParam(v[0])}, ${floatParam(v[1])})`;

function emitPrimitive(node, p) {
    const params = node.params || {};
    switch (node.kind) {
        case 'sphere':
            return `sdSphere(${p}, ${floatParam(params.radius)})`;
        case 'box':
            return `sdBox(${p}, ${vec3(params.halfExtents)})`;
        case 'roundBox':
            return `sdRoundBox(${p}, ${vec3(params.halfExtents)}, ${floatParam(params.radius)})`;
        case 'cylinder':
            return `sdCylinder(${p}, ${floatParam(params.radius)})`;
        case 'cappedCylinder':
            return `sdCappedCylinder(${p}, ${floatParam(params.halfHeight)}, ${floatParam(params.radius)})`;
        case 'torus':
            return `sdTorus(${p}, ${vec2([params.mainRadius, params.tubeRadius])})`;
        case 'cone':
            return `sdCone(${p}, ${floatParam(params.angle)})`;
        case 'cappedCone':
            return `sdCappedCone(${p}, ${floatParam(params.halfHeight)}, ${floatParam(params.radius1)}, ${floatParam(params.radius2)})`;
        case 'ellipsoid':
            return `sdEllipsoid(${p}, ${vec3(params.radii)})`;
        case 'capsule':
            return `sdCapsule(${p}, ${vec3(params.a)}, ${vec3(params.b)}, ${floatParam(params.radiusA)}, ${floatParam(params.radiusB)})`;
        case 'segment':
            return `sdSegment(${p}, ${vec3(params.a)}, ${vec3(params.b)})`;
        case 'plane':
            return `sdPlane(${p}, ${vec3(params.normal)}, ${floatParam(params.offset)})`;
        case 'partialDisk':
            return `sdPartialDisk(${p}, ${floatParam(params.halfHeight)}, ${floatParam(params.radius)}, ${floatParam(params.angle)})`;
        case 'regularPolygon':
            return `sdRegularPolygon(${p}, ${floatParam(params.halfHeight)}, ${floatParam(params.radius)}, ${floatParam(params.sides)})`;
        default:
            throw new Error(`Unknown SDF primitive kind: ${node.kind}`);
    }
}

// Per-combinator-kind GLSL emitters.
//
// Maps a combinator node `kind` to an expression folding its already-emitted
// child distance strings. Hard combinators use IQ min/max with sign
// preservation; `bound` is an alias for a finite clip box (intersect with an
// `sdBox`). A `group` node folds its children in order, each with its own
// `combine` mode (the nested-CSG shape used by `Composed` objects). Smooth
// `smooth_*` modes use the IQ `opSmooth*` helpers and fold down to a scalar by
// taking `.x` (the blend factor is only meaningful at the material-mixing fold
// in the proxy shader / composer, not inside a single member's tree).

// Smooth-blend radius default (matches `sdf/composer.js`).
const COMBINE_SMOOTHNESS_DEFAULT = 0.1;

function _combineSmoothness(node) {
    const k = Number(
        node.smoothness != null ? node.smoothness : COMBINE_SMOOTHNESS_DEFAULT,
    );
    return Number.isFinite(k) ? k : COMBINE_SMOOTHNESS_DEFAULT;
}

function foldOp(op, a, b, k = COMBINE_SMOOTHNESS_DEFAULT) {
    if (op === 'intersection' || op === 'intersect') return `opIntersect(${a}, ${b})`;
    if (op === 'subtract') return `opSubtract(${a}, ${b})`;
    if (op === 'xor') return `opXor(${a}, ${b})`;
    if (op === 'smooth_union') return `opSmoothUnion(${a}, ${b}, ${k}).x`;
    if (op === 'smooth_intersection' || op === 'smooth_intersect') {
        return `opSmoothIntersect(${a}, ${b}, ${k}).x`;
    }
    if (op === 'smooth_subtract') return `opSmoothSubtract(${a}, ${b}, ${k}).x`;
    return `opUnion(${a}, ${b})`;
}

function childExpr(node, child) {
    // A primitive child evaluates in its local space; a combinator child has
    // already been emitted recursively.
    if (child.children) {
        return emitNode(child);
    }
    return emitPrimitive(child, transformExpr(child.transform));
}

function emitNode(node) {
    switch (node.kind) {
        case 'union':
        case 'intersect':
        case 'subtract':
        case 'xor':
        case 'smooth_union':
        case 'smooth_intersection':
        case 'smooth_intersect':
        case 'smooth_subtract': {
            // Uniform fold: every child combines with the node's single op.
            const k = _combineSmoothness(node);
            const [first, ...rest] = node.children;
            let acc = childExpr(node, first);
            for (const child of rest) {
                const d = childExpr(node, child);
                acc = foldOp(node.kind, acc, d, k);
            }
            return acc;
        }
        case 'group': {
            // Ordered fold: each child carries its own `combine` mode.
            const children = node.children || [];
            let acc = null;
            for (const child of children) {
                const d = childExpr(node, child);
                const k = _combineSmoothness(child);
                acc = acc === null ? d : foldOp(child.combine || 'union', acc, d, k);
            }
            return acc === null ? 'MAX_DIST' : acc;
        }
        default:
            throw new Error(`Unknown SDF combinator kind: ${node.kind}`);
    }
}

function emitTree(tree) {
    // A root can be a bare primitive (e.g. a point = a single sphere), a
    // combinator tree, or a `group` of combined constituents.
    if (tree.children) {
        return emitNode(tree);
    }
    return emitPrimitive(tree, transformExpr(tree.transform));
}

window.__tanga = {
    THREE, OrbitControls, CSS2DRenderer, CSS2DObject, Line2, LineSegments2, LineMaterial, LineGeometry, LineSegmentsGeometry, buildSceneObject, buildOverlay, fitCamera, orthoFrustum, finiteAspect, updateEntityMesh, removeEntityMesh,
};
