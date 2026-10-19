// Tanga — unit tests for the style-diff rebuild decision (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import { styleNeedsRebuild } from '../../../py/pytanga/viz/templates/renderers/style-diff.js';

test('a surface change requires a rebuild', () => {
    const prev = { style: { color: '#ff0000', surface: { shader: null, textures: [] } } };
    const ent = {
        style: {
            color: '#ff0000',
            surface: { shader: { name: 'checkerboard', fragment: 'x', uniforms: {} }, textures: [] },
        },
    };
    assert.equal(styleNeedsRebuild(ent, prev), true);
});

test('color/opacity changes stay cheap (no rebuild)', () => {
    const prev = { style: { color: '#ff0000', opacity: 1.0, surface: { shader: null, textures: [] } } };
    const ent = { style: { color: '#00ff00', opacity: 0.5, surface: { shader: null, textures: [] } } };
    assert.equal(styleNeedsRebuild(ent, prev), false);
});
