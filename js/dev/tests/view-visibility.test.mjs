// Tanga — unit tests for view visibility (`visible: false` / `control_state`).
//
// Covers the three pieces of the general visibility contract:
//   * `View.setHidden` removes a view from flow and from every size query, and
//     restores its own inline `display` on show;
//   * `applyNodeVisibility` maps a serialized `view_layout` node to that call
//     for *any* node type (containers included);
//   * `stackMinSize` / `stackPreferredSize` ignore hidden children completely
//     (size **and** gap).
import test from 'node:test';
import assert from 'node:assert/strict';

import { installFakeDom } from './helpers/fake-dom.mjs';
import { View } from '../../../py/pytanga/viz/templates/views/view.js';
import { Size } from '../../../py/pytanga/viz/templates/views/size.js';
import { applyNodeVisibility } from '../../../py/pytanga/viz/templates/views/node-state.js';
import {
    stackMinSize,
    stackPreferredSize,
} from '../../../py/pytanga/viz/templates/views/stack-size.js';

import {
    applyViewState,
    clearStatefulViews,
    getStatefulView,
    registerStatefulView,
    unregisterStatefulTree,
    unregisterStatefulView,
} from '../../../py/pytanga/viz/templates/views/view-state.js';

installFakeDom();

const px = (value) => Size.fromJSON({ value, unit: 'px' });

/** A view whose intrinsic size comes from a subclass size hook. */
class SizedView extends View {
    _minSizePx() { return 20; }
    _maxSizePx() { return 40; }
    _preferredPx() { return 30; }
}

test('a hidden view is removed from flow and reports no size', () => {
    const view = new SizedView();
    assert.equal(view.minSizePx('x', 100), 20);
    assert.equal(view.maxSizePx('x', 100), 40);
    assert.equal(view.preferredPx('x', 100), 30);

    view.setHidden(true);

    assert.equal(view.hidden, true);
    assert.equal(view.el.style.display, 'none');
    assert.equal(view.minSizePx('x', 100), 0);
    assert.equal(view.minSizePx('y', 100), 0);
    assert.equal(view.maxSizePx('x', 100), 0);
    assert.equal(view.preferredPx('x', 100), null);
    assert.equal(view.preferredPx('y', 100), null);
});

test('explicit size constraints are kept, not cleared, by hiding', () => {
    const view = new View();
    view.minWidth = px(120);
    view.minHeight = px(80);

    view.setHidden(true);
    view.setHidden(false);

    assert.equal(view.minWidth.value, 120);
    assert.equal(view.minHeight.value, 80);
    assert.equal(view.minSizePx('x', 400), 120);
});

test('showing a view restores its own inline display', () => {
    const view = new View();
    view.el.style.display = 'flex';

    view.setHidden(true);
    assert.equal(view.el.style.display, 'none');

    view.setHidden(false);
    assert.equal(view.el.style.display, 'flex');
});

test('showing a view without inline display clears it again', () => {
    const view = new View();
    view.setHidden(true);
    view.setHidden(false);
    assert.equal(view.el.style.display, '');
});

test('setHidden emits visibilitychange only on an actual change', () => {
    const view = new View();
    const seen = [];
    view.on('visibilitychange', (event) => seen.push(event.detail.hidden));

    view.setHidden(true);
    view.setHidden(true);
    view.setHidden(false);

    assert.deepEqual(seen, [true, false]);
});

test('applyNodeVisibility hides only on visible:false', () => {
    const view = new View();

    applyNodeVisibility(view, { id: 'v1', type: 'group' });
    assert.equal(view.hidden, false);

    applyNodeVisibility(view, { id: 'v1', type: 'group', visible: false });
    assert.equal(view.hidden, true);

    applyNodeVisibility(view, { id: 'v1', type: 'group', visible: true });
    assert.equal(view.hidden, false);

    // A node without `visible` (the common case) means "visible".
    view.setHidden(true);
    applyNodeVisibility(view, { id: 'v1', type: 'button_view' });
    assert.equal(view.hidden, false);
});

