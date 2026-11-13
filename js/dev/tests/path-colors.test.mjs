// Tanga — unit tests for the pure path-color helpers (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import { hasExplicitPathColors, pathColorChangeNeedsColorUpdate } from '../../../py/pytanga/viz/templates/renderers/path-colors.js';

test('hasExplicitPathColors detects per-point and per-segment colors', () => {
    assert.equal(hasExplicitPathColors({}), false);
    assert.equal(hasExplicitPathColors({ colors: [null, null] }), false);
    assert.equal(hasExplicitPathColors({ colors: [null, '#ff0000'] }), true);
    assert.equal(hasExplicitPathColors({ segmentColors: [null, '#00ff00'] }), true);
});

test('pathColorChangeNeedsColorUpdate flags base color change on colored paths', () => {
    const prev = { style: { color: '#ff0000' }, colors: [null, '#ff0000'], segmentColors: [] };
    const ent = { style: { color: '#00ff00' }, colors: [null, '#ff0000'], segmentColors: [] };
    assert.equal(pathColorChangeNeedsColorUpdate(ent, prev), true);
});

test('pathColorChangeNeedsColorUpdate ignores uniform paths', () => {
    const prev = { style: { color: '#ff0000' }, colors: [null, null], segmentColors: [] };
    const ent = { style: { color: '#00ff00' }, colors: [null, null], segmentColors: [] };
    assert.equal(pathColorChangeNeedsColorUpdate(ent, prev), false);
});

test('pathColorChangeNeedsColorUpdate flags color-array changes', () => {
    const prev = { style: { color: '#ff0000' }, colors: ['#ff0000'], segmentColors: [] };
    const ent = { style: { color: '#ff0000' }, colors: ['#00ff00'], segmentColors: [] };
    assert.equal(pathColorChangeNeedsColorUpdate(ent, prev), true);
});

test('pathColorChangeNeedsColorUpdate flags segment-array changes', () => {
    const prev = { style: { color: '#ff0000' }, colors: [], segmentColors: ['#ff0000'] };
    const ent = { style: { color: '#ff0000' }, colors: [], segmentColors: ['#00ff00'] };
    assert.equal(pathColorChangeNeedsColorUpdate(ent, prev), true);
});

test('pathColorChangeNeedsColorUpdate ignores unchanged colored path', () => {
    const prev = { style: { color: '#ff0000' }, colors: ['#ff0000'], segmentColors: [] };
    const ent = { style: { color: '#ff0000' }, colors: ['#ff0000'], segmentColors: [] };
    assert.equal(pathColorChangeNeedsColorUpdate(ent, prev), false);
});
