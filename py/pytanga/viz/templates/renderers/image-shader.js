// Image shader — standard vertex/fragment shaders for the image plane.
// Pure GLSL string building (Node-testable).

export function buildImageVertex() {
    return /* glsl */ `
varying vec2 vUv;
void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;
}

export function buildImageFragment() {
    return /* glsl */ `
precision highp float;
varying vec2 vUv;
uniform sampler2D uImage0;
uniform vec2 uImageSize;
uniform float uValueMin;
uniform float uValueMax;
uniform float uBrightness;
uniform float uContrast;
uniform float uMidpoint;
uniform int uMode;

vec4 sampleNearest(vec2 px) {
    vec2 snap = (floor(px) + 0.5) / uImageSize;
    return texture2D(uImage0, snap);
}

// Manual 4-tap bilinear in texel space (the texture itself is nearest-filtered).
vec4 sampleBilinear(vec2 px) {
    vec2 texel = 1.0 / uImageSize;
    vec2 uv = px * texel;
    vec2 st = uv - 0.5 * texel;
    vec2 f = fract(st * uImageSize);
    vec2 i = floor(st * uImageSize);
    vec2 p0 = (i + 0.5) * texel;
    vec2 p1 = p0 + texel;
    vec4 s00 = texture2D(uImage0, p0);
    vec4 s10 = texture2D(uImage0, vec2(p1.x, p0.y));
    vec4 s01 = texture2D(uImage0, vec2(p0.x, p1.y));
    vec4 s11 = texture2D(uImage0, p1);
    return mix(mix(s00, s10, f.x), mix(s01, s11, f.x), f.y);
}

void main() {
    vec2 px = vUv * uImageSize;
    vec2 df = fwidth(px);
    // Axis-aligned (integer zoom / pan) → nearest (hard pixel borders);
    // rotated / non-axis-aligned → bilinear (anti-aliased).
    vec4 tex = (min(df.x, df.y) < 0.5) ? sampleNearest(px) : sampleBilinear(px);

    vec3 color;
    if (uMode == 0) {
        color = vec3(tex.r);            // channel 1 as grayscale
    } else if (uMode == 2) {
        color = vec3(length(tex.rgb));  // magnitude of channels 1-3
    } else if (uMode == 3) {
        color = vec3(tex.a);            // channel 4 as grayscale
    } else {
        color = tex.rgb;                // RGB
    }

    vec3 n = (color - uValueMin) / max(uValueMax - uValueMin, 1e-6);
    vec3 outC = clamp((n - uMidpoint) * uContrast + uMidpoint + uBrightness, 0.0, 1.0);
    gl_FragColor = vec4(outC, 1.0);
}`;
}
