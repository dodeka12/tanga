// Tanga Viewer — image-pyramid tile math (pure, Node-testable).
//
// These helpers compute the tiles of a level that intersect a normalized
// viewport.  No browser or three.js imports, so `js/dev/tests` can unit-test
// them directly.

// Grid dimensions of a pyramid level, matching `ImagePyramid.dimensions` /
// `ImagePyramid.grid` on the backend (double ceil: level dims, then tiles).
export function pyramidGrid(pyramid, level) {
    const scale = 2 ** level;
    const levelW = Math.ceil(pyramid.width / scale);
    const levelH = Math.ceil(pyramid.height / scale);
    return {
        cols: Math.ceil(levelW / pyramid.tile_size),
        rows: Math.ceil(levelH / pyramid.tile_size),
        width: levelW,
        height: levelH,
    };
}

// Relative dead-band around a level boundary: a level change is only reported
// once the screen crosses the boundary by this margin, so per-frame jitter at
// the boundary does not oscillate between two levels.
const _HYSTERESIS = 0.02;

// Long side (device pixels) of a pyramid level, matching the `max(nextW, nextH)`
// bound `levelForScreen` compares against the on-screen resolution.
function _levelResolution(pyramid, level) {
    return Math.max(
        Math.ceil(pyramid.width / (2 ** level)),
        Math.ceil(pyramid.height / (2 ** level)),
    );
}

// Pick the pyramid level whose long side best matches a target on-screen
// resolution `screenLongSide` (device pixels on the image's long side, already
// including the device-pixel ratio and the current zoom).  Returns the coarsest
// level whose long side is still >= `screenLongSide`, so the texture is never
// upscaled on screen.  Level 0 is full resolution; each level halves the
// dimensions (ceil).  Falls back to level 0 when `screenLongSide` is not a
// positive number, and clamps to [0, levels-1].
//
// When the optional integer `currentLevel` is given, the result is clamped by a
// ±2% dead-band around the level boundary: a level change is only reported once
// the screen clearly crosses the boundary, which keeps per-frame
// re-resolution from oscillating between two levels at a power-of-two zoom
// boundary (see `updateImageLod`).
export function levelForScreen(pyramid, screenLongSide, currentLevel) {
    const levels = pyramid.levels || 1;
    if (!(Number.isFinite(screenLongSide) && screenLongSide > 0)) return 0;
    // Ideal level (no hysteresis): coarsest level whose long side >= screen size.
    let ideal = 0;
    while (ideal + 1 < levels) {
        if (_levelResolution(pyramid, ideal + 1) < screenLongSide) break;
        ideal++;
    }
    if (!Number.isInteger(currentLevel)) return ideal;
    if (ideal === currentLevel) return ideal;
    if (ideal < currentLevel) {
        // Finer: only once the screen clearly exceeds the current level's resolution.
        const bound = _levelResolution(pyramid, currentLevel) * (1 + _HYSTERESIS);
        return screenLongSide > bound ? ideal : currentLevel;
    }
    // Coarser: only once the screen clearly falls below the new level's resolution.
    const bound = _levelResolution(pyramid, ideal) * (1 - _HYSTERESIS);
    return screenLongSide < bound ? ideal : currentLevel;
}

// Tiles of `level` intersecting a normalized viewport `{u0, v0, u1, v1}`
// (0..1 image coords, v=0 at the top), expanded by `border` tiles and clamped
// to the level's grid.  Returns a sorted array of `{ level, x, y }`.
export function visibleTiles(viewport, pyramid, level, border = 0) {
    const grid = pyramidGrid(pyramid, level);
    const x0 = Math.max(0, viewport.u0 * grid.width);
    const y0 = Math.max(0, viewport.v0 * grid.height);
    const x1 = Math.min(grid.width, viewport.u1 * grid.width);
    const y1 = Math.min(grid.height, viewport.v1 * grid.height);

    const minX = Math.max(0, Math.floor(x0 / pyramid.tile_size) - border);
    const maxX = Math.min(grid.cols - 1, Math.floor((x1 - 1) / pyramid.tile_size) + border);
    const minY = Math.max(0, Math.floor(y0 / pyramid.tile_size) - border);
    const maxY = Math.min(grid.rows - 1, Math.floor((y1 - 1) / pyramid.tile_size) + border);

    const tiles = [];
    for (let y = minY; y <= maxY; y++) {
        for (let x = minX; x <= maxX; x++) {
            tiles.push({ level, x, y });
        }
    }
    return tiles;
}

// Pixel rect (within a level) of one tile, clipped to the level's edge —
// matching `ImagePyramid._extract_tile` on the backend (edge tiles are
// clipped to `min(tile_size, level_dim − coord·tile_size)`).
export function tileRect(pyramid, level, x, y) {
    const grid = pyramidGrid(pyramid, level);
    const x0 = x * pyramid.tile_size;
    const y0 = y * pyramid.tile_size;
    return {
        x0,
        y0,
        w: Math.min(pyramid.tile_size, grid.width - x0),
        h: Math.min(pyramid.tile_size, grid.height - y0),
    };
}
