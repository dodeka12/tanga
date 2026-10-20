// Tanga — unit tests for the depth-image GLSL builders (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import {
    buildDepthColormap,
    buildDepthFragment,
    buildDepthVertex,
} from '../../../py/pytanga/viz/templates/renderers/depth-shader.js';

test('vertex shader declares depth uniforms and displaces along z', () => {
    const vertex = buildDepthVertex();
    assert.ok(vertex.includes('varying vec2 vUv'));
    assert.ok(vertex.includes('uniform sampler2D uDepth'));
    assert.ok(vertex.includes('uniform vec2 uDepthSize'));
    assert.ok(vertex.includes('varying float vValid'));
    assert.ok(vertex.includes('p.z +='));
    // Depth-mapping uniforms must be snake_case to match the Python/JS keys.
    assert.ok(vertex.includes('uniform float u_depth_scale'));
    assert.ok(vertex.includes('uniform float u_missing_depth'));
    assert.ok(!vertex.includes('uDepthScale'));
});

test('fragment shader declares segmentation uniforms and helper', () => {
    const fragment = buildDepthFragment();
    assert.ok(fragment.includes('uniform sampler2D uSegMask'));
    assert.ok(fragment.includes('uniform float u_seg_scale'));
    assert.ok(fragment.includes('uniform int u_selected_segments[16]'));
    assert.ok(fragment.includes('bool tangaSegmentSelected(vec2 uv)'));
    assert.ok(fragment.includes('* u_seg_scale + 0.5'));
    assert.ok(fragment.includes('discard'));
});

test('colormap declares the depthColormap selector', () => {
    const colormap = buildDepthColormap();
    assert.ok(colormap.includes('vec3 depthColormap(float t, int m)'));
    assert.ok(colormap.includes('_depthViridis'));
    assert.ok(colormap.includes('_depthTurbo'));
});

test('vertex shader computes a world-space surface normal', () => {
    const vertex = buildDepthVertex();
    assert.ok(vertex.includes('varying vec3 vNormal'));
    assert.ok(vertex.includes('varying vec3 vWorldPosition'));
    assert.ok(vertex.includes('uniform vec2 uWorldStep'));
    assert.ok(vertex.includes('normalize(cross(tX, tY))'));
    assert.ok(vertex.includes('vNormal = normalize(mat3(modelMatrix) * n)'));
    assert.ok(vertex.includes('vWorldPosition = (modelMatrix * vec4(p, 1.0)).xyz'));
});

test('vertex shader supports pinhole camera-frame positions', () => {
    const vertex = buildDepthVertex();
    assert.ok(vertex.includes('uniform float u_depth_kind'));
    assert.ok(vertex.includes('uniform float u_fx'));
    assert.ok(vertex.includes('uniform float u_fy'));
    assert.ok(vertex.includes('uniform float u_cx'));
    assert.ok(vertex.includes('uniform float u_cy'));
    assert.ok(vertex.includes('uniform vec2 u_frame_size'));
    assert.ok(vertex.includes('float axialDepthZ(vec2 uvSample, float dSample)'));
    assert.ok(vertex.includes('vec3 pinholeVertex(vec2 uvSample, float z)'));
    // Axial, radial, and inverse depth branches.
    assert.ok(vertex.includes('// Axial depth: d = distance along the optical axis.'));
    assert.ok(vertex.includes('// Radial depth: d = Euclidean distance along the projection ray.'));
    assert.ok(vertex.includes('// Inverse depth: d = 1/Z.'));
    assert.ok(vertex.includes('return (abs(metric) > 1e-9) ? (1.0 / metric) : u_depth_max;'));
    // Pinhole depth_min/depth_max are axial metres: clamp the converted Z.
    assert.ok(vertex.includes('clamp(axialDepthZ(snap, d), u_depth_min, u_depth_max)'));
    // The calibration pose is applied as the object transform, not in the shader.
    assert.ok(!vertex.includes('u_camera_to_world'));
    assert.ok(vertex.includes('p = pc;'));
});

test('pinhole vertex math inverts the texture v coordinate to the OpenCV row', () => {
    const vertex = buildDepthVertex();
    // flipY textures sample the top row at v=1, but the camera frame's y axis
    // points down (row 0 at the top); both pinhole sites must invert v.
    assert.ok(vertex.includes('vec2 pixel = vec2(uvSample.x, 1.0 - uvSample.y) * u_frame_size;'));
    assert.ok(!vertex.includes('vec2 pixel = uvSample * u_frame_size;'));
});

test('fragment shader shades plain mode with scene lighting', () => {
    const fragment = buildDepthFragment();
    assert.ok(fragment.includes('uniform int uLightCount'));
    assert.ok(fragment.includes('uniform vec3 uLightDir[MAX_LIGHTS]'));
    assert.ok(fragment.includes('uniform vec3 uLightColor[MAX_LIGHTS]'));
    assert.ok(fragment.includes('uniform vec3 uAmbientColor'));
    assert.ok(fragment.includes('uniform float u_shininess'));
    assert.ok(fragment.includes('uniform vec3 u_specular'));
    assert.ok(fragment.includes('uAmbientColor * u_color'));
    assert.ok(fragment.includes('pow(max(dot(N, H), 0.0), u_shininess)'));
    assert.ok(fragment.includes('gl_FragColor = vec4(ambient + diffuse + specular, u_opacity)'));
});

test('vertex and fragment shaders carry the depth-jump stretch filter', () => {
    const vertex = buildDepthVertex();
    assert.ok(vertex.includes('varying float vStretch'));
    assert.ok(vertex.includes('snap - du'));
    assert.ok(vertex.includes('snap - dv'));
    const fragment = buildDepthFragment();
    assert.ok(fragment.includes('uniform float u_max_stretch'));
    assert.ok(fragment.includes('vStretch > u_max_stretch'));
});
