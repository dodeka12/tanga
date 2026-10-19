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

// Per-layer compositing pipeline shared by the image plane and the background
// quad.  It declares the four texture samplers, the per-layer uniforms, the
// shared brightness/contrast/midpoint uniforms, and the helpers that sample a
// layer (`tangaSampleLayer`), blend one layer over another (`tangaBlend`), and
// composite every enabled layer bottom-up (`tangaComposite`).
export function buildImageLayerPipeline() {
    const samplers = [];
    const decls = [];
    const steps = [];
    for (let i = 0; i < 4; i++) {
        samplers.push(`uniform sampler2D uImage${i};`);
        decls.push(layerUniformDecl(i));
        steps.push(layerComposite(i));
    }
    return /* glsl */ `
${samplers.join('\n')}
${decls.join('')}
uniform float u_brightness;
uniform float u_contrast;
uniform float u_midpoint;

vec3 tangaSampleLayer(vec4 tex, int chmode, float vmin, float vmax) {
    vec3 color;
    if (chmode == 0) {
        color = vec3(tex.r);            // channel 1 as grayscale
    } else if (chmode == 2) {
        color = vec3(length(tex.rgb));  // magnitude of channels 1-3
    } else if (chmode == 3) {
        color = vec3(tex.a);            // channel 4 as grayscale
    } else {
        color = tex.rgb;                // RGB
    }

    vec3 n = (color - vmin) / max(vmax - vmin, 1e-6);
    return clamp((n - u_midpoint) * u_contrast + u_midpoint + u_brightness, 0.0, 1.0);
}

vec3 tangaBlend(vec3 dst, vec3 src, float alpha, int mode) {
    if (mode == 1) {
        return dst + src * alpha;                        // add
    } else if (mode == 2) {
        return mix(dst, dst * src, alpha);               // multiply
    } else if (mode == 3) {
        return mix(dst, 1.0 - (1.0 - dst) * (1.0 - src), alpha);  // screen
    }
    return mix(dst, src, alpha);                         // normal (source-over)
}

void tangaComposite(vec2 uv, out vec3 color, out float alpha) {
    vec3 acc = vec3(0.0);
    float accA = 0.0;
${steps.join('')}
    color = acc;
    alpha = accA;
}`;
}

function layerUniformDecl(i) {
    return `
uniform int u_layer${i}_enabled;
uniform float u_layer${i}_opacity;
uniform int u_layer${i}_blend;
uniform int u_layer${i}_mode;
uniform float u_layer${i}_value_min;
uniform float u_layer${i}_value_max;`;
}

function layerComposite(i) {
    const sample = `tangaSampleLayer(texture2D(uImage${i}, uv), `
        + `u_layer${i}_mode, u_layer${i}_value_min, u_layer${i}_value_max)`;
    if (i === 0) {
        return `
    if (u_layer${i}_enabled == 1) {
        acc = ${sample};
        accA = u_layer${i}_opacity;
    }`;
    }
    return `
    if (u_layer${i}_enabled == 1) {
        vec3 c${i} = ${sample};
        acc = accA > 0.0 ? tangaBlend(acc, c${i}, u_layer${i}_opacity, u_layer${i}_blend) : c${i};
        accA = accA > 0.0 ? max(accA, u_layer${i}_opacity) : u_layer${i}_opacity;
    }`;
}

export function buildImageFragment() {
    return /* glsl */ `
precision highp float;
varying vec2 vUv;
${buildImageLayerPipeline()}

void main() {
    // Hardware sampling: mipmapped textures + linear minification give smooth
    // downscaling, and NearestFilter magnification keeps hard 1:1 pixels.
    vec3 color;
    float alpha;
    tangaComposite(vUv, color, alpha);
    gl_FragColor = vec4(color, alpha);
}`;
}
