// Tanga — unit tests for the pure layout reconciliation core (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import {
    collectNodeTypes,
    planReconciliation,
} from '../../../py/pytanga/viz/templates/views/reconcile.js';

const N = (id, type, children = []) => ({ id, type, children });
const ids = (nodes) => nodes.map((n) => n.id);

test('empty live map → every node is created, nothing orphaned', () => {
    const root = N('v0', 'split', [N('sv0', 'scene_view'), N('sv1', 'scene_view')]);
    const plan = planReconciliation(collectNodeTypes(root), new Map());
    assert.deepEqual(ids(plan.reuse), []);
    assert.deepEqual(ids(plan.create), ['v0', 'sv0', 'sv1']);
    assert.deepEqual(plan.orphaned, []);
});

test('same reusable node re-pushed → reused', () => {
    const plan = planReconciliation(
        [N('sv0', 'scene_view')],
        new Map([['sv0', 'scene_view']]),
    );
    assert.deepEqual(ids(plan.reuse), ['sv0']);
    assert.deepEqual(ids(plan.create), []);
    assert.deepEqual(plan.orphaned, []);
});

test('container is never reused (rebuilt) → created + old orphaned', () => {
    const plan = planReconciliation([N('v0', 'split')], new Map([['v0', 'split']]));
    assert.deepEqual(ids(plan.reuse), []);
    assert.deepEqual(ids(plan.create), ['v0']);
    assert.deepEqual(plan.orphaned, ['v0']);
});

test('non-reusable leaf (table_view) → created + old orphaned', () => {
    const plan = planReconciliation(
        [N('t1', 'table_view')],
        new Map([['t1', 'table_view']]),
    );
    assert.deepEqual(ids(plan.reuse), []);
    assert.deepEqual(ids(plan.create), ['t1']);
    assert.deepEqual(plan.orphaned, ['t1']);
});

test('reordered same-scene panes → both reused (order-independent)', () => {
    const live = new Map([['sv0', 'scene_view'], ['sv1', 'scene_view']]);
    const plan = planReconciliation(
        [N('sv1', 'scene_view'), N('sv0', 'scene_view')],
        live,
    );
    assert.deepEqual(ids(plan.reuse).sort(), ['sv0', 'sv1']);
    assert.deepEqual(ids(plan.create), []);
    assert.deepEqual(plan.orphaned, []);
});

test('removed node id → orphaned', () => {
    const live = new Map([['sv0', 'scene_view'], ['sv1', 'scene_view']]);
    const plan = planReconciliation([N('sv0', 'scene_view')], live);
    assert.deepEqual(ids(plan.reuse), ['sv0']);
    assert.deepEqual(ids(plan.create), []);
    assert.deepEqual(plan.orphaned, ['sv1']);
});

test('added node id → created', () => {
    const plan = planReconciliation(
        [N('sv0', 'scene_view'), N('sv2', 'scene_view')],
        new Map([['sv0', 'scene_view']]),
    );
    assert.deepEqual(ids(plan.reuse), ['sv0']);
    assert.deepEqual(ids(plan.create), ['sv2']);
    assert.deepEqual(plan.orphaned, []);
});

test('same id but different type → not reused; old orphaned + new created', () => {
    const plan = planReconciliation(
        [N('sv0', 'slider_view')],
        new Map([['sv0', 'scene_view']]),
    );
    assert.deepEqual(ids(plan.reuse), []);
    assert.deepEqual(ids(plan.create), ['sv0']);
    assert.deepEqual(plan.orphaned, ['sv0']);
});

test('two panes of the same scene with distinct ids → both reused', () => {
    const live = new Map([['sv0', 'scene_view'], ['sv1', 'scene_view']]);
    const plan = planReconciliation(
        [N('sv0', 'scene_view'), N('sv1', 'scene_view')],
        live,
    );
    assert.deepEqual(ids(plan.reuse), ['sv0', 'sv1']);
    assert.deepEqual(ids(plan.create), []);
    assert.deepEqual(plan.orphaned, []);
});

test('collectNodeTypes traverses nested children in DFS order', () => {
    const root = N('v0', 'split', [
        N('g1', 'group', [N('b1', 'button_view')]),
        N('sv0', 'scene_view', [N('ov1', 'label_view')]),
    ]);
    assert.deepEqual(collectNodeTypes(root), [
        { id: 'v0', type: 'split' },
        { id: 'g1', type: 'group' },
        { id: 'b1', type: 'button_view' },
        { id: 'sv0', type: 'scene_view' },
        { id: 'ov1', type: 'label_view' },
    ]);
});
