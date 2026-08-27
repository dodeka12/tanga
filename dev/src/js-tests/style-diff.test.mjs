import test from 'node:test';
import assert from 'node:assert/strict';
import { styleNeedsRebuild } from '../../../py/pytanga/viz/templates/renderers/style-diff.js';

const sphere = () => ({
    style: {
        style_type: 'SphereStyle',
        color: '#4488ff',
        opacity: 0.9,
        wireframe: true,
    },
});

test('identical styles → false', () => {
    assert.equal(styleNeedsRebuild(sphere(), sphere()), false);
});

test('color-only change → false (cheap in-place)', () => {
    const prev = sphere();
    const next = sphere();
    next.style.color = '#ff0000';
    assert.equal(styleNeedsRebuild(next, prev), false);
});

test('opacity-only change → false (cheap in-place)', () => {
    const prev = sphere();
    const next = sphere();
    next.style.opacity = 0.3;
    assert.equal(styleNeedsRebuild(next, prev), false);
});

test('wireframe change → true', () => {
    const prev = sphere();
    const next = sphere();
    next.style.wireframe = false;
    assert.equal(styleNeedsRebuild(next, prev), true);
});

test('per-kind field change (size) → true', () => {
    const prev = { style: { style_type: 'PointStyle', color: '#fff', size: 0.1 } };
    const next = { style: { style_type: 'PointStyle', color: '#fff', size: 0.2 } };
    assert.equal(styleNeedsRebuild(next, prev), true);
});

test('new field added (double_sided) → true', () => {
    const prev = { style: { style_type: 'SphereStyle', color: '#fff' } };
    const next = { style: { style_type: 'SphereStyle', color: '#fff', double_sided: true } };
    assert.equal(styleNeedsRebuild(next, prev), true);
});

test('nested object change (wireframe_dash) → true', () => {
    const prev = { style: { style_type: 'LineStyle', wireframe_dash: { dash_size: 1, gap_size: 1 } } };
    const next = { style: { style_type: 'LineStyle', wireframe_dash: { dash_size: 2, gap_size: 1 } } };
    assert.equal(styleNeedsRebuild(next, prev), true);
});

test('missing prev → false', () => {
    assert.equal(styleNeedsRebuild(sphere(), undefined), false);
    assert.equal(styleNeedsRebuild(sphere(), null), false);
});

test('missing ent → false', () => {
    assert.equal(styleNeedsRebuild(undefined, sphere()), false);
    assert.equal(styleNeedsRebuild(null, sphere()), false);
});

test('style present on one side only → true', () => {
    assert.equal(styleNeedsRebuild({ style: { style_type: 'SphereStyle' } }, {}), true);
    assert.equal(styleNeedsRebuild({}, { style: { style_type: 'SphereStyle' } }), true);
});
