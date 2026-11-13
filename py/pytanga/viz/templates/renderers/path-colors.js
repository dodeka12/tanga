// Tanga Viewer — pure per-path color helpers (no THREE import).
// Decides when a PointPath has explicit per-point or per-segment colors, and
// whether a style-only color change must rewrite the vertex color attribute.

/** True when `ent.colors` or `ent.segmentColors` has a real (non-null) entry. */
export function hasExplicitPathColors(ent) {
    return (ent.colors || []).some((c) => c !== null && c !== undefined)
        || (ent.segmentColors || []).some((c) => c !== null && c !== undefined);
}

/**
 * True when a colored path's vertex-color attribute must be rewritten in place
 * instead of going through the generic material-color path: the uniform
 * fallback color changed, or the explicit color arrays changed while both
 * entities stayed colored.
 */
export function pathColorChangeNeedsColorUpdate(ent, prev) {
    if (!ent || !prev) return false;
    if (!hasExplicitPathColors(ent) || !hasExplicitPathColors(prev)) return false;
    const newColor = ent.style ? ent.style.color : undefined;
    const oldColor = prev.style ? prev.style.color : undefined;
    if (newColor !== oldColor) return true;
    if (JSON.stringify(ent.colors || []) !== JSON.stringify(prev.colors || [])) return true;
    if (JSON.stringify(ent.segmentColors || []) !== JSON.stringify(prev.segmentColors || [])) return true;
    return false;
}

/**
 * Merge a content update into the previous entity dict.
 *
 * A `PointPath` whose update omits `segmentColors` is uniform again: the list is
 * reset to `[]` so the stale, previously-coloured list is not inherited through
 * the `{ ...prev, ...content }` merge.
 */
export function mergeEntityContent(prev, content) {
    const merged = { ...prev, ...content };
    if (merged.kind === 'PointPath' && content.segmentColors == null) {
        merged.segmentColors = [];
    }
    return merged;
}
