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

// Built-in per-layer color maps (selectable via u_layer{i}_colormap), mirroring
// the depth colormap math in depth-shader.js.
export function buildImageColormap() {
    return /* glsl */ `
vec3 _imageViridis(float t) {
    const vec3 c0 = vec3(0.2777273272234177, 0.005407344544966578, 0.3340998053353061);
    const vec3 c1 = vec3(0.1050930431085774, 1.404613529898575, 1.384590162594685);
    const vec3 c2 = vec3(-0.3308618287255563, 0.214847559468213, 0.09509516302823659);
    const vec3 c3 = vec3(-4.634230498983486, -5.799100973351585, -19.33244095627987);
    const vec3 c4 = vec3(6.228269936347081, 14.17993336680509, 56.69055260068105);
    const vec3 c5 = vec3(4.776384997670288, -13.74514537774601, -65.35303263337234);
    const vec3 c6 = vec3(-5.435455855934631, 4.645852612178535, 26.3124352495832);
    return c0 + t * (c1 + t * (c2 + t * (c3 + t * (c4 + t * (c5 + t * c6)))));
}

vec3 _imageTurbo(float x) {
    const vec4 kRedVec4 = vec4(0.13572138, 4.61539260, -42.66032258, 132.13108234);
    const vec4 kGreenVec4 = vec4(0.09140261, 2.19418839, 4.84296658, -14.18503333);
    const vec4 kBlueVec4 = vec4(0.10667330, 12.64194608, -60.58204836, 110.36276771);
    const vec2 kRedVec2 = vec2(-152.94239396, 59.28637943);
    const vec2 kGreenVec2 = vec2(4.27729857, 2.82956604);
    const vec2 kBlueVec2 = vec2(-89.90310912, 27.34824973);
    vec4 v4 = vec4(1.0, x, x * x, x * x * x);
    vec2 v2 = v4.zw * v4.z;
    return vec3(
        dot(v4, kRedVec4) + dot(v2, kRedVec2),
        dot(v4, kGreenVec4) + dot(v2, kGreenVec2),
        dot(v4, kBlueVec4) + dot(v2, kBlueVec2)
    );
}

vec3 imageColormap(float t, int m) {
    if (m == 1) return _imageViridis(t);
    if (m == 2) return _imageTurbo(t);
    return vec3(t);
}`;
}

// Per-layer compositing pipeline shared by the image plane and the background
// quad.  It declares the four texture samplers, the per-layer uniforms, the
// shared brightness/contrast/midpoint uniforms, and the helpers that sample a
// layer (`tangaSampleLayer`), blend one layer over another (`tangaBlend`), and
// composite every enabled layer bottom-up (`tangaComposite`).
export function buildImageLayerPipeline(layerCount = 8) {
    const samplers = [];
    const decls = [];
    const steps = [];
    for (let i = 0; i < layerCount; i++) {
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

${buildImageColormap()}

vec4 tangaSampleLayer(vec4 tex, int chmode, int colormap, float vmin, float vmax) {
    vec3 color;
    float alpha = 1.0;
    bool scalar = (chmode == 0 || chmode == 2 || chmode == 3);
    if (chmode == 0) {
        color = vec3(tex.r);            // channel 1 as grayscale
    } else if (chmode == 2) {
        color = vec3(length(tex.rgb));  // magnitude of channels 1-3
    } else if (chmode == 3) {
        color = vec3(tex.a);            // channel 4 as grayscale
    } else {
        color = tex.rgb;                // RGB
        alpha = tex.a;                  // 4-channel alpha is respected
    }

    vec3 n;
    if (scalar) {
        float t = (color.r - vmin) / max(vmax - vmin, 1e-6);
        n = imageColormap(clamp(t, 0.0, 1.0), colormap);
    } else {
        n = (color - vmin) / max(vmax - vmin, 1e-6);
    }
    return vec4(clamp((n - u_midpoint) * u_contrast + u_midpoint + u_brightness, 0.0, 1.0), alpha);
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
uniform int u_layer${i}_colormap;
uniform float u_layer${i}_value_min;
uniform float u_layer${i}_value_max;`;
}

function layerComposite(i) {
    const sample = `tangaSampleLayer(texture2D(uImage${i}, uv), `
        + `u_layer${i}_mode, u_layer${i}_colormap, u_layer${i}_value_min, u_layer${i}_value_max)`;
    if (i === 0) {
        return `
    if (u_layer${i}_enabled == 1) {
        vec4 s${i} = ${sample};
        acc = s${i}.rgb;
        accA = u_layer${i}_opacity * s${i}.a;
    }`;
    }
    return `
    if (u_layer${i}_enabled == 1) {
        vec4 s${i} = ${sample};
        vec3 c${i} = s${i}.rgb;
        float a${i} = u_layer${i}_opacity * s${i}.a;
        acc = accA > 0.0 ? tangaBlend(acc, c${i}, a${i}, u_layer${i}_blend) : c${i};
        accA = accA > 0.0 ? max(accA, a${i}) : a${i};
    }`;
}

export function buildImageFragment(layerCount = 8) {
    return /* glsl */ `
precision highp float;
varying vec2 vUv;
${buildImageLayerPipeline(layerCount)}

void main() {
    // Hardware sampling: mipmapped textures + linear minification give smooth
    // downscaling, and NearestFilter magnification keeps hard 1:1 pixels.
    vec3 color;
    float alpha;
    tangaComposite(vUv, color, alpha);
    gl_FragColor = vec4(color, alpha);
}`;
}
