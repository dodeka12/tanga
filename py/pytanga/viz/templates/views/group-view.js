// Tanga Viewer — `GroupView`: a titled `StackView` (panel chrome) that holds
// control views (or any views). Usable as a split pane or a scene overlay
// (anchored by `position`).

import { Size } from './size.js';
import { View } from './view.js';
import { StackView } from './stack-view.js';
import { stackMainAxis, stackMinSize, stackPreferredSize } from './stack-size.js';
import { applyTooltip, createIconElement, sendControlEvent } from '../controls-panel.js';
import { isGroupHeaderInteractiveEvent } from './group-header.js';

// Fallback vertical chrome (border-box px) used when the rendered DOM can't be
// measured (fake DOM in tests, or before the first layout).  Derived from
// `themes/views/group-view.css`:
//   .tanga-group          border 1px + padding 8px on each side (18px total)
//   .tanga-group-header   ~22px content (toggle) + 6px padding-bottom
//                         + 1px border-bottom + 6px margin-bottom (35px total)
// folded = 1 + 8 + (22 + 6 + 1) = 38   (pane ends at the title bar's bottom border)
// chrome = 2 + 16 + 29 + 6      = 53   (full shell + header + its margin)
// A headerless group has folded = 0 and only the shell around its content.
const FOLDED_FALLBACK = 38;
const CHROME_FALLBACK = 53;
const SHELL_FALLBACK = 18; // .tanga-group border 1px + padding 8px ×2

export class GroupView extends StackView {
    constructor({
        title = '',
        direction = 'vertical',
        position = null,
        collapsed = false,
        show_header = true,
        collapsible = true,
        title_size = null,
        variant = 'default',
        enabled = true,
        scrollable = false,
        gap = null,
        align = 'stretch',
        justify = 'start',
        icon = null,
        icon_only = false,
        tooltip = '',
        parent_id = null,
        id = null,
        children = [],
    } = {}) {
        super({ direction, children: [], gap, align, justify });
        this.title = title ?? '';
        this.position = position;
        this.collapsed = collapsed;
        this.show_header = show_header !== false;
        this.collapsible = this.show_header && collapsible !== false;
        this.title_size = title_size == null ? null : Number(title_size);
        this.variant = ['default', 'small', 'tiny'].includes(variant)
            ? variant : 'default';
        if (this.collapsed && !this.collapsible) this.collapsed = false;
        this.enabled = enabled;
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
        this.tooltip = tooltip;
        this.parent_id = parent_id;
        this.groupId = id;

        this.el.classList.add('tanga-group');
        this._syncChromeClasses();
        this._setupChrome();
        if (!this.enabled) this.setEnabled(false);

        for (const child of children) this.addChild(child);
    }

    _syncChromeClasses() {
        this.el.classList.toggle('tanga-group-no-header', !this.show_header);
        this.el.classList.toggle('tanga-group-static', !this.collapsible);
        this.el.classList.toggle('tanga-group-small', this.variant === 'small');
        this.el.classList.toggle('tanga-group-tiny', this.variant === 'tiny');
        // Deprecated alias kept for one release (see phase 1 CSS).
        this.el.classList.toggle('tanga-group-nested', this.variant === 'small');
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

        this._content = document.createElement('div');
        this._content.className = 'tanga-group-content';
        this.el.appendChild(this._content);

        this._ensureHeader();
        this._applyFlex(); // retarget flex onto the content div
        this._applyScroll(); // scroll the content region below the title bar
        this._applyCollapsed();
    }

