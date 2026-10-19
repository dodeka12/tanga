// Tanga — unit tests for the surface shader GLSL assembly (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import {
    buildSurfaceFragment,
    buildSurfaceVertex,
    buildStandardTextureSurfaceColor,
} from '../../../py/pytanga/viz/templates/renderers/surface-shader.js';

test('surface vertex shader exposes the documented varyings', () => {
    const vs = buildSurfaceVertex();
    for (const name of ['vUv', 'vNormal', 'vWorldPosition', 'vLocalPos']) {
        assert.ok(vs.includes(name), `vertex shader should expose ${name}`);
    }
});

test('surface fragment injects lighting preamble and user body with one main()', () => {
    const fs = buildSurfaceFragment({ userFragment: 'vec3 c = u_color;' });
    assert.ok(fs.includes('uLightCount'), 'should declare the scene-lighting uniforms');
    assert.ok(fs.includes('uAmbientColor'), 'should declare the ambient light uniform');
    assert.ok(fs.includes('vec3 c = u_color;'), 'should inject the user fragment');
    assert.ok(fs.includes('tangaLight'), 'should provide the tangaLight helper');
    assert.equal((fs.match(/void main\(\)/g) || []).length, 1);
});

test('standard texture surface color lights the albedo', () => {
    const body = buildStandardTextureSurfaceColor();
    assert.ok(body.includes('tangaLight(baseColor, n, p)'));
});

test('standard texture map samples the first texture sampler', () => {
    const fs = buildSurfaceFragment({
        textureSamplers: ['uTexture'],
        sampleTexture: 'uTexture',
    });
    assert.ok(fs.includes('uniform sampler2D uTexture;'));
    assert.ok(fs.includes('texture2D(uTexture, vUv).rgb'));
});
