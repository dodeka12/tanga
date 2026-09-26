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

// Pick the finest pyramid level whose long side is <= `maxDim` pixels (the
// largest dimension of the level's own grid, not the full-resolution source).
// Level 0 is full resolution; each level halves the dimensions (ceil).
export function bestPyramidLevel(pyramid, maxDim = 2048) {
    const levels = pyramid.levels || 1;
    let level = 0;
    let w = pyramid.width;
    let h = pyramid.height;
    while (level + 1 < levels && Math.max(w, h) > maxDim) {
        level++;
        w = Math.ceil(w / 2);
        h = Math.ceil(h / 2);
    }
    return level;
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
