// Overlay emitters — per-kind GLSL emitters for shader-drawn overlays.
//
// Overlays are NOT raymarched volumes: each is a procedural pattern drawn in
// the fragment shader and depth-composited against the raymarch result (an
// overlay in front of the surface draws over it; one behind is hidden). Each
// registered kind contributes a GLSL preamble (uniforms + a per-kind apply
// function) plus uniform builders; `applyOverlays` chains them all and is
// called from the raymarch `main()` after shading.
//
// This mirrors the standard viewer's `renderers/factory.js` dispatch, in GLSL
// space. Register a new overlay kind here by adding a `{kind, applyFn, src,
// buildUniforms, applyUniforms}` entry.

import * as THREE from 'three';

import { parseHexColor } from '../material-table.js';

export const MAX_GRIDS = 8;
export const MAX_AXES = 4;

function gridUniformDefaults() {
    return {
        uGridCount: { value: 0 },
        uGridOrigin: { value: Array.from({ length: MAX_GRIDS }, () => new THREE.Vector3()) },
        uGridU: { value: Array.from({ length: MAX_GRIDS }, () => new THREE.Vector3()) },
        uGridV: { value: Array.from({ length: MAX_GRIDS }, () => new THREE.Vector3()) },
        uGridInterval: { value: Array.from({ length: MAX_GRIDS }, () => new THREE.Vector2(1, 1)) },
        uGridColor: { value: Array.from({ length: MAX_GRIDS }, () => new THREE.Vector4(0, 0, 0, 0)) },
    };
}

function populateGridUniforms(u, overlays) {
    const grids = (overlays || []).filter((o) => o.kind === 'grid');
    const n = Math.min(grids.length, MAX_GRIDS);
    u.uGridCount.value = n;
    for (let i = 0; i < MAX_GRIDS; i++) {
        const g = i < n ? grids[i] : null;
        if (g) {
            u.uGridOrigin.value[i].set(g.origin[0], g.origin[1], g.origin[2]);
            u.uGridU.value[i].set(g.dir_u[0], g.dir_u[1], g.dir_u[2]).normalize();
            u.uGridV.value[i].set(g.dir_v[0], g.dir_v[1], g.dir_v[2]).normalize();
            u.uGridInterval.value[i].set(g.interval_u, g.interval_v);
            const [r, gg, b] = parseHexColor(g.color);
            u.uGridColor.value[i].set(r, gg, b, typeof g.opacity === 'number' ? g.opacity : 0.5);
        } else {
            u.uGridOrigin.value[i].set(0, 0, 0);
            u.uGridU.value[i].set(0, 0, 0);
            u.uGridV.value[i].set(0, 0, 0);
            u.uGridInterval.value[i].set(1, 1);
            u.uGridColor.value[i].set(0, 0, 0, 0);
        }
    }
}

const grid = {
    kind: 'grid',
    applyFn: 'applyGrid',
    src: `
const int MAX_GRIDS = ${MAX_GRIDS};
uniform int uGridCount;
uniform vec3 uGridOrigin[MAX_GRIDS];
uniform vec3 uGridU[MAX_GRIDS];
uniform vec3 uGridV[MAX_GRIDS];
uniform vec2 uGridInterval[MAX_GRIDS];
uniform vec4 uGridColor[MAX_GRIDS];  // rgb = color, a = opacity

vec3 applyGrid(vec3 col, vec3 ro, vec3 rd, float tHit, bool hit, float maxDist) {
    for (int i = 0; i < MAX_GRIDS; i++) {
        if (i >= uGridCount) break;
        vec3 n = normalize(cross(uGridU[i], uGridV[i]));
        float denom = dot(rd, n);
        if (abs(denom) < 1e-6) continue;
        float t = dot(uGridOrigin[i] - ro, n) / denom;
        if (t < 0.0) continue;
        float limit = hit ? tHit : maxDist;
        if (t >= limit) continue;
        vec3 p = ro + rd * t;
        vec2 c = vec2(
            dot(p - uGridOrigin[i], uGridU[i]) / uGridInterval[i].x,
            dot(p - uGridOrigin[i], uGridV[i]) / uGridInterval[i].y
        );
        vec2 g = abs(fract(c) - 0.5) / fwidth(c);
        float line = 1.0 - min(min(g.x, g.y), 1.0);
        float fade = exp(-0.05 * t);
        col = mix(col, uGridColor[i].rgb, line * uGridColor[i].a * fade);
    }
    return col;
}
`,
    buildUniforms(overlays) {
        const u = gridUniformDefaults();
        populateGridUniforms(u, overlays);
        return u;
    },
    applyUniforms(u, overlays) {
        populateGridUniforms(u, overlays);
    },
};

function axesUniformDefaults() {
    return {
        uAxesCount: { value: 0 },
        uAxesOrigin: { value: Array.from({ length: MAX_AXES }, () => new THREE.Vector3()) },
        uAxesColorX: { value: Array.from({ length: MAX_AXES }, () => new THREE.Vector3(1, 0, 0)) },
        uAxesColorY: { value: Array.from({ length: MAX_AXES }, () => new THREE.Vector3(0, 1, 0)) },
        uAxesColorZ: { value: Array.from({ length: MAX_AXES }, () => new THREE.Vector3(0, 0, 1)) },
        uAxesOpacity: { value: new Array(MAX_AXES).fill(1.0) },
    };
}

