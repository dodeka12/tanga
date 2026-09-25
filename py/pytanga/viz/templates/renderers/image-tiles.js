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