    // Create the header bar once, or drop it when the group has no title,
    // icon or fold toggle to show.  A late header is inserted *before* the
    // content so it always stays above it.
    _ensureHeader() {
        if (!this.show_header || !(this.collapsible || this.title || this.icon)) {
            this._teardownHeader();
            return;
        }
        if (this._header) {
            // A layout re-push can flip `collapsible`; the toggle presence is
            // part of the header structure, so rebuild when it disagrees.
            if (!!this._toggleBtn === this.collapsible) {
                this._applyTitleSize();
                return;
            }
            this._teardownHeader();
        }

        this._header = document.createElement('div');
        this._header.className = 'tanga-group-header';

        if (this.scrollable) {
            this._header.style.flexShrink = '0';
        }

        const titleWrap = document.createElement('div');
        titleWrap.className = 'tanga-group-title-wrap';
        this._titleWrap = titleWrap;
        this._renderTitle();
        this._header.appendChild(titleWrap);

        if (this.collapsible) {
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'tanga-group-toggle';
            applyTooltip(toggleBtn, 'Collapse / Expand');
            this._toggleBtn = toggleBtn;
            this._updateFoldIcon();
            toggleBtn.addEventListener('click', () => {
                this.setCollapsed(!this.collapsed);
                sendControlEvent('control:group_toggle', this.groupId, this.collapsed);
            });
            this._header.appendChild(toggleBtn);
        }

        // Clicking anywhere on a collapsible header folds it.  The toggle has
        // its own handler, and `setCollapsed()` remains the only state path.
        // Resolve interactive descendants from the event path: the toggle
        // redraws its icon before this listener runs, detaching the click
        // target, so `event.target.closest(...)` would no longer find it.
        this._header.addEventListener('click', (event) => {
            if (!this.collapsible || !this.enabled) return;
            if (isGroupHeaderInteractiveEvent(event)) return;
            this.setCollapsed(!this.collapsed);
            sendControlEvent('control:group_toggle', this.groupId, this.collapsed);
        });

        this.el.insertBefore(this._header, this._content);
        this._applyTitleSize();
        this._invalidateChrome();

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

    _teardownHeader() {
        if (!this._header && !this._headerResizeObserver) return;
        if (this._headerResizeObserver) {
            this._headerResizeObserver.disconnect();
            this._headerResizeObserver = null;
        }
        if (this._header && this._header.parentNode) this._header.remove();
        this._header = null;
        this._titleWrap = null;
        this._toggleBtn = null;
        this._lastHeaderHeight = null;
        this._invalidateChrome();
    }

    _renderTitle() {
        const wrap = this._titleWrap;
        if (!wrap) return;
        wrap.replaceChildren();
        if (this.icon) {
            const icon = createIconElement(this.icon);
            icon.classList.add('tanga-group-icon');
            wrap.appendChild(icon);
        }
        if (!this.icon_only && this.title) {
            const span = document.createElement('span');
            span.className = 'tanga-group-title';
            span.textContent = this.title;
            wrap.appendChild(span);
        }
        // Keep the toggle button flush right when there is no title/icon.
        wrap.style.display = wrap.childElementCount ? '' : 'none';
        applyTooltip(wrap, this.tooltip);
    }

    // Instance override (scoped custom property only — never a resolved
    // appearance value), so every theme rule for `.tanga-group-title` still
    // applies except the font size.
    _applyTitleSize() {
        if (this.title_size == null) {
            this.el.style.removeProperty('--tanga-group-title-font-size');
        } else {
            this.el.style.setProperty(
                '--tanga-group-title-font-size', `${this.title_size}px`
            );
        }
    }

    update(node) {
        if ('title' in node) this.title = node.title ?? '';
        this.position = node.position ?? this.position;
        this.direction = node.direction ?? this.direction;
        this.scrollable = node.scrollable ?? this.scrollable;
        this.gap = node.gap ?? this.gap;
        this.align = node.align ?? this.align;
        this.justify = node.justify ?? this.justify;
        this.icon = node.icon ?? this.icon;
        this.icon_only = node.icon_only ?? this.icon_only;
        this.tooltip = node.tooltip ?? this.tooltip;
        this.parent_id = node.parent_id ?? this.parent_id;
        this.groupId = node.id ?? this.groupId;
        if ('show_header' in node) this.show_header = node.show_header !== false;
        if ('collapsible' in node) this.collapsible = node.collapsible !== false;
        if ('title_size' in node) {
            this.title_size = node.title_size == null ? null : Number(node.title_size);
        }
        if ('variant' in node) {
            this.variant = ['default', 'small', 'tiny'].includes(node.variant)
                ? node.variant : 'default';
        }
        this.collapsible = this.show_header && this.collapsible;
        if (this.collapsed && !this.collapsible) this.collapsed = false;
        this._syncChromeClasses();
        this._ensureHeader();
        this._applyTitleSize();
        this._applyFlex();
        this._applyScroll();
        this._renderTitle();
        if (node.collapsed !== undefined) {
            this.setCollapsed(!!node.collapsed);
        }
        if (node.enabled !== undefined) {
            this.setEnabled(!!node.enabled);
        }
        this._applyCollapsed();
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

    // Enable/disable.  Disabling greys the header, collapses the pane, and locks
    // the fold toggle so it cannot be expanded while disabled.
    setEnabled(enabled) {
        this.enabled = !!enabled;
        this.el.classList.toggle('tanga-group-disabled', !this.enabled);
        if (this._toggleBtn) this._toggleBtn.disabled = !this.enabled;
        // A static group cannot fold, so dim its content instead.
        if (!this.enabled && this.collapsible) this.setCollapsed(true);
    }

    setTitle(title) {
        this.title = title ?? '';
        // A rename can create or drop the header bar.
        this._ensureHeader();
        this._renderTitle();
    }

    setTooltip(tooltip) {
        this.tooltip = tooltip || '';
        applyTooltip(this._titleWrap || this.el, this.tooltip);
    }

    // Collapse/expand.  When collapsed the pane is reduced to its title bar, so
    // its main-axis min/max change; we change them through the normal setters,
    // which broadcast `constraintschange` so any subscribed container re-lays
    // out (no special SplitView knowledge needed).
    setCollapsed(collapsed) {
        if (!this.collapsible) return;
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
        if (!header) {
            // No header bar: only the panel shell surrounds the content.
            if (typeof getComputedStyle !== 'function') {
                return { folded: 0, chrome: SHELL_FALLBACK };
            }
            const cs = getComputedStyle(this.el);
            if (!cs || (!cs.paddingTop && !cs.paddingBottom
                && !cs.borderTopWidth && !cs.borderBottomWidth)) {
                return { folded: 0, chrome: SHELL_FALLBACK };
            }
            const shell = (parseFloat(cs.paddingTop) || 0)
                + (parseFloat(cs.paddingBottom) || 0)
                + (parseFloat(cs.borderTopWidth) || 0)
                + (parseFloat(cs.borderBottomWidth) || 0);
            const result = { folded: 0, chrome: Math.round(shell) };
            this._chromeYCache = result;
            return result;
        }
        if (typeof header.getBoundingClientRect !== 'function') {
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
            : stackMinSize(axis, this.direction, this.children, available, this._gapPx());
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
        const contentPref = stackPreferredSize(
            axis, this.direction, this.children, available, this._gapPx()
        );
        return contentPref === null || contentPref === undefined
            ? null
            : contentPref + chrome;
    }

    destroy() {
        this._teardownHeader();
        if (typeof document !== 'undefined' && typeof document.removeEventListener === 'function') {
            document.removeEventListener('tanga:themechange', this._onThemeChange);
        }
        super.destroy();
    }
}
