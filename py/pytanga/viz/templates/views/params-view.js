// Tanga Viewer — `ParamsView`: a two-column key-label + control grid.
// Each row renders a title (left) and a child control view (right).  The child
// controls are ordinary control views (built by `build.js`), so their events
// route through the existing `(id, event)` registry.

import { View } from './view.js';
import { stackMinSize, stackPreferredSize } from './stack-size.js';

export class ParamsView extends View {
    constructor({ title = '', dense = false } = {}) {
        super();
        this.title = title;
        this.children = [];
        this._rows = [];
        this.el.classList.add('tanga-params-view');
        if (dense) this.el.classList.add('tanga-params-dense');
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

    addRow({ key, title, control, full_width = false }) {
        const row = document.createElement('div');
        row.className = 'tanga-params-row';

        const cell = document.createElement('div');
        cell.className = 'tanga-params-control';

        // A nested `GroupView` (it renders its own title) and a `full_width`
        // row (a button/markdown/progress without a key label) span the whole
        // row, so neither gets a separate key element.
        const isGroup = control && control.typeTag === 'group';
        const isFullWidth = full_width || isGroup;
        let keyEl = null;
        if (isFullWidth) {
            row.classList.add('tanga-params-row-group');
            if (isGroup) control.el.classList.add('tanga-group-nested');
        } else {
            keyEl = document.createElement('span');
            keyEl.className = 'tanga-params-key';
            keyEl.textContent = title || key;
            row.appendChild(keyEl);
        }

        row.appendChild(cell);
        this.el.appendChild(row);
        control.mount(cell);

        // Track the child's visibility so a server-driven `control_state
        // {visible}` (which hides the control view) also hides the row's title.
        const syncVisibility = () => this._syncRowVisibility(key);
        control.on('constraintschange', syncVisibility);
        control.on('preferredchange', syncVisibility);

        this._rows.push({ key, title, control, row, keyEl, syncVisibility });
        this.children.push(control);
        this._invalidateContent();
        return control;
    }

    _syncRowVisibility(key) {
        const entry = this._rows.find((r) => r.key === key);
        if (!entry) return;
        const hidden = entry.control.hidden;
        entry.row.style.display = hidden ? 'none' : '';
        this._invalidateContent();
    }

    setRowTitle(key, title) {
        const entry = this._rows.find((r) => r.key === key);
        if (!entry) return;
        entry.title = title;
        if (entry.keyEl) entry.keyEl.textContent = title || key;
        this._invalidateContent();
    }

    removeChild(view) {
        const idx = this.children.indexOf(view);
        if (idx === -1) return;
        this.children.splice(idx, 1);
        const entry = this._rows[idx];
        this._rows.splice(idx, 1);
        view.off('constraintschange', entry.syncVisibility);
        view.off('preferredchange', entry.syncVisibility);
        view.unmount();
        if (entry.row && entry.row.parentNode) entry.row.remove();
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
