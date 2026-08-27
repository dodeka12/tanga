// Tanga Viewer — Pure style-diff helper (no DOM, no THREE).
// Decides whether a style change requires rebuilding an entity's mesh rather
// than updating it in place.  Only `color` and `opacity` are cheaply
// applicable in place; any other style field change requires a rebuild so the
// per-kind renderer re-reads every style parameter.

const CHEAP_STYLE_FIELDS = new Set(['color', 'opacity']);

/**
 * Return true when the style of *ent* differs from *prev* in any field other
 * than the cheap, in-place-updatable fields (`color`, `opacity`).
 *
 * `ent.style` and `prev.style` are the resolved style dicts emitted by the
 * serializer; values may be nested objects (e.g. dash patterns, texture
 * labels), so the comparison is a deep JSON equality.
 *
 * @param {object|undefined|null} ent   Merged entity dict (with `.style`).
 * @param {object|undefined|null} prev  Previously applied entity dict.
 * @returns {boolean}
 */
export function styleNeedsRebuild(ent, prev) {
    if (!ent || !prev) return false;
    const newStyle = ent.style || {};
    const oldStyle = prev.style || {};
    const keys = new Set([...Object.keys(newStyle), ...Object.keys(oldStyle)]);
    for (const key of keys) {
        if (CHEAP_STYLE_FIELDS.has(key)) continue;
        const a = JSON.stringify(newStyle[key] ?? null);
        const b = JSON.stringify(oldStyle[key] ?? null);
        if (a !== b) return true;
    }
    return false;
}
