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

const REGISTRY = [grid];

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
