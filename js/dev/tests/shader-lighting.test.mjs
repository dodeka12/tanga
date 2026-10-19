// Tanga — unit tests for the shared scene-lighting module (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import {
    DEFAULT_LIGHTING,
    MAX_LIGHTS,
    parseLight,
    parseLighting,
    setLightUniforms,
} from '../../../py/pytanga/viz/templates/renderers/shader-lighting.js';

test('DEFAULT_LIGHTING mirrors the Python scene default', () => {
    assert.equal(DEFAULT_LIGHTING.ambient.intensity, 0.5);
    assert.equal(DEFAULT_LIGHTING.lights.length, 2);
    assert.equal(DEFAULT_LIGHTING.lights[0].intensity, 0.8);
    assert.equal(DEFAULT_LIGHTING.lights[1].intensity, 0.3);
});

function _assertCloseVec(actual, expected, eps = 1e-12) {
    assert.equal(actual.length, expected.length);
    for (let i = 0; i < actual.length; i++) {
        assert.ok(
            Math.abs(actual[i] - expected[i]) < eps,
            `${actual[i]} != ${expected[i]} (within ${eps})`,
        );
    }
}

test('parseLighting parses the new wire shape (ambient + two lights)', () => {
    const lighting = parseLighting({
        ambient: { color: '#ffffff', intensity: 0.5 },
        lights: [
            { direction: [10, 20, 10], color: '#ffffff', intensity: 0.8 },
            { direction: [-5, -2, -8], color: '#ffffff', intensity: 0.3 },
        ],
    });
    assert.equal(lighting.lights.length, 2);
    assert.deepEqual(lighting.ambient, [0.5, 0.5, 0.5]);
    // First light: normalize((10,20,10)) with white @ 0.8.
    _assertCloseVec(
        lighting.lights[0].direction,
        [0.408248290463863, 0.816496580927726, 0.408248290463863],
    );
    assert.deepEqual(lighting.lights[0].color, [0.8, 0.8, 0.8]);
});

test('parseLight normalizes a non-unit direction', () => {
    const light = parseLight({ direction: [2, 0, 0], color: '#ffffff', intensity: 1 });
    assert.deepEqual(light.direction, [1, 0, 0]);
});

test('parseLighting defaults to the shared default', () => {
    const lighting = parseLighting(null);
    assert.equal(lighting.lights.length, 2);
    assert.deepEqual(lighting.ambient, [0.5, 0.5, 0.5]);
});

function _makeUniforms() {
    const makeVec = () => ({ _v: [0, 0, 0], set(x, y, z) { this._v = [x, y, z]; } });
    return {
        uLightCount: { value: 0 },
        uLightDir: { value: Array.from({ length: MAX_LIGHTS }, makeVec) },
        uLightColor: { value: Array.from({ length: MAX_LIGHTS }, makeVec) },
        uAmbientColor: { value: makeVec() },
    };
}

test('setLightUniforms writes lights and zeroes unused slots', () => {
    const u = _makeUniforms();
    const lighting = parseLighting({
        ambient: { color: '#ff0000', intensity: 0.5 },
        lights: [{ direction: [0, 1, 0], color: '#00ff00', intensity: 0.25 }],
    });

    setLightUniforms(u, lighting);

    assert.equal(u.uLightCount.value, 1);
    assert.deepEqual(u.uLightDir.value[0]._v, [0, 1, 0]);
    assert.deepEqual(u.uLightColor.value[0]._v, [0, 0.25, 0]);
    assert.deepEqual(u.uAmbientColor.value._v, [0.5, 0, 0]);
    // Unused slots must be zeroed.
    for (let i = 1; i < MAX_LIGHTS; i++) {
        assert.deepEqual(u.uLightDir.value[i]._v, [0, 0, 0]);
        assert.deepEqual(u.uLightColor.value[i]._v, [0, 0, 0]);
    }
});