function populateAxesUniforms(u, overlays) {
    const axes = (overlays || []).filter((o) => o.kind === 'axes');
    const n = Math.min(axes.length, MAX_AXES);
    u.uAxesCount.value = n;
    for (let i = 0; i < MAX_AXES; i++) {
        const a = i < n ? axes[i] : null;
        if (a) {
            u.uAxesOrigin.value[i].set(a.origin[0], a.origin[1], a.origin[2]);
            const [rx, gx, bx] = parseHexColor(a.color_x);
            const [ry, gy, by] = parseHexColor(a.color_y);
            const [rz, gz, bz] = parseHexColor(a.color_z);
            u.uAxesColorX.value[i].set(rx, gx, bx);
            u.uAxesColorY.value[i].set(ry, gy, by);
            u.uAxesColorZ.value[i].set(rz, gz, bz);
            u.uAxesOpacity.value[i] = typeof a.opacity === 'number' ? a.opacity : 1.0;
        } else {
            u.uAxesOrigin.value[i].set(0, 0, 0);
            u.uAxesColorX.value[i].set(1, 0, 0);
            u.uAxesColorY.value[i].set(0, 1, 0);
            u.uAxesColorZ.value[i].set(0, 0, 1);
            u.uAxesOpacity.value[i] = 1.0;
        }
    }
}

const axes = {
    kind: 'axes',
    applyFn: 'applyAxes',
    src: `
const int MAX_AXES = ${MAX_AXES};
uniform int uAxesCount;
uniform vec3 uAxesOrigin[MAX_AXES];
uniform vec3 uAxesColorX[MAX_AXES];
uniform vec3 uAxesColorY[MAX_AXES];
uniform vec3 uAxesColorZ[MAX_AXES];
uniform float uAxesOpacity[MAX_AXES];
const float AXIS_LINE_HALF_WIDTH = 1.5;

vec3 applyAxis(vec3 col, vec3 ro, vec3 rd, float tHit, bool hit, float maxDist,
               vec3 O, vec3 d, vec3 color, float opacity) {
    vec3 w0 = ro - O;
    float b = dot(rd, d);
    float d1 = dot(rd, w0);
    float d2 = dot(d, w0);
    float denom = 1.0 - b * b;
    float s;
    float dist;
    if (abs(denom) > 1e-6) {
        float t = (d2 - b * d1) / denom;
        s = (b * d2 - d1) / denom;
        if (t < 0.0) {
            // Closest full-line point is on the negative side: the nearest
            // point of the positive ray is the origin.
            s = max(0.0, -d1);
            dist = length(ro + rd * s - O);
        } else {
            dist = length(ro + rd * s - (O + d * t));
        }
    } else {
        // Parallel: the camera ray's distance to the line is constant.
        dist = length(cross(w0, d));
        s = -d1;
    }
    if (s < 0.0) return col;
    float limit = hit ? tHit : maxDist;
    if (s > limit) return col;
    // Screen-space line width in pixels. Use the Euclidean screen gradient
    // (length of dFdx/dFdy) rather than fwidth's |dx|+|dy|, which over-weights
    // diagonals, so the width is independent of the line's screen orientation;
    // a ~3px smooth falloff keeps shallow (near-horizontal/vertical) lines from
    // aliasing into a dashed pattern.
    float px = length(vec2(dFdx(dist), dFdy(dist)));
    float distPx = dist / max(px, 1e-6);
    float line = 1.0 - smoothstep(0.0, AXIS_LINE_HALF_WIDTH, distPx);
    return mix(col, color, line * opacity);
}

vec3 applyAxes(vec3 col, vec3 ro, vec3 rd, float tHit, bool hit, float maxDist) {
    for (int i = 0; i < MAX_AXES; i++) {
        if (i >= uAxesCount) break;
        vec3 O = uAxesOrigin[i];
        float opacity = uAxesOpacity[i];
        col = applyAxis(col, ro, rd, tHit, hit, maxDist, O, vec3(1.0, 0.0, 0.0), uAxesColorX[i], opacity);
        col = applyAxis(col, ro, rd, tHit, hit, maxDist, O, vec3(0.0, 1.0, 0.0), uAxesColorY[i], opacity);
        col = applyAxis(col, ro, rd, tHit, hit, maxDist, O, vec3(0.0, 0.0, 1.0), uAxesColorZ[i], opacity);
    }
    return col;
}
`,
    buildUniforms(overlays) {
        const u = axesUniformDefaults();
        populateAxesUniforms(u, overlays);
        return u;
    },
    applyUniforms(u, overlays) {
        populateAxesUniforms(u, overlays);
    },
};

const REGISTRY = [grid, axes];

export function overlaySrc() {
    const body = REGISTRY.map((r) => r.src).join('\n');
    const calls = REGISTRY.map(
        (r) => `    col = ${r.applyFn}(col, ro, rd, tHit, hit, maxDist);`
    ).join('\n');
    const dispatcher = [
        'vec3 applyOverlays(vec3 col, vec3 ro, vec3 rd, float tHit, bool hit, float maxDist) {',
        calls,
        '    return col;',
        '}',
    ].join('\n');
    return body + '\n' + dispatcher;
}

export function buildOverlayUniforms(overlays) {
    const uniforms = {};
    for (const r of REGISTRY) {
        Object.assign(uniforms, r.buildUniforms(overlays));
    }
    return uniforms;
}

export function applyOverlayUniforms(u, overlays) {
    for (const r of REGISTRY) {
        r.applyUniforms(u, overlays);
    }
}
