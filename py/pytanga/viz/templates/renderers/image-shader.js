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

// Shared color-processing GLSL: channel-mode mapping → value-range normalize →
// brightness/contrast → clamp.  Declares the standard color uniforms and a
// `tangaSampleColor(vec4)` helper used by both the image plane and the
// background quad.
export function buildImageColorPipeline() {
    return /* glsl */ `
uniform float u_value_min;
uniform float u_value_max;
uniform float u_brightness;
uniform float u_contrast;
uniform float u_midpoint;
uniform int u_mode;

vec3 tangaSampleColor(vec4 tex) {
    vec3 color;
    if (u_mode == 0) {
        color = vec3(tex.r);            // channel 1 as grayscale
    } else if (u_mode == 2) {
        color = vec3(length(tex.rgb));  // magnitude of channels 1-3
    } else if (u_mode == 3) {
        color = vec3(tex.a);            // channel 4 as grayscale
    } else {
        color = tex.rgb;                // RGB
    }

    vec3 n = (color - u_value_min) / max(u_value_max - u_value_min, 1e-6);
    return clamp((n - u_midpoint) * u_contrast + u_midpoint + u_brightness, 0.0, 1.0);
}`;
}

export function buildImageFragment() {
    return /* glsl */ `
precision highp float;
varying vec2 vUv;
uniform sampler2D uImage0;
${buildImageColorPipeline()}

void main() {
    // Hardware sampling: mipmapped textures + linear minification give smooth
    // downscaling, and NearestFilter magnification keeps hard 1:1 pixels.
    vec4 tex = texture2D(uImage0, vUv);
    gl_FragColor = vec4(tangaSampleColor(tex), 1.0);
}`;
}
