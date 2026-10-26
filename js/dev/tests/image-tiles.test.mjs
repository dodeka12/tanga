// Tanga — unit tests for the image-pyramid tile math (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import { levelForScreen, pyramidGrid, tileRect, visibleTiles } from '../../../py/pytanga/viz/templates/renderers/image-tiles.js';

const PYRAMID = { width: 1000, height: 500, tile_size: 256, levels: 11 };

test('levelForScreen keeps a small image at full resolution for a big screen', () => {
    assert.equal(levelForScreen(PYRAMID, 2000), 0);
});

test('levelForScreen picks the coarsest level still >= the screen size', () => {
    // 4056 px wide: screen 2000 → level 1 (2028 >= 2000; level 2 = 1014 < 2000).
    assert.equal(levelForScreen({ width: 4056, height: 3040, levels: 13 }, 2000), 1);
    // screen 3000 → only level 0 (4056) is >= 3000.
    assert.equal(levelForScreen({ width: 4056, height: 3040, levels: 13 }, 3000), 0);
    // 8192 px wide: screen 3000 → level 1 (4096 >= 3000; level 2 = 2048 < 3000).
    assert.equal(levelForScreen({ width: 8192, height: 4096, levels: 14 }, 3000), 1);
});

test('levelForScreen never exceeds the last level', () => {
    assert.equal(levelForScreen({ width: 100000, height: 1, levels: 3 }, 1), 2);
});

test('levelForScreen falls back to full resolution for a non-positive screen', () => {
    assert.equal(levelForScreen(PYRAMID, 0), 0);
    assert.equal(levelForScreen(PYRAMID, undefined), 0);
});

test('levelForScreen hysteresis holds the coarser level at a boundary', () => {
    const P = { width: 4096, height: 2048, levels: 13 };
    // Boundary between level 0 (4096) and level 1 (2048): at 2050 the ideal is
    // level 0, but 2050 < 2048 * 1.05, so the current level 1 is kept.
    assert.equal(levelForScreen(P, 2050, 1), 1);
    // Clearly past the margin → switch to the finer level 0.
    assert.equal(levelForScreen(P, 2200, 1), 0);
});

test('levelForScreen hysteresis holds the finer level at a boundary', () => {
    const P = { width: 4096, height: 2048, levels: 13 };
    // At 2010 the ideal is level 1, but 2010 > 2048 * 0.95, so the current
    // level 0 is kept.
    assert.equal(levelForScreen(P, 2010, 0), 0);
    // Clearly below the margin → switch to the coarser level 1.
    assert.equal(levelForScreen(P, 1900, 0), 1);
});

test('levelForScreen without a current level returns the ideal level', () => {
    const P = { width: 4096, height: 2048, levels: 13 };
    assert.equal(levelForScreen(P, 2050), 0);
    assert.equal(levelForScreen(P, 2010), 1);
});

test('levelForScreen hysteresis still allows a multi-level jump', () => {
    const P = { width: 4096, height: 2048, levels: 13 };
    // 800 is far below the level-1 boundary, so a jump from 0 to 2 is allowed.
    assert.equal(levelForScreen(P, 800, 0), 2);
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
