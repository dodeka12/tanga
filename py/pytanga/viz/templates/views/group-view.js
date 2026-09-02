// Tanga Viewer — `GroupView`: a titled `StackView` (panel chrome) that holds
// control views (or any views). Usable as a split pane or a scene overlay
// (anchored by `position`).

import { Size } from './size.js';
import { View } from './view.js';
import { StackView } from './stack-view.js';
import { stackMainAxis, stackMinSize, stackPreferredSize } from './stack-size.js';
import { createIconElement } from '../controls-panel.js';

// Fallback vertical chrome (border-box px) used when the rendered DOM can't be
// measured (fake DOM in tests, or before the first layout).  Derived from
// `themes/views/group-view.css`:
//   .tanga-group          border 1px + padding 8px on each side (18px total)
//   .tanga-group-header   ~22px content (toggle) + 6px padding-bottom
//                         + 1px border-bottom + 6px margin-bottom (35px total)
// folded = 1 + 8 + (22 + 6 + 1) = 38   (pane ends at the title bar's bottom border)
// chrome = 2 + 16 + 29 + 6      = 53   (full shell + header + its margin)
const FOLDED_FALLBACK = 38;
const CHROME_FALLBACK = 53;

export class GroupView extends StackView {
    constructor({
        title = '',
        direction = 'vertical',
        position = null,
        collapsed = false,
        scrollable = false,
        gap = null,
        align = 'stretch',
        justify = 'start',
        icon = null,
        icon_only = false,
        parent_id = null,
        id = null,
        children = [],
    } = {}) {
        super({ direction, children: [], gap, align, justify });
        this.title = title;
        this.position = position;
        this.collapsed = collapsed;
        this.scrollable = scrollable;
        this._collapseMin = null;   // stashed explicit main-axis min (Size|null)
        this._collapseMax = null;   // stashed explicit main-axis max (Size|null)
        this._collapseStashed = false;
        this._chromeYCache = null;    // cached measured chrome { folded, chrome }
        this._toggleBtn = null;
        this._lastHeaderHeight = null; // guard for the header ResizeObserver
        this._onThemeChange = () => this._invalidateChrome();
        if (typeof document !== 'undefined' && typeof document.addEventListener === 'function') {
            document.addEventListener('tanga:themechange', this._onThemeChange);
        }
        this.icon = icon;
        this.icon_only = icon_only;
        this.parent_id = parent_id;
        this.groupId = id;

        this.el.classList.add('tanga-group');
        this._setupChrome();

        for (const child of children) this.addChild(child);
    }

    _setupChrome() {
        Object.assign(this.el.style, {
            display: 'flex',
            flexDirection: 'column',
            position: 'relative',
        });

        if (this.scrollable) {
            this.el.style.overflow = 'hidden';
        }

        this._header = document.createElement('div');
        this._header.className = 'tanga-group-header';
        Object.assign(this._header.style, {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '6px',
        });

        if (this.scrollable) {
            this._header.style.flexShrink = '0';
        }

        const titleWrap = document.createElement('div');
        titleWrap.className = 'tanga-group-title-wrap';
        Object.assign(titleWrap.style, {
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
        });

        if (this.icon) {
            const icon = createIconElement(this.icon);
            icon.classList.add('tanga-group-icon');
            titleWrap.appendChild(icon);
        }

        if (!this.icon_only) {
            const titleSpan = document.createElement('span');
            titleSpan.className = 'tanga-group-title';
            titleSpan.textContent = this.title || 'Controls';
            titleWrap.appendChild(titleSpan);
        }

        this._header.appendChild(titleWrap);

        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'tanga-group-toggle';
        toggleBtn.title = 'Collapse / Expand';
        this._toggleBtn = toggleBtn;
        this._updateFoldIcon();

        toggleBtn.addEventListener('click', () => {
            this.setCollapsed(!this.collapsed);
        });
        this._header.appendChild(toggleBtn);
        this.el.appendChild(this._header);

        this._content = document.createElement('div');
        this._content.className = 'tanga-group-content';
        this.el.appendChild(this._content);
        this._applyFlex(); // retarget flex onto the content div
        this._applyScroll(); // scroll the content region below the title bar
        this._applyCollapsed();

        if (typeof ResizeObserver !== 'undefined') {
            this._headerResizeObserver = new ResizeObserver((entries) => {
                const rect = entries[0] && entries[0].contentRect;
                if (!rect || rect.height === this._lastHeaderHeight) return;
                this._lastHeaderHeight = rect.height;
                this._invalidateChrome();
            });
            this._headerResizeObserver.observe(this._header);
        }
    }

    _applyCollapsed() {
        if (this._content) this._content.style.display = this.collapsed ? 'none' : '';
    }

    _updateFoldIcon() {
        if (!this._toggleBtn) return;
        this._toggleBtn.replaceChildren(
            createIconElement(
                this.collapsed ? 'material:expand_less' : 'material:expand_more'
            )
        );
    }

