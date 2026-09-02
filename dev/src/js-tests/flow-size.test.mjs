import test from 'node:test';
import assert from 'node:assert/strict';
import {
    flowFlex,
    flexCss,
} from '../../../py/pytanga/viz/templates/views/flow-size.js';

test('flowFlex(null) -> natural (0 1 auto)', () => {
    assert.deepEqual(flowFlex(null), { grow: 0, shrink: 1, basis: 'auto' });
    assert.deepEqual(flowFlex(undefined), { grow: 0, shrink: 1, basis: 'auto' });
});

test('flowFlex(auto) -> natural (0 1 auto)', () => {
    assert.deepEqual(flowFlex({ value: 0, unit: 'auto' }), { grow: 0, shrink: 1, basis: 'auto' });
});

test('flowFlex(fr) -> grow by value (n 1 0)', () => {
    assert.deepEqual(flowFlex({ value: 2, unit: 'fr' }), { grow: 2, shrink: 1, basis: '0' });
});

test('flowFlex(px) -> fixed basis (0 0 <v>px)', () => {
    assert.deepEqual(flowFlex({ value: 200, unit: 'px' }), { grow: 0, shrink: 0, basis: '200px' });
});

test('flowFlex(%) -> fixed basis (0 0 <v>%)', () => {
    assert.deepEqual(flowFlex({ value: 50, unit: '%' }), { grow: 0, shrink: 0, basis: '50%' });
});

test('flexCss assembles the flex shorthand string', () => {
    assert.equal(flexCss(flowFlex(null)), '0 1 auto');
    assert.equal(flexCss(flowFlex({ value: 0, unit: 'auto' })), '0 1 auto');
    assert.equal(flexCss(flowFlex({ value: 2, unit: 'fr' })), '2 1 0');
    assert.equal(flexCss(flowFlex({ value: 200, unit: 'px' })), '0 0 200px');
    assert.equal(flexCss(flowFlex({ value: 50, unit: '%' })), '0 0 50%');
});
