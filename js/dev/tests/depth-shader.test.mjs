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
