// Tanga Viewer — Pure flex mapping for flow containers (no DOM).
// Maps a child's `preferred` size (the `Size` JSON shape `{value, unit}`) to a
// CSS `flex: <grow> <shrink> <basis>` triple, so a flow container (`stack` /
// `group`) can lay children out with flexible sizing and spacing.

/**
 * Map a `Size`-shaped object (`{ value, unit }`) or null/undefined to a CSS
 * flex triple `{ grow, shrink, basis }`.
 *
 * - null/undefined or `auto` -> natural size, may shrink (`0 1 auto`)
 * - `fr`  -> grow to fill leftover, weighted by `value` (`n 1 0`)
 * - `px`  -> fixed basis, no grow/shrink (`0 0 <v>px`)
 * - `%`   -> fixed basis, no grow/shrink (`0 0 <v>%`)
 */
export function flowFlex(sizeSpec) {
    if (sizeSpec == null || sizeSpec.unit === 'auto') {
        return { grow: 0, shrink: 1, basis: 'auto' };
    }
    if (sizeSpec.unit === 'fr') {
        return { grow: sizeSpec.value, shrink: 1, basis: '0' };
    }
    if (sizeSpec.unit === 'px') {
        return { grow: 0, shrink: 0, basis: sizeSpec.value + 'px' };
    }
    if (sizeSpec.unit === '%') {
        return { grow: 0, shrink: 0, basis: sizeSpec.value + '%' };
    }
    // Unknown unit: treat as natural (auto).
    return { grow: 0, shrink: 1, basis: 'auto' };
}

/** Assemble a flex triple into the CSS `flex` shorthand string. */
export function flexCss({ grow, shrink, basis }) {
    return `${grow} ${shrink} ${basis}`;
}