test('applyNodeVisibility tolerates views without setHidden', () => {
    assert.doesNotThrow(() => applyNodeVisibility({}, { visible: false }));
    assert.doesNotThrow(() => applyNodeVisibility(null, { visible: false }));
});

const sized = (size) => ({ minSizePx: () => size, preferredPx: () => size, hidden: false });
const hiddenSized = (size) => ({ ...sized(size), hidden: true });

test('stackMinSize skips hidden children and their gaps', () => {
    assert.equal(stackMinSize('y', 'vertical', [sized(10), sized(10)], 100, 12), 32);
    assert.equal(
        stackMinSize('y', 'vertical', [sized(10), hiddenSized(10), sized(10)], 100, 12),
        32
    );
    assert.equal(stackMinSize('y', 'vertical', [hiddenSized(10)], 100, 12), 0);
});

test('stackPreferredSize skips hidden children and their gaps', () => {
    assert.equal(
        stackPreferredSize('y', 'vertical', [sized(10), hiddenSized(10), sized(10)], 100, 12),
        32
    );
    assert.equal(stackPreferredSize('y', 'vertical', [hiddenSized(10)], 100, 12), null);
});

// ── control_state routing (view-state.js) ───────────────────

test('built views are reachable by id for control_state', () => {
    clearStatefulViews();
    const view = new View({ viewId: 'g1' });
    registerStatefulView(view);

    assert.equal(getStatefulView('g1'), view);
    assert.equal(getStatefulView('missing'), undefined);

    unregisterStatefulView(view);
    assert.equal(getStatefulView('g1'), undefined);
});

test('unregistering a replaced view keeps the newer one', () => {
    clearStatefulViews();
    const oldView = new View({ viewId: 'g1' });
    const newView = new View({ viewId: 'g1' });
    registerStatefulView(oldView);
    registerStatefulView(newView);

    unregisterStatefulView(oldView);

    assert.equal(getStatefulView('g1'), newView);
});

test('applyViewState routes visible to any view', () => {
    const view = new View();

    assert.equal(applyViewState(view, { visible: false }), true);
    assert.equal(view.hidden, true);

    assert.equal(applyViewState(view, { visible: true }), true);
    assert.equal(view.hidden, false);
});

test('applyViewState skips fields a view does not implement', () => {
    const view = new View();

    assert.equal(applyViewState(view, { collapsed: true }), false);
    assert.equal(applyViewState(view, {}), false);
    assert.equal(applyViewState(null, { visible: false }), false);
});

test('applyViewState routes titles, row titles and tooltips', () => {
    const calls = [];
    const view = {
        setTitle: (title) => calls.push(['title', title]),
        setRowTitle: (row, title) => calls.push(['row', row, title]),
        setTooltip: (tooltip) => calls.push(['tooltip', tooltip]),
    };

    applyViewState(view, { title: 'Radius' });
    applyViewState(view, { row: 'radius', title: 'Radius (m)' });
    applyViewState(view, { tooltip: 'hint' });

    assert.deepEqual(calls, [
        ['title', 'Radius'],
        ['row', 'radius', 'Radius (m)'],
        ['tooltip', 'hint'],
    ]);
});

test('unregisterStatefulTree drops a whole built subtree', () => {
    clearStatefulViews();
    const root = new View({ viewId: 'root' });
    const child = new View({ viewId: 'child' });
    const grandchild = new View({ viewId: 'grandchild' });
    child.children = [grandchild];
    root.children = [child];
    registerStatefulView(root);
    registerStatefulView(child);
    registerStatefulView(grandchild);

    unregisterStatefulTree(root);

    assert.equal(getStatefulView('root'), undefined);
    assert.equal(getStatefulView('child'), undefined);
    assert.equal(getStatefulView('grandchild'), undefined);
});
