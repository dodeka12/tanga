// Tanga Viewer — Split-view `Size` value object (px / % / fr / auto).
// Pure and DOM-free; the Python mirror is `py/pytanga/viz/_size.py`.

const UNITS = ['px', '%', 'fr', 'auto'];

/**
 * An extent along one axis together with a resolution unit.
 *
 * - `px`   — absolute CSS pixels.
 * - `%`    — a fraction of the parent extent along the same axis.
 * - `fr`   — a flexible share (preferred sizes only; no absolute extent).
 * - `auto` — unconstrained (min → 0, max → ∞, preferred → natural).
 */
export class Size {
    constructor(value, unit = 'px') {
        if (!UNITS.includes(unit)) {
            throw new Error(
                `Unknown size unit ${JSON.stringify(unit)}; expected one of ${UNITS.join(', ')}`
            );
        }
        this.value = Number(value);
        this.unit = unit;
    }

    static px(value) { return new Size(value, 'px'); }
    static percent(value) { return new Size(value, '%'); }
    static fr(value) { return new Size(value, 'fr'); }
    static auto() { return new Size(0, 'auto'); }

    /** Parse the canonical JSON shape `{value, unit}` (or a `Size`, or null). */
    static fromJSON(data) {
        if (data === null || data === undefined) return null;
        return new Size(data.value, data.unit ?? 'px');
    }

    toJSON() { return { value: this.value, unit: this.unit }; }

    /**
     * Resolve to CSS px given the parent extent along the axis.  `fr`/`auto`
     * have no absolute extent, so they defer to `natural`.
     */
    resolve(available, natural = null) {
        if (this.unit === 'px') return this.value;
        if (this.unit === '%') return (this.value / 100) * available;
        return natural;
    }

    equals(other) {
        return other !== null && other !== undefined
            && this.value === other.value && this.unit === other.unit;
    }

    clone() { return new Size(this.value, this.unit); }
}
