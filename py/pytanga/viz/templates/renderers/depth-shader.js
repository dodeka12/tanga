// Depth image shader — vertex/fragment shaders for the 2.5D depth surface.
// Pure GLSL string building (Node-testable, mirrors image-shader.js).

import { lightPreamble } from './shader-lighting.js';

export function buildDepthVertex() {
    return /* glsl */ `
precision highp float;
varying vec2 vUv;
varying float vDepth;
varying float vValid;
varying vec3 vNormal;
varying vec3 vWorldPosition;

uniform sampler2D uDepth;
uniform vec2 uDepthSize;
uniform vec2 uWorldStep;     // object-space distance between depth samples
uniform float u_depth_scale;  // world units per depth unit (may be negative)
uniform float u_depth_offset; // subtracted from depth before scaling
uniform float u_missing_depth; // sentinel for non-finite depth
uniform float u_depth_min;    // clamp lower bound (also the missing-depth height)
uniform float u_depth_max;    // clamp upper bound
uniform float u_depth_kind;   // 0 = orthographic, 1 = pinhole axial, 2 = pinhole radial, 3 = pinhole inverse
uniform float u_fx;           // pinhole intrinsics (pixels of the reference frame)
uniform float u_fy;
uniform float u_cx;
uniform float u_cy;
uniform vec2 u_frame_size;    // reference (full-resolution) frame

// Raw depth sample → axial depth Z (camera frame, world units), per depth_kind.
float axialDepthZ(vec2 uvSample, float dSample) {
    float metric = (dSample - u_depth_offset) * u_depth_scale;
    if (u_depth_kind > 2.5) {
        // Inverse depth: d = 1/Z.
        return (abs(metric) > 1e-9) ? (1.0 / metric) : u_depth_max;
    }
    if (u_depth_kind > 1.5) {
        // Radial depth: d = Euclidean distance along the projection ray.
        vec2 pixel = uvSample * u_frame_size;
        float xn = (pixel.x - u_cx) / u_fx;
        float yn = (pixel.y - u_cy) / u_fy;
        return metric / sqrt(xn * xn + yn * yn + 1.0);
    }
    // Axial depth: d = distance along the optical axis.
    return metric;
}

// Camera-frame vertex (x right, y down, z forward) from axial depth Z.
vec3 pinholeVertex(vec2 uvSample, float z) {
    vec2 pixel = uvSample * u_frame_size;
    return vec3((pixel.x - u_cx) / u_fx * z, (pixel.y - u_cy) / u_fy * z, z);
}

void main() {
    vUv = uv;
    // Nearest tap at the pixel centre (depth is a nearest-filtered texture).
    vec2 snap = (floor(uv * uDepthSize) + 0.5) / max(uDepthSize, vec2(1.0));
    float d = texture2D(uDepth, snap).r;
    bool missing = (d == u_missing_depth);
    vValid = missing ? 0.0 : 1.0;

    vec2 du = vec2(1.0 / max(uDepthSize.x, 1.0), 0.0);
    vec2 dv = vec2(0.0, 1.0 / max(uDepthSize.y, 1.0));
    float dU = texture2D(uDepth, snap + du).r;
    float dV = texture2D(uDepth, snap + dv).r;
    bool missingU = (dU == u_missing_depth);
    bool missingV = (dV == u_missing_depth);

    vec3 p;
    vec3 n;
    if (u_depth_kind > 0.5) {
        // Pinhole: depth_min/depth_max are axial depth (Z) in world units, so
        // convert the raw sample to Z first, then clamp.
        float zC  = missing  ? u_depth_min : clamp(axialDepthZ(snap, d), u_depth_min, u_depth_max);
        float zCU = missingU ? u_depth_min : clamp(axialDepthZ(snap + du, dU), u_depth_min, u_depth_max);
        float zCV = missingV ? u_depth_min : clamp(axialDepthZ(snap + dv, dV), u_depth_min, u_depth_max);
        vDepth = zC;

        vec3 pc = pinholeVertex(snap, zC);
        vec3 pcU = pinholeVertex(snap + du, zCU);
        vec3 pcV = pinholeVertex(snap + dv, zCV);
        vec3 nCam = normalize(cross(pcU - pc, pcV - pc));
        p = pc;
        n = nCam;
    } else {
        // Orthographic: clamp the raw depth value (legacy heightfield), then
        // apply depth_scale/depth_offset.
        float zC  = missing  ? u_depth_min : clamp(d, u_depth_min, u_depth_max);
        float zCU = missingU ? u_depth_min : clamp(dU, u_depth_min, u_depth_max);
        float zCV = missingV ? u_depth_min : clamp(dV, u_depth_min, u_depth_max);
        vDepth = zC;

        p = position;
        p.z += (zC - u_depth_offset) * u_depth_scale;
        float hC = (zC - u_depth_offset) * u_depth_scale;
        vec3 tX = vec3(uWorldStep.x, 0.0, (zCU - u_depth_offset) * u_depth_scale - hC);
        vec3 tY = vec3(0.0, uWorldStep.y, (zCV - u_depth_offset) * u_depth_scale - hC);
        n = normalize(cross(tX, tY));
    }

    vNormal = normalize(mat3(modelMatrix) * n);
    vWorldPosition = (modelMatrix * vec4(p, 1.0)).xyz;

    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
}`;
}

