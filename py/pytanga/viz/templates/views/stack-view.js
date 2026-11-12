// Tanga Viewer — `StackView`: a flow/flex container that stacks children
// vertically, horizontally, or wraps.  Content-size math lives in `stack-size.js`.

import { View } from './view.js';
import { flowFlex, flexCss } from './flow-size.js';
import {
    GAP,
    resolveGapPx,
    stackMainAxis,
    stackMinSize,
    stackPreferredSize,
} from './stack-size.js';

const DIRECTIONS = ['vertical', 'horizontal', 'wrap'];

/**
 * A flex container of `View` children laid out in normal flow (no splitters).
 * `direction` is `"vertical"` (column), `"horizontal"` (row), or `"wrap"`
 * (row that wraps to a new line when out of space).
 */
export class StackView extends View {
    constructor({
        direction = 'vertical',
        scrollable = false,
        gap = null,
        align = 'stretch',
        justify = 'start',
        children = [],
    } = {}) {
        super();
        if (!DIRECTIONS.includes(direction)) {
            throw new Error(
                `direction must be one of ${DIRECTIONS.join(', ')}, got ${JSON.stringify(direction)}`
            );
        }
        this.direction = direction;
        this.scrollable = scrollable;
        this.gap = gap;
        this.align = align;
        this.justify = justify;
        this.children = [];
        this._childSubs = new Map(); // view -> AbortController
        this._content = this.el; // children mount here (GroupView retargets this)
        this._gapCache = null; // measured computed gap (px)
        this._onThemeChange = () => {
            this._gapCache = null;
            this._relayout();
        };
        if (typeof document !== 'undefined' && typeof document.addEventListener === 'function') {
            document.addEventListener('tanga:themechange', this._onThemeChange);
        }

        this.el.classList.add('tanga-stack', `tanga-stack-${direction}`);
        this._applyFlex();
        this._applyScroll();

        for (const child of children) this.addChild(child);
    }

    _applyFlex() {
        const s = this._content.style;
        s.display = 'flex';
        s.position = 'relative';
        s.gap = this.gap == null ? `var(--tanga-stack-gap, ${GAP}px)` : `${this.gap}px`;
        this._gapCache = null;
        s.alignItems = this.align;
        s.justifyContent = this.justify;
        s.flexDirection = this.direction === 'vertical' ? 'column' : 'row';
        s.flexWrap = this.direction === 'wrap' ? 'wrap' : 'nowrap';
    }

    // The used gap: an explicit Python `gap` wins, otherwise the computed CSS
    // gap (`var(--tanga-stack-gap)`), so a theme moves the layout *and* the
    // size maths.  A detached element reports no gap — never cache that.
    _gapPx() {
        if (this.gap != null) return this.gap;
        if (this._gapCache != null) return this._gapCache;
        if (typeof getComputedStyle !== 'function') return GAP;
        const cs = getComputedStyle(this._content);
        const raw = (this.direction === 'vertical' ? cs.rowGap : cs.columnGap) || cs.gap;
        const px = resolveGapPx(raw, null);
        if (px === null) return GAP;
        this._gapCache = px;
        return px;
    }

    // A (re)mounted element has a new computed style — drop a stale gap.
    mount(host) {
        this._gapCache = null;
        super.mount(host);
    }

    _applyScroll() {
        if (!this.scrollable) return;
        this._content.classList.add('tanga-scroll');
        Object.assign(this._content.style, {
            overflow: 'auto',
            minWidth: '0',
            minHeight: '0',
            flex: '1 1 auto',
        });
    }

    addChild(view) {
        const ac = new AbortController();
        // Let "auto"-orientation children (e.g. SeparatorView) derive the
        // perpendicular orientation from this container's direction.
        if (typeof view.resolveOrientation === 'function') view.resolveOrientation(this.direction);
        view.mount(this._content);
        const mainAxis = stackMainAxis(this.direction);
        const pref = mainAxis === 'x' ? view.preferredWidth : view.preferredHeight;
        view.el.style.flex = flexCss(flowFlex(pref));
        if (pref && pref.unit === 'fr') {
            // A growing child must be able to shrink below its content size;
            // only clear the main-axis min when the child has no explicit one.
            if (mainAxis === 'x' && view.minWidth === null) {
                view.el.style.minWidth = '0';
            } else if (mainAxis === 'y' && view.minHeight === null) {
                view.el.style.minHeight = '0';
            }
        }
        view.on('preferredchange', () => this._relayout(), { signal: ac.signal });
        view.on('constraintschange', () => this._relayout(), { signal: ac.signal });
        this._childSubs.set(view, ac);
        this.children.push(view);
        this._relayout();
        return view;
    }

    removeChild(view) {
        const idx = this.children.indexOf(view);
        if (idx === -1) return;
        const ac = this._childSubs.get(view);
        if (ac) ac.abort();
        this._childSubs.delete(view);
        this.children.splice(idx, 1);
        view.unmount();
        this._relayout();
    }

    // A stack's minimum is at least what its children need (content sizing).
    // A scrollable stack instead decouples from content along its main axis so
    // an enclosing SplitView may shrink it and the content scrolls.
    minSizePx(axis, available) {
        const explicit = super.minSizePx(axis, available);
        if (this.scrollable && axis === stackMainAxis(this.direction)) {
            return explicit;
        }
        return Math.max(
            explicit,
            stackMinSize(axis, this.direction, this.children, available, this._gapPx())
        );
    }

    preferredPx(axis, available) {
        const explicit = super.preferredPx(axis, available);
        if (explicit !== null && explicit !== undefined) return explicit;
        if (this.scrollable && axis === stackMainAxis(this.direction)) {
            return null;
        }
        return stackPreferredSize(
            axis, this.direction, this.children, available, this._gapPx()
        );
    }

    _relayout() {
        // Content size may have changed — notify an enclosing SplitView.
        this.emit('preferredchange', { fields: ['preferredWidth', 'preferredHeight'] });
    }

    destroy() {
        if (typeof document !== 'undefined' && typeof document.removeEventListener === 'function') {
            document.removeEventListener('tanga:themechange', this._onThemeChange);
        }
        for (const ac of this._childSubs.values()) ac.abort();
        this._childSubs.clear();
        super.destroy();
    }
}
