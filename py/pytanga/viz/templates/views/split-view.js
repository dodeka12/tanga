// Tanga Viewer — `SplitView`: a container that lays children along one axis,
// with draggable splitters.  Pure layout math lives in `split-resolver.js`.

import { View } from './view.js';
import { resolveSplit, deriveMinSize, SPLITTER_SIZE } from './split-resolver.js';
import { SpacerView } from './spacer-view.js';

/**
 * A container of `View` children arranged along a single axis with splitters.
 *
 * `orientation` is `"horizontal"` (children side-by-side) or `"vertical"`
 * (stacked).  `movable` is `true`/`false`/`null` (auto): `false` locks every
 * splitter; otherwise a splitter is draggable unless a neighbor is fixed.
 */
export class SplitView extends View {
    constructor({ orientation = 'horizontal', movable = null, children = [] } = {}) {
        super();
        if (orientation !== 'horizontal' && orientation !== 'vertical') {
            throw new Error(
                `orientation must be 'horizontal' or 'vertical', got ${JSON.stringify(orientation)}`
            );
        }
        this.orientation = orientation;
        this.axis = orientation === 'horizontal' ? 'x' : 'y';
        this.movable = movable;
        this.children = [];
        this._childSubs = new Map(); // view -> AbortController
        this._sizes = null; // current per-child px sizes (drag/relayout basis)
        this._splitters = [];
        this._spacerView = null;
        this._drag = null;

        this.el.classList.add('tanga-split', `tanga-split-${orientation}`);
        this.el.style.position = 'relative';
        this.el.style.overflow = 'hidden';

        this._onExtentChanged = () => this._relayout();

        for (const child of children) this.addChild(child);
    }

    addChild(view) {
        const ac = new AbortController();
        view.mount(this.el);
        view.on('constraintschange', () => this._relayout(), { signal: ac.signal });
        view.on('preferredchange', () => this._relayout(), { signal: ac.signal });
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
        this._sizes = null;
        this._relayout();
    }

    // A container's minimum is at least what its children need: along the split
    // axis they stack, along the cross axis the container must fit its largest
    // child.  This lets nested scene panes' own minimums propagate upward.
    minSizePx(axis, available) {
        const explicit = super.minSizePx(axis, available);
        const derived = deriveMinSize(axis, this.axis, this.children, available);
        return Math.max(explicit, derived);
    }

    _relayout() {
        const available = this.axis === 'x' ? this.width : this.height;
        if (available <= 0 || this.children.length === 0) return;

        const descriptors = this.children.map((child, i) => ({
            min: child.minSizePx(this.axis, available),
            max: child.maxSizePx(this.axis, available),
            preferred: this._sizes && this._sizes[i] !== undefined
                ? this._sizes[i] * available
                : child.preferredPx(this.axis, available),
        }));

        const plan = resolveSplit(descriptors, available);
        if (this.movable === false) {
            plan.splitters.forEach((s) => { s.movable = false; });
        }
        this._sizes = plan.items.map((it) => it.size / available);

        const sizeKey = this.axis === 'x' ? 'width' : 'height';
        const posKey = this.axis === 'x' ? 'left' : 'top';
        const crossSize = this.axis === 'x' ? 'height' : 'width';
        const crossPos = this.axis === 'x' ? 'top' : 'left';

        let offset = 0;
        plan.items.forEach((item, i) => {
            const el = this.children[i].el;
            el.style.position = 'absolute';
            el.style[posKey] = offset + 'px';
            el.style[crossPos] = '0px';
            el.style[sizeKey] = item.size + 'px';
            el.style[crossSize] = '100%';
            offset += item.size;
            if (i < plan.splitters.length) offset += SPLITTER_SIZE;
        });

        this._syncSplitterBars(plan.splitters, sizeKey, posKey, crossSize, crossPos);
        this._syncSpacer(plan.spacer, offset, sizeKey, posKey, crossSize, crossPos);
    }

