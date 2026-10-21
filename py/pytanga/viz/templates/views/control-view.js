// Tanga Viewer — `ControlView` base: a single HTML control rendered as a `View`
// (no scene, no Three.js).  Subclasses fill `render()` with the control element.

import { View } from './view.js';

export class ControlView extends View {
    constructor({ id, label = '', tooltip = '', hide_label = false } = {}) {
        super();
        this.controlId = id;
        this.label = label;
        this.tooltip = tooltip;
        this.hide_label = hide_label;
        this.el.classList.add('tanga-control-view');
        // Density floors live in CSS (`.tanga-control-view` min-width/min-height),
        // not here, so a theme can re-size controls.  `build.js` still applies any
        // explicit `min_width`/`min_height` serialized from Python.
    }

    /**
     * A control's minimum size is its theme-driven CSS floor (`.tanga-control-view`
     * `min-width`/`min-height`) unless the view carries an explicit `min_*`.
     * Reading the computed style keeps StackView/GroupView/SplitView able to size
     * to their controls while letting a theme change the density.
     */
    minSizePx(axis, available) {
        if (this._hidden) return 0;
        const explicit = super.minSizePx(axis, available);
        if (explicit > 0) return explicit;
        if (typeof getComputedStyle !== 'function') return 0;
        const prop = axis === 'x' ? 'minWidth' : 'minHeight';
        const px = parseFloat(getComputedStyle(this.el)[prop]);
        return Number.isFinite(px) && px > 0 ? px : 0;
    }

    _onMounted() {
        this.rerender();
    }

    /** Re-render the control in place (idempotent; safe on re-mount). */
    rerender() {
        const el = this.render();
        this.el.replaceChildren(el || []);
    }

    /** Refresh shared fields from a serialized node (used when a view is reused). */
    update(node = {}) {
        this.controlId = node.id ?? this.controlId;
        this.label = node.label ?? this.label;
        this.tooltip = node.tooltip ?? this.tooltip;
        this.hide_label = node.hide_label ?? this.hide_label;
    }

    /** Return the control DOM element (subclass responsibility). */
    render() {
        return null;
    }
}
