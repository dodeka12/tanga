// Tanga Viewer — `StackView`: a flow/flex container that stacks children
// vertically, horizontally, or wraps.  Content-size math lives in `stack-size.js`.

import { View } from './view.js';
import { GAP, stackMainAxis, stackMinSize, stackPreferredSize } from './stack-size.js';

const DIRECTIONS = ['vertical', 'horizontal', 'wrap'];

/**
 * A flex container of `View` children laid out in normal flow (no splitters).
 * `direction` is `"vertical"` (column), `"horizontal"` (row), or `"wrap"`
 * (row that wraps to a new line when out of space).
 */
export class StackView extends View {
    constructor({ direction = 'vertical', scrollable = false, children = [] } = {}) {
        super();
        if (!DIRECTIONS.includes(direction)) {
            throw new Error(
                `direction must be one of ${DIRECTIONS.join(', ')}, got ${JSON.stringify(direction)}`
            );
        }
        this.direction = direction;
        this.scrollable = scrollable;
        this.children = [];
        this._childSubs = new Map(); // view -> AbortController
        this._content = this.el; // children mount here (GroupView retargets this)

        this.el.classList.add('tanga-stack', `tanga-stack-${direction}`);
        this._applyFlex();
        this._applyScroll();

        for (const child of children) this.addChild(child);
    }

    _applyFlex() {
        const s = this._content.style;
        s.display = 'flex';
        s.position = 'relative';
        s.gap = `${GAP}px`;
        s.flexDirection = this.direction === 'vertical' ? 'column' : 'row';
        s.flexWrap = this.direction === 'wrap' ? 'wrap' : 'nowrap';
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
        view.mount(this._content);
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
        return Math.max(explicit, stackMinSize(axis, this.direction, this.children, available));
    }

    preferredPx(axis, available) {
        const explicit = super.preferredPx(axis, available);
        if (explicit !== null && explicit !== undefined) return explicit;
        if (this.scrollable && axis === stackMainAxis(this.direction)) {
            return null;
        }
        return stackPreferredSize(axis, this.direction, this.children, available);
    }

    _relayout() {
        // Content size may have changed — notify an enclosing SplitView.
        this.emit('preferredchange', { fields: ['preferredWidth', 'preferredHeight'] });
    }

    destroy() {
        for (const ac of this._childSubs.values()) ac.abort();
        this._childSubs.clear();
        super.destroy();
    }
}