    _syncSplitterBars(splitters, sizeKey, posKey, crossSize, crossPos) {
        while (this._splitters.length < splitters.length) {
            const idx = this._splitters.length;
            const bar = document.createElement('div');
            bar.classList.add('tanga-splitter');
            bar.style.position = 'absolute';
            bar.style.zIndex = '10';
            bar.addEventListener('pointerdown', (e) => this._onSplitterDown(idx, e));
            this.el.appendChild(bar);
            this._splitters.push(bar);
        }
        while (this._splitters.length > splitters.length) {
            this._splitters.pop().remove();
        }
        splitters.forEach((sp, k) => {
            const bar = this._splitters[k];
            const movable = sp.movable;
            // Fixed splitters draw a thin 1px line centered in the reserved gap;
            // movable ones are a filled bar.
            bar.style[posKey] = movable
                ? sp.position + 'px'
                : (sp.position + (SPLITTER_SIZE - 1) / 2) + 'px';
            bar.style[crossPos] = '0px';
            bar.style[sizeKey] = (movable ? SPLITTER_SIZE : 1) + 'px';
            bar.style[crossSize] = '100%';
            bar.style.cursor = movable
                ? (this.axis === 'x' ? 'col-resize' : 'row-resize')
                : 'default';
            bar.style.background = movable ? '#4a4a5e' : '#3a3a4a';
            bar.classList.toggle('tanga-splitter--fixed', !movable);
            bar.dataset.movable = movable ? '1' : '0';
        });
    }

    _syncSpacer(spacerPx, offset, sizeKey, posKey, crossSize, crossPos) {
        if (spacerPx <= 0) {
            if (this._spacerView) this._spacerView.el.style.display = 'none';
            return;
        }
        if (!this._spacerView) {
            this._spacerView = new SpacerView();
            this._spacerView.mount(this.el);
        }
        const el = this._spacerView.el;
        el.style.display = 'block';
        el.style.position = 'absolute';
        el.style[posKey] = offset + 'px';
        el.style[crossPos] = '0px';
        el.style[sizeKey] = spacerPx + 'px';
        el.style[crossSize] = '100%';
    }

    _onSplitterDown(index, event) {
        const bar = this._splitters[index];
        if (bar.dataset.movable !== '1') return;
        event.preventDefault();
        this._drag = {
            index,
            startPos: this.axis === 'x' ? event.clientX : event.clientY,
            startSizes: this._sizes.slice(),
            startAvailable: this.axis === 'x' ? this.width : this.height,
        };
        const onMove = (e) => this._onSplitterMove(e);
        const onUp = () => {
            window.removeEventListener('pointermove', onMove);
            window.removeEventListener('pointerup', onUp);
            this._drag = null;
        };
        window.addEventListener('pointermove', onMove);
        window.addEventListener('pointerup', onUp);
    }

    _onSplitterMove(event) {
        if (!this._drag) return;
        const { index, startPos, startSizes, startAvailable } = this._drag;
        const current = this.axis === 'x' ? event.clientX : event.clientY;
        const delta = current - startPos;
        const available = startAvailable;

        const leftIdx = index;
        const rightIdx = index + 1;
        const left = startSizes[leftIdx] * available;
        const right = startSizes[rightIdx] * available;
        const leftMin = this.children[leftIdx].minSizePx(this.axis, available);
        const leftMax = this.children[leftIdx].maxSizePx(this.axis, available);
        const rightMin = this.children[rightIdx].minSizePx(this.axis, available);
        const rightMax = this.children[rightIdx].maxSizePx(this.axis, available);

        let newLeft = left + delta;
        newLeft = Math.max(
            leftMin,
            Math.min(leftMax !== null && leftMax !== undefined ? leftMax : Infinity, newLeft)
        );
        const applied = newLeft - left;
        let newRight = right - applied;
        newRight = Math.max(
            rightMin,
            Math.min(rightMax !== null && rightMax !== undefined ? rightMax : Infinity, newRight)
        );

        this._sizes[leftIdx] = newLeft / available;
        this._sizes[rightIdx] = newRight / available;
        this._relayout();
    }

    destroy() {
        for (const ac of this._childSubs.values()) ac.abort();
        this._childSubs.clear();
        super.destroy();
    }
}
