// Tanga Viewer — `ParamsView`: a two-column key-label + control grid.
// Each row renders a title (left) and a child control view (right).  The child
// controls are ordinary control views (built by `build.js`), so their events
// route through the existing `(id, event)` registry.

import { View } from './view.js';
import { stackMinSize, stackPreferredSize } from './stack-size.js';

export class ParamsView extends View {
    constructor({ title = '' } = {}) {
        super();
        this.title = title;
        this.children = [];
        this._rows = [];
        this.el.classList.add('tanga-params-view');
        this._titleEl = document.createElement('div');
        this._titleEl.className = 'tanga-params-title';
        this._setTitle(title);
        this._heightCache = null;
        this._onThemeChange = () => this._invalidateContent();
        if (typeof document !== 'undefined' && typeof document.addEventListener === 'function') {
            document.addEventListener('tanga:themechange', this._onThemeChange);
        }
    }

    _setTitle(title) {
        this.title = title;
        this._titleEl.textContent = title;
        if (title && !this._titleEl.parentNode) {
            this.el.appendChild(this._titleEl);
        } else if (!title && this._titleEl.parentNode) {
            this._titleEl.remove();
        }
    }

    update(node = {}) {
        this._setTitle(node.title ?? this.title);
        this._invalidateContent();
    }

    addRow({ key, title, control }) {
        const row = document.createElement('div');
        row.className = 'tanga-params-row';

        const keyEl = document.createElement('span');
        keyEl.className = 'tanga-params-key';
        keyEl.textContent = title || key;

        const cell = document.createElement('div');
        cell.className = 'tanga-params-control';

        row.appendChild(keyEl);
        row.appendChild(cell);
        this.el.appendChild(row);
        control.mount(cell);

        this._rows.push({ key, title, control, row });
        this.children.push(control);
        this._invalidateContent();
        return control;
    }

    removeChild(view) {
        const idx = this.children.indexOf(view);
        if (idx === -1) return;
        this.children.splice(idx, 1);
        const { row } = this._rows[idx];
        this._rows.splice(idx, 1);
        view.unmount();
        if (row && row.parentNode) row.remove();
        this._invalidateContent();
    }

    // ── content measurement (height only; width is theme-driven) ─

    _invalidateContent() {
        this._heightCache = null;
        this.emit('preferredchange', { fields: ['preferredWidth', 'preferredHeight'] });
        this.emit('constraintschange', { fields: ['minWidth', 'minHeight'] });
    }

    _measureHeight() {
        let height = 0;
        let measurable = false;
        for (const entry of this._rows) {
            const rect = typeof entry.row.getBoundingClientRect === 'function'
                ? entry.row.getBoundingClientRect()
                : null;
            if (rect && rect.height > 0) {
                measurable = true;
                height += rect.height;
            }
        }
        if (!measurable) return null;
        if (this._rows.length > 1) {
            height += (this._rows.length - 1) * this._cssPx('rowGap');
        }
        height += this._titleHeight();
        return Math.round(height);
    }

    _cssPx(prop) {
        const cs = typeof getComputedStyle === 'function' ? getComputedStyle(this.el) : null;
        return cs ? (parseFloat(cs[prop]) || 0) : 0;
    }

    _minWidthPx() {
        const cs = typeof getComputedStyle === 'function' ? getComputedStyle(this.el) : null;
        if (!cs) return 0;
        const px = parseFloat(cs.minWidth);
        return Number.isFinite(px) && px > 0 ? px : 0;
    }

    _titleHeight() {
        if (!this.title) return 0;
        const rect = this._titleEl.getBoundingClientRect();
        const margin = parseFloat(getComputedStyle(this._titleEl).marginBottom) || 0;
        return (rect ? rect.height : 0) + margin;
    }

    _contentHeight() {
        if (this._heightCache != null) return this._heightCache;
        const measured = this._measureHeight();
        this._heightCache = measured;
        return measured;
    }

    // ── sizing ────────────────────────────────────────────────

    minSizePx(axis, available) {
        const explicit = super.minSizePx(axis, available);
        if (explicit > 0) return explicit;
        if (axis === 'x') {
            // The params view stretches to fill its container, so its width is
            // not intrinsic — use the theme's `--tanga-params-min-width` floor.
            const minWidth = this._minWidthPx();
            if (minWidth > 0) return minWidth;
            return stackMinSize('x', 'vertical', this.children, available);
        }
        const height = this._contentHeight();
        if (height != null) return height;
        return stackMinSize('y', 'vertical', this.children, available);
    }

    preferredPx(axis, available) {
        const explicit = super.preferredPx(axis, available);
        if (explicit !== null && explicit !== undefined) return explicit;
        if (axis === 'x') return null;  // stretches to fill; no natural width
        const height = this._contentHeight();
        if (height != null) return height;
        return stackPreferredSize('y', 'vertical', this.children, available);
    }

    destroy() {
        if (typeof document !== 'undefined' && typeof document.removeEventListener === 'function') {
            document.removeEventListener('tanga:themechange', this._onThemeChange);
        }
        super.destroy();
    }
}
