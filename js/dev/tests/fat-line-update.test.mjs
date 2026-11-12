// Tanga — unit tests for the pure fat-line rewrite helper (node --test).

import test from 'node:test';
import assert from 'node:assert/strict';

import { rewriteFatLinePositions } from '../../../py/pytanga/viz/templates/renderers/fat-line-update.js';

/**
 * Build a fake LineSegmentsGeometry that records the rewrite call order.
 *
 * @param {{count?: number, instanceCount?: number}} [options]
 * @returns {object}
 */
function fakeGeometry({ count = 0, instanceCount = Infinity } = {}) {
    const calls = [];
    return {
        calls,
        attributes: { instanceStart: { count } },
        instanceCount,
        dispose() {
            calls.push('dispose');
        },
        setPositions(positions) {
            calls.push('setPositions');
            this.attributes.instanceStart.count = positions.length / 6;
        },
    };
}

/**
 * Build a flat list of `segments` start/end vertex pairs.
 *
 * @param {number} segments
 * @returns {Float32Array}
 */
function positionsFor(segments) {
    return new Float32Array(segments * 6);
}

test('growing a fat line disposes before rewriting so the cached bound resets', () => {
    const geometry = fakeGeometry({ count: 1 });

    rewriteFatLinePositions(geometry, positionsFor(2));

    assert.deepEqual(geometry.calls, ['dispose', 'setPositions']);
    assert.equal(geometry.attributes.instanceStart.count, 2);
    assert.equal(geometry.instanceCount, 2);
});

test('same-size rewrite does not dispose', () => {
    const geometry = fakeGeometry({ count: 3 });

    rewriteFatLinePositions(geometry, positionsFor(3));

    assert.deepEqual(geometry.calls, ['setPositions']);
    assert.equal(geometry.instanceCount, 3);
});

test('shrinking rewrite does not dispose and lowers the draw bound', () => {
    const geometry = fakeGeometry({ count: 5 });

    rewriteFatLinePositions(geometry, positionsFor(2));

    assert.deepEqual(geometry.calls, ['setPositions']);
    assert.equal(geometry.instanceCount, 2);
});

test('missing instance attributes count as an empty geometry', () => {
    const calls = [];
    const geometry = {
        attributes: undefined,
        instanceCount: Infinity,
        dispose() {
            calls.push('dispose');
        },
        setPositions() {
            calls.push('setPositions');
        },
    };

    rewriteFatLinePositions(geometry, positionsFor(1));

    assert.deepEqual(calls, ['dispose', 'setPositions']);
    assert.equal(geometry.instanceCount, 1);
});
