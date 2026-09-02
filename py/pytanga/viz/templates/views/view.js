// Tanga Viewer — `View` base class (split-agnostic rectangular region).
// Tracks the measured extent via a per-instance ResizeObserver, per-axis size
// constraints, and emits events over the native `EventTarget`.

import { Size } from './size.js';
import { ViewEvent } from './view-event.js';

/**
 * Base for every pane/container in a layout.  Knows nothing about splits —
 * only a DOM element, its current extent, and per-axis preferred/min/max sizes.
 *
 * Events (payloads in `event.detail`):
 * - `extentchange`     `{ prev, width, height }`
 * - `constraintschange` `{ fields: [...] }`   (min/max changed)
 * - `preferredchange`   `{ fields: [...] }`   (preferred changed)
 * - `destroy`
 */
export class View extends EventTarget {
    constructor({ el } = {}) {
        super();
        this.el = el || document.createElement('div');
        this.el.classList.add('tanga-view');

        // Per-axis constraints (Size|null).
        this._minWidth = null;
        this._maxWidth = null;
        this._minHeight = null;
        this._maxHeight = null;
        this._prefWidth = null;
        this._prefHeight = null;

        // Measured extent (authoritative: read back from the ResizeObserver).
        this._width = 0;
        this._height = 0;

        this._resizeObserver = new ResizeObserver((entries) => {
            const rect = entries[0] && entries[0].contentRect;
            if (!rect) return;
            this._syncExtent(rect.width, rect.height);
        });
        this._resizeObserver.observe(this.el);
    }

    // ── extent ─────────────────────────────────────────────────

    get width() { return this._width; }
    get height() { return this._height; }
    get extent() { return { width: this._width, height: this._height }; }

    _syncExtent(width, height) {
        if (width === this._width && height === this._height) return;
        const prev = { width: this._width, height: this._height };
        this._width = width;
        this._height = height;
        this._onExtentChanged(width, height);
        this.emit('extentchange', { prev, width, height });
    }

    // ── constraints ────────────────────────────────────────────

    get minWidth() { return this._minWidth; }
    set minWidth(size) { this._setConstraint('_minWidth', size, 'minWidth'); }
    get maxWidth() { return this._maxWidth; }
    set maxWidth(size) { this._setConstraint('_maxWidth', size, 'maxWidth'); }
    get minHeight() { return this._minHeight; }
    set minHeight(size) { this._setConstraint('_minHeight', size, 'minHeight'); }
    get maxHeight() { return this._maxHeight; }
    set maxHeight(size) { this._setConstraint('_maxHeight', size, 'maxHeight'); }
    get preferredWidth() { return this._prefWidth; }
    set preferredWidth(size) { this._setConstraint('_prefWidth', size, 'preferredWidth'); }
    get preferredHeight() { return this._prefHeight; }
    set preferredHeight(size) { this._setConstraint('_prefHeight', size, 'preferredHeight'); }

    _setConstraint(field, size, name) {
        const parsed = Size.fromJSON(size);
        if (this._sameSize(this[field], parsed)) return;
        this[field] = parsed;
        this._applySizeCss(name, parsed);
        const event = name.startsWith('pref') ? 'preferredchange' : 'constraintschange';
        this.emit(event, { fields: [name] });
    }

    // Render min/max size specs as real CSS so they take effect outside a
    // SplitView too (dialogs, overlays, standalone content).  Preferred sizes
    // stay as flex/layout hints and are not forced onto the element here.
    _applySizeCss(name, size) {
        if (!size || size.unit === 'fr' || size.unit === 'auto') return;
        if (!this.el.style) return;
        const value = size.unit === '%' ? (size.value + '%') : (size.value + 'px');
        if (name === 'minWidth') this.el.style.minWidth = value;
        else if (name === 'maxWidth') this.el.style.maxWidth = value;
        else if (name === 'minHeight') this.el.style.minHeight = value;
        else if (name === 'maxHeight') this.el.style.maxHeight = value;
    }

    _sameSize(a, b) {
        if (a === null && b === null) return true;
        if (a === null || b === null) return false;
        return a.equals(b);
    }

    minSizePx(axis, available) {
        const s = axis === 'x' ? this._minWidth : this._minHeight;
        return s ? s.resolve(available, 0) : 0;
    }
    maxSizePx(axis, available) {
        const s = axis === 'x' ? this._maxWidth : this._maxHeight;
        return s ? s.resolve(available, null) : null;
    }
    preferredPx(axis, available) {
        const s = axis === 'x' ? this._prefWidth : this._prefHeight;
        return s ? s.resolve(available, null) : null;
    }

    get fixedX() {
        return this._minWidth !== null && this._maxWidth !== null
            && this._minWidth.equals(this._maxWidth);
    }
    get fixedY() {
        return this._minHeight !== null && this._maxHeight !== null
            && this._minHeight.equals(this._maxHeight);
    }

    // ── lifecycle ──────────────────────────────────────────────

    mount(parentEl) {
        parentEl.appendChild(this.el);
        this._onMounted();
    }

    unmount() { this.el.remove(); }

    destroy() {
        this._resizeObserver.disconnect();
        this.emit('destroy');
    }

    // ── event sugar ────────────────────────────────────────────

    emit(type, detail) {
        return this.dispatchEvent(new ViewEvent(type, detail));
    }

    on(type, handler, options) {
        this.addEventListener(type, handler, options);
        return () => this.removeEventListener(type, handler, options);
    }

    off(type, handler, options) { this.removeEventListener(type, handler, options); }

    // ── subclass hooks ─────────────────────────────────────────

    _onExtentChanged(width, height) {}
    _onMounted() {}
}
