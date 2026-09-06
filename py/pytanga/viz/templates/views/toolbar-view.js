// Tanga Viewer — `ToolbarView`: a horizontal `StackView` with a thin border and
// a configurable inner margin (padding).  Sizes to its controls plus the
// border/padding "chrome" (see `_chrome`).

import { Size } from './size.js';
import { View } from './view.js';
import { StackView } from './stack-view.js';
import { stackCrossAxis, stackMinSize, stackPreferredSize } from './stack-size.js';

// Fallback chrome (border-box px per axis) used when the rendered DOM can't be
// measured (fake DOM in tests, or before the first layout).  Derived from the
// default `themes/views/toolbar-view.css` + inline margin:
//   1px border on each side + 6px margin on each side = 14px per axis.
const CHROME_FALLBACK = 14;

/**
 * A horizontal control toolbar: a bordered row of controls.
 * `direction` is fixed to `"horizontal"`; `margin` is the inner spacing
 * (padding) between the border and the controls; `border` toggles the outline;
 * `gap`/`align`/`justify` come straight from `StackView`.
 */
export class ToolbarView extends StackView {
    constructor({
        direction = 'horizontal',
        margin = null,
        border = true,
        gap = null,
        align = 'center',
        justify = 'start',
        children = [],
    } = {}) {
        super({ direction, gap, align, justify, children: [] });
        this.margin = Size.fromJSON(margin);
        this.border = border;

        this.el.classList.add('tanga-toolbar');
        if (border === false) this.el.classList.add('tanga-toolbar-borderless');
        this._applyMargin();

        // The cross axis (height) tracks the tallest rendered child rather than
        // the controls' min-height floors, so icon-only toolbars stay compact
        // and taller controls (dropdowns, sliders) don't overflow the chrome.
        this._contentHeightCache = null;
        this._contentObserver = null;
        this._onThemeChange = () => this._invalidateContent();
        if (typeof document !== 'undefined' && typeof document.addEventListener === 'function') {
            document.addEventListener('tanga:themechange', this._onThemeChange);
        }
        if (typeof ResizeObserver !== 'undefined') {
            this._contentObserver = new ResizeObserver(() => this._remeasureContent());
        }

        for (const child of children) this.addChild(child);
    }

    _applyMargin() {
        if (this.margin == null) return;
        const unit = this.margin.unit === '%' ? '%' : 'px';
        this.el.style.padding = `${this.margin.value}${unit}`;
    }

    // Measured padding + border along each axis (border-box px).  Falls back to
    // a constant when the DOM can't be measured (fake DOM in tests).
    _chrome() {
        const cs = typeof getComputedStyle === 'function' ? getComputedStyle(this.el) : null;
        if (!cs) return { x: CHROME_FALLBACK, y: CHROME_FALLBACK };
        const x = (parseFloat(cs.paddingLeft) || 0)
            + (parseFloat(cs.paddingRight) || 0)
            + (parseFloat(cs.borderLeftWidth) || 0)
            + (parseFloat(cs.borderRightWidth) || 0);
        const y = (parseFloat(cs.paddingTop) || 0)
            + (parseFloat(cs.paddingBottom) || 0)
            + (parseFloat(cs.borderTopWidth) || 0)
            + (parseFloat(cs.borderBottomWidth) || 0);
        return { x: Math.round(x), y: Math.round(y) };
    }

    // An explicit min/preferred describes the whole toolbar (chrome included),
    // so it is returned unchanged; otherwise the derived content size is bumped
    // by the border/padding on both axes.  The cross axis uses the measured
    // content height so the toolbar hugs its tallest control.
    minSizePx(axis, available) {
        const explicit = View.prototype.minSizePx.call(this, axis, available);
        const contentMin = axis === stackCrossAxis(this.direction)
            ? this._contentHeight(available)
            : stackMinSize(axis, this.direction, this.children, available);
        return Math.max(explicit, contentMin + this._chrome()[axis]);
    }

    preferredPx(axis, available) {
        const explicit = View.prototype.preferredPx.call(this, axis, available);
        if (explicit !== null && explicit !== undefined) return explicit;
        const contentPref = axis === stackCrossAxis(this.direction)
            ? this._contentHeight(available)
            : stackPreferredSize(axis, this.direction, this.children, available);
        return contentPref === null || contentPref === undefined
            ? null
            : contentPref + this._chrome()[axis];
    }

    // Fix the cross axis (height for a horizontal toolbar) to its natural
    // content height unless an explicit max is set.  This makes the toolbar a
    // fixed-height pane, so a vertical split collapses it to the toolbar's
    // height instead of stretching it.  The main axis stays unbounded so the
    // toolbar can still fill its pane horizontally.
    maxSizePx(axis, available) {
        const explicit = View.prototype.maxSizePx.call(this, axis, available);
        if (explicit !== null && explicit !== undefined) return explicit;
        if (axis === stackCrossAxis(this.direction)) {
            return this.minSizePx(axis, available);
        }
        return null;
    }

    // ── cross-axis content measurement ─────────────────────────

    // Measure the tallest child's rendered height (border-box px) along the
    // cross axis, or `null` when the DOM isn't measurable (fake DOM in tests,
    // or no laid-out children yet).
    _measureContent() {
        let max = 0;
        let measurable = false;
        for (const child of this.children) {
            const el = child.el;
            if (!el || typeof el.getBoundingClientRect !== 'function') continue;
            const rect = el.getBoundingClientRect();
            if (rect && rect.height > 0) {
                measurable = true;
                max = Math.max(max, rect.height);
            }
        }
        return measurable ? Math.round(max) : null;
    }

    // Cross-axis content height — the measured tallest child where possible,
    // otherwise the pure stack min (max of the children's min floors).  Cached;
    // invalidated on child add/remove/resize and theme change.
    _contentHeight(available) {
        if (this._contentHeightCache != null) return this._contentHeightCache;
        const measured = this._measureContent();
        this._contentHeightCache = measured !== null
            ? measured
            : stackMinSize(stackCrossAxis(this.direction), this.direction, this.children, available);
        return this._contentHeightCache;
    }

    // A child resized — drop the cached height and tell enclosing containers to
    // re-layout so they pick up the new value.
    _remeasureContent() {
        if (this._contentHeightCache == null) return;
        this._invalidateContent();
    }

    _invalidateContent() {
        this._contentHeightCache = null;
        this.emit('preferredchange', { fields: ['preferredWidth', 'preferredHeight'] });
        this.emit('constraintschange', { fields: ['minWidth', 'minHeight', 'maxWidth', 'maxHeight'] });
    }

    addChild(view) {
        this._contentHeightCache = null;
        const added = super.addChild(view);
        if (this._contentObserver && added.el) this._contentObserver.observe(added.el);
        this.emit('constraintschange', { fields: ['minWidth', 'minHeight', 'maxWidth', 'maxHeight'] });
        return added;
    }

    removeChild(view) {
        this._contentHeightCache = null;
        if (this._contentObserver && view.el) this._contentObserver.unobserve(view.el);
        super.removeChild(view);
        this.emit('constraintschange', { fields: ['minWidth', 'minHeight', 'maxWidth', 'maxHeight'] });
    }

    destroy() {
        if (this._contentObserver) this._contentObserver.disconnect();
        if (typeof document !== 'undefined' && typeof document.removeEventListener === 'function') {
            document.removeEventListener('tanga:themechange', this._onThemeChange);
        }
        super.destroy();
    }
}