// Built-in depth color maps (selectable via u_colormap).
export function buildDepthColormap() {
    return /* glsl */ `
vec3 _depthViridis(float t) {
    const vec3 c0 = vec3(0.2777273272234177, 0.005407344544966578, 0.3340998053353061);
    const vec3 c1 = vec3(0.1050930431085774, 1.404613529898575, 1.384590162594685);
    const vec3 c2 = vec3(-0.3308618287255563, 0.214847559468213, 0.09509516302823659);
    const vec3 c3 = vec3(-4.634230498983486, -5.799100973351585, -19.33244095627987);
    const vec3 c4 = vec3(6.228269936347081, 14.17993336680509, 56.69055260068105);
    const vec3 c5 = vec3(4.776384997670288, -13.74514537774601, -65.35303263337234);
    const vec3 c6 = vec3(-5.435455855934631, 4.645852612178535, 26.3124352495832);
    return c0 + t * (c1 + t * (c2 + t * (c3 + t * (c4 + t * (c5 + t * c6)))));
}

vec3 _depthTurbo(float x) {
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

vec3 depthColormap(float t, int m) {
    if (m == 0) return _depthViridis(t);
    if (m == 2) return vec3(t);
    return _depthTurbo(t);
}`;
}

export function buildDepthFragment() {
    return /* glsl */ `
precision highp float;
varying vec2 vUv;
varying float vDepth;
varying float vValid;
varying vec3 vNormal;
varying vec3 vWorldPosition;

uniform sampler2D uDepth;
uniform sampler2D uSegMask;
uniform sampler2D uImage0;
uniform vec2 uDepthSize;
uniform vec2 uSegSize;
uniform vec2 uImageSize;
uniform float u_missing_depth;
uniform float u_depth_min;
uniform float u_depth_max;
uniform int u_render_mode;       // 0 = depth colormap, 1 = image, 2 = plain
uniform int u_colormap;          // 0 = viridis, 1 = turbo, 2 = gray
uniform vec3 u_color;
uniform float u_opacity;
uniform int u_discard_missing;
uniform int u_seg_enabled;
uniform int u_num_selected;
uniform float u_seg_scale;        // 255.0 for uint8, 1.0 for float/uint16
uniform int u_selected_segments[16];
uniform float u_shininess;        // Blinn-Phong specular exponent (plain mode)
uniform vec3 u_specular;          // Blinn-Phong specular color (plain mode)

${lightPreamble}

${buildDepthColormap()}

bool tangaSegmentSelected(vec2 uv) {
    if (u_seg_enabled == 0) return true;
    vec2 snap = (floor(uv * uSegSize) + 0.5) / max(uSegSize, vec2(1.0));
    int id = int(texture2D(uSegMask, snap).r * u_seg_scale + 0.5);
    for (int i = 0; i < 16; i++) {
        if (i >= u_num_selected) break;
        if (u_selected_segments[i] == id) return true;
    }
    return false;
}

void main() {
    // Missing depth -> discard (no color, no depth write).
    if (u_discard_missing == 1 && vValid < 0.5) discard;
    // Segmentation filter -> discard non-selected segments (no depth write).
    if (!tangaSegmentSelected(vUv)) discard;

    if (u_render_mode == 1) {
        vec2 snap = (floor(vUv * uImageSize) + 0.5) / max(uImageSize, vec2(1.0));
        vec3 rgb = texture2D(uImage0, snap).rgb;
        gl_FragColor = vec4(rgb, u_opacity);
    } else if (u_render_mode == 2) {
        // Blinn-Phong (ambient + directional diffuse + specular), world space.
        vec3 N = normalize(vNormal);
        if (!gl_FrontFacing) N = -N;
        vec3 V = normalize(cameraPosition - vWorldPosition);
        vec3 ambient = uAmbientColor * u_color;
        vec3 diffuse = vec3(0.0);
        vec3 specular = vec3(0.0);
        for (int i = 0; i < MAX_LIGHTS; i++) {
            if (i >= uLightCount) break;
            float ndl = max(dot(N, uLightDir[i]), 0.0);
            diffuse += uLightColor[i] * u_color * ndl;
            vec3 H = normalize(uLightDir[i] + V);
            specular += uLightColor[i] * u_specular * pow(max(dot(N, H), 0.0), u_shininess);
        }
        gl_FragColor = vec4(ambient + diffuse + specular, u_opacity);
    } else {
        float t = clamp((vDepth - u_depth_min) / max(u_depth_max - u_depth_min, 1e-6), 0.0, 1.0);
        gl_FragColor = vec4(depthColormap(t, u_colormap), u_opacity);
    }
}`;
}
