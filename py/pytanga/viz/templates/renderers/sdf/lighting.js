// Shared SDF lighting model (directional lights + ambient) used by both the
// fullscreen SDF viewer and the standard viewer's per-object SDF proxies, so
// both share one source of truth for the light preamble and uniform uploads.
//
// Pure module (no three.js / DOM): the light preamble is a GLSL string and the
// uniform setters operate on whatever uniform objects the caller supplies.

export const MAX_LIGHTS = 8;

// Frontend defaults mirror the Python defaults (a white light from (10,20,10)
// at intensity 0.8 plus a white 0.45 ambient).
export const DEFAULT_LIGHTING = {
    ambient: { color: '#ffffff', intensity: 0.45 },
    lights: [{ direction: [10, 20, 10], color: '#ffffff', intensity: 0.8 }],
};

// Declared as a JS template so `MAX_LIGHTS` has a single source of truth, then
// injected into the assembled fragment before the raymarch body.
export const lightPreamble = `
const int MAX_LIGHTS = ${MAX_LIGHTS};
uniform int uLightCount;
uniform vec3 uLightDir[MAX_LIGHTS];
uniform vec3 uLightColor[MAX_LIGHTS];
uniform vec3 uAmbientColor;
`;

export function parseHexColor(hex, fallback = [0.7, 0.6, 0.5]) {
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

export function parseAmbient(a) {
    const [r, g, b] = parseHexColor(a && a.color);
    const i = a && typeof a.intensity === 'number' ? a.intensity : 1.0;
    return [r * i, g * i, b * i];
}

export function parseLight(l) {
    const [r, g, b] = parseHexColor(l && l.color);
    const i = l && typeof l.intensity === 'number' ? l.intensity : 1.0;
    let d = (l && l.direction) || [0, 0, 1];
    const len = Math.hypot(d[0], d[1], d[2]);
    d = len > 1e-9 ? [d[0] / len, d[1] / len, d[2] / len] : [0, 0, 1];
    return { direction: d, color: [r * i, g * i, b * i] };
}

export function parseLighting(wire) {
    return {
        ambient: parseAmbient((wire && wire.ambient) || DEFAULT_LIGHTING.ambient),
        lights: ((wire && wire.lights) || DEFAULT_LIGHTING.lights).map(parseLight),
    };
}

export function setLightUniforms(u, lighting) {
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
