// Tanga — unit tests for the multi-layer image GLSL builders (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import {
    buildImageColorPipeline,
    buildImageFragment,
    buildImageLayerPipeline,
    buildImageVertex,
} from '../../../py/pytanga/viz/templates/renderers/image-shader.js';

function bracesBalanced(src) {
    let depth = 0;
    for (const ch of src) {
        if (ch === '{') depth += 1;
        else if (ch === '}') depth -= 1;
        if (depth < 0) return false;
    }
    return depth === 0;
}

test('fragment declares four samplers and per-layer uniforms', () => {
    const fragment = buildImageFragment();
    for (let i = 0; i < 4; i++) {
        assert.ok(fragment.includes(`uniform sampler2D uImage${i}`));
        assert.ok(fragment.includes(`uniform int u_layer${i}_enabled`));
        assert.ok(fragment.includes(`uniform float u_layer${i}_opacity`));
        assert.ok(fragment.includes(`uniform int u_layer${i}_blend`));
        assert.ok(fragment.includes(`uniform int u_layer${i}_mode`));
        assert.ok(fragment.includes(`uniform float u_layer${i}_value_min`));
        assert.ok(fragment.includes(`uniform float u_layer${i}_value_max`));
    }
    assert.ok(fragment.includes('tangaComposite(vUv, color, alpha)'));
    assert.ok(fragment.includes('gl_FragColor = vec4(color, alpha)'));
    assert.ok(bracesBalanced(fragment));
});

test('fragment has exactly one main function', () => {
    const fragment = buildImageFragment();
    assert.equal(fragment.match(/void main\s*\(/g).length, 1);
});

test('layer pipeline declares global adjustments and per-layer sample/blend', () => {
    const pipeline = buildImageLayerPipeline();
    assert.ok(pipeline.includes('uniform float u_brightness'));
    assert.ok(pipeline.includes('uniform float u_contrast'));
    assert.ok(pipeline.includes('uniform float u_midpoint'));
    assert.ok(pipeline.includes('vec3 tangaSampleLayer(vec4 tex, int chmode, float vmin, float vmax)'));
    assert.ok(pipeline.includes('vec3 tangaBlend(vec3 dst, vec3 src, float alpha, int mode)'));
    // Four blend branches: add, multiply, screen, normal (source-over).
    assert.ok(pipeline.includes('dst + src * alpha'));
    assert.ok(pipeline.includes('dst * src'));
    assert.ok(pipeline.includes('1.0 - (1.0 - dst) * (1.0 - src)'));
    assert.ok(pipeline.includes('mix(dst, src, alpha)'));
});

test('legacy color pipeline is unchanged (background back-compat)', () => {
    const pipeline = buildImageColorPipeline();
    assert.ok(pipeline.includes('vec3 tangaSampleColor(vec4 tex)'));
    assert.ok(pipeline.includes('uniform int u_mode'));
    assert.ok(pipeline.includes('uniform float u_value_min'));
    assert.ok(pipeline.includes('uniform float u_value_max'));
});

test('vertex shader is unchanged', () => {
    const vertex = buildImageVertex();
    assert.ok(vertex.includes('varying vec2 vUv'));
    assert.ok(vertex.includes('projectionMatrix * modelViewMatrix'));
});