    // Collapse/expand.  When collapsed the pane is reduced to its title bar, so
    // its main-axis min/max change; we change them through the normal setters,
    // which broadcast `constraintschange` so any subscribed container re-lays
    // out (no special SplitView knowledge needed).
    setCollapsed(collapsed) {
        if (this.collapsed === collapsed) return;
        this.collapsed = collapsed;
        if (this.direction !== 'wrap') {
            if (collapsed) {
                this._pinCollapsed();
                this._collapseStashed = true;
            } else if (this._collapseStashed) {
                this._restoreCollapsed();
                this._collapseStashed = false;
            } else {
                // Constructed already-collapsed (e.g. serialized state): the
                // explicit min/max were never pinned, but the resolved size
                // changes with `collapsed`, so notify subscribed containers.
                this.emit('constraintschange', {
                    fields: ['minWidth', 'minHeight', 'maxWidth', 'maxHeight'],
                });
            }
        } else {
            this.emit('constraintschange', {
                fields: ['minWidth', 'minHeight', 'maxWidth', 'maxHeight'],
            });
        }
        this._applyCollapsed();
        this._updateFoldIcon();
    }

    _pinCollapsed() {
        const main = stackMainAxis(this.direction);
        const folded = Size.px(this._chromeY().folded);
        if (main === 'x') {
            this._collapseMin = this._minWidth;
            this._collapseMax = this._maxWidth;
            this.minWidth = folded;
            this.maxWidth = folded;
        } else {
            this._collapseMin = this._minHeight;
            this._collapseMax = this._maxHeight;
            this.minHeight = folded;
            this.maxHeight = folded;
        }
    }

    _restoreCollapsed() {
        const main = stackMainAxis(this.direction);
        if (main === 'x') {
            this.minWidth = this._collapseMin;
            this.maxWidth = this._collapseMax;
        } else {
            this.minHeight = this._collapseMin;
            this.maxHeight = this._collapseMax;
        }
    }

    // Measure the group's vertical chrome (title bar + shell) from the rendered
    // DOM so it tracks the active theme.  Returns `{ folded, chrome }` in px:
    //   folded — collapsed pane height, i.e. the title bar's bottom border (the
    //            drawn "horizontal bar") relative to the pane top;
    //   chrome — the full vertical chrome above + below the content (added to
    //            the content size for expanded min/preferred).
    // Falls back to constants when the DOM isn't measurable (fake DOM in tests,
    // or before the first layout).  The measured result is cached; invalidation
    // happens in the header ResizeObserver / theme-change handler.
    _chromeY() {
        if (this._chromeYCache) return this._chromeYCache;
        const header = this._header;
        if (!header || typeof header.getBoundingClientRect !== 'function') {
            return { folded: FOLDED_FALLBACK, chrome: CHROME_FALLBACK };
        }
        const elRect = this.el.getBoundingClientRect();
        const headerRect = header.getBoundingClientRect();
        if (!headerRect || !headerRect.height) {
            return { folded: FOLDED_FALLBACK, chrome: CHROME_FALLBACK };
        }
        const folded = Math.round(headerRect.bottom - elRect.top);
        const csHeader = getComputedStyle(header);
        const csEl = getComputedStyle(this.el);
        const chrome = folded
            + (parseFloat(csHeader.marginBottom) || 0)
            + (parseFloat(csEl.paddingBottom) || 0)
            + (parseFloat(csEl.borderBottomWidth) || 0);
        const result = { folded, chrome: Math.round(chrome) };
        this._chromeYCache = result;
        return result;
    }

    // Drop the cached chrome and tell enclosing containers to re-layout, so they
    // pick up a new measured value after a theme/header change.
    _invalidateChrome() {
        this._chromeYCache = null;
        this.emit('preferredchange', { fields: ['preferredWidth', 'preferredHeight'] });
        this.emit('constraintschange', { fields: ['minWidth', 'minHeight', 'maxWidth', 'maxHeight'] });
    }

    // The group's chrome (title bar + shell) adds to the *derived* content size
    // along the stack axis.  An explicit `min_*`/`preferred_*` describes the
    // whole pane (chrome included), so it is returned unchanged — otherwise
    // `min_height == max_height` would no longer read as a fixed pane (the
    // chrome would push the derived min above the explicit max).  When
    // collapsed, the content is hidden, so the folded pane is just the chrome up
    // to the title bar's bottom border.
    minSizePx(axis, available) {
        if (this.direction === 'wrap' || axis !== stackMainAxis(this.direction)) {
            return super.minSizePx(axis, available);
        }
        const { folded, chrome } = this._chromeY();
        if (this.collapsed) return folded;
        const explicit = View.prototype.minSizePx.call(this, axis, available);
        const contentMin = this.scrollable
            ? 0
            : stackMinSize(axis, this.direction, this.children, available);
        return Math.max(explicit, contentMin + chrome);
    }

    maxSizePx(axis, available) {
        if (this.collapsed && this.direction !== 'wrap'
            && axis === stackMainAxis(this.direction)) {
            return this._chromeY().folded;
        }
        return super.maxSizePx(axis, available);
    }

    preferredPx(axis, available) {
        if (this.direction === 'wrap' || axis !== stackMainAxis(this.direction)) {
            return super.preferredPx(axis, available);
        }
        const { folded, chrome } = this._chromeY();
        if (this.collapsed) return folded;
        const explicit = View.prototype.preferredPx.call(this, axis, available);
        if (explicit !== null && explicit !== undefined) return explicit;
        if (this.scrollable) return null;
        const contentPref = stackPreferredSize(axis, this.direction, this.children, available);
        return contentPref === null || contentPref === undefined
            ? null
            : contentPref + chrome;
    }

    destroy() {
        if (this._headerResizeObserver) this._headerResizeObserver.disconnect();
        if (typeof document !== 'undefined' && typeof document.removeEventListener === 'function') {
            document.removeEventListener('tanga:themechange', this._onThemeChange);
        }
        super.destroy();
    }
}
