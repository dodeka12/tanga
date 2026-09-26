// Tanga — unit tests for the image-pyramid tile math (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import { bestPyramidLevel, pyramidGrid, tileRect, visibleTiles } from '../../../py/pytanga/viz/templates/renderers/image-tiles.js';

const PYRAMID = { width: 1000, height: 500, tile_size: 256, levels: 11 };

test('bestPyramidLevel keeps a small image at full resolution', () => {
    assert.equal(bestPyramidLevel(PYRAMID), 0);
});

test('bestPyramidLevel picks the first level under the max dimension', () => {
    // 4056 px wide: level 0 = 4056 (> 2048), level 1 = 2028 (<= 2048).
    assert.equal(bestPyramidLevel({ width: 4056, height: 3040, levels: 13 }), 1);
    // 8192 px wide: levels 0..1 are > 2048, level 2 = 2048 (<= 2048).
    assert.equal(bestPyramidLevel({ width: 8192, height: 4096, levels: 14 }), 2);
});

test('bestPyramidLevel never exceeds the last level', () => {
    assert.equal(bestPyramidLevel({ width: 100000, height: 1, levels: 3 }), 2);
});

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

test('tileRect is full-size for interior tiles', () => {
    // PYRAMID 1000×500, tile 256 → level 0 grid 4×2.
    assert.deepEqual(tileRect(PYRAMID, 0, 0, 0), { x0: 0, y0: 0, w: 256, h: 256 });
});

test('tileRect clips the right/bottom edge tiles', () => {
    assert.deepEqual(tileRect(PYRAMID, 0, 3, 1), { x0: 768, y0: 256, w: 232, h: 244 });
});
