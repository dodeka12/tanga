// Tanga — unit tests for the image-pyramid tile math (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import { pyramidGrid, visibleTiles } from '../../../py/pytanga/viz/templates/renderers/image-tiles.js';

const PYRAMID = { width: 1000, height: 500, tile_size: 256, levels: 11 };

test('pyramidGrid computes level dimensions and tile grid', () => {
    assert.deepEqual(pyramidGrid(PYRAMID, 0), { cols: 4, rows: 2, width: 1000, height: 500 });
    assert.deepEqual(pyramidGrid(PYRAMID, 1), { cols: 2, rows: 1, width: 500, height: 250 });
});

test('visibleTiles covers the full viewport at level 0', () => {
    const tiles = visibleTiles({ u0: 0, v0: 0, u1: 1, v1: 1 }, PYRAMID, 0);
    assert.equal(tiles.length, 4 * 2);
});

test('visibleTiles selects only the intersecting tile', () => {
    const viewport = { u0: 0, v0: 0, u1: 256 / 1000, v1: 256 / 500 };
    assert.deepEqual(visibleTiles(viewport, PYRAMID, 0), [{ level: 0, x: 0, y: 0 }]);
});

test('visibleTiles adds a one-tile border and clamps', () => {
    const viewport = { u0: 0, v0: 0, u1: 256 / 1000, v1: 256 / 500 };
    assert.deepEqual(visibleTiles(viewport, PYRAMID, 0, 1), [
        { level: 0, x: 0, y: 0 },
        { level: 0, x: 1, y: 0 },
        { level: 0, x: 0, y: 1 },
        { level: 0, x: 1, y: 1 },
    ]);
});
