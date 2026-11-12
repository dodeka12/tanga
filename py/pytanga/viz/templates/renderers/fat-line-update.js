// Tanga Viewer — Pure fat-line update helper (no DOM, no THREE).

/**
 * Rewrite a fat-line geometry's positions and keep its instance draw bound in
 * sync.
 *
 * three.js r168/r170 cache the draw bound in `geometry._maxInstanceCount` on
 * first render and clear it only on dispose.  `setPositions` replaces the
 * attribute buffers but not that cached bound, so growing a path in place would
 * keep drawing only the original segment count.  Dispose before the rewrite
 * when the count grows; pin `instanceCount` because r168 leaves it at Infinity
 * after `setPositions` (r169+ sets it itself).
 *
 * @param {object} geometry - LineSegmentsGeometry/LineGeometry
 * @param {number[]|Float32Array} positions - flat start/end vertex pairs
 */
export function rewriteFatLinePositions(geometry, positions) {
    const count = Math.floor(positions.length / 6);
    const oldCount = geometry.attributes?.instanceStart?.count ?? 0;

    if (count > oldCount) geometry.dispose();

    geometry.setPositions(positions);
    geometry.instanceCount = count;
}
