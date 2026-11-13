// Tanga — unit tests for whole-row hiding in a `ParamsView`.
//
// A Parameters row is a title (key label) plus the control view; hiding the
// control must hide the whole row, both for a control built with
// `visible: false` (initial state at build time) and for a server-driven
// `control_state {visible}`.  The row must also stop reserving height/gaps.
import test from 'node:test';
import assert from 'node:assert/strict';

import { installFakeDom } from './helpers/fake-dom.mjs';
import { View } from '../../../py/pytanga/viz/templates/views/view.js';
import { ParamsView } from '../../../py/pytanga/viz/templates/views/params-view.js';

installFakeDom();

function rowWithControl(control) {
    const params = new ParamsView({ title: '' });
    params.addRow({ key: 'radius', title: 'Radius', control });
    return { params, row: params._rows[0].row };
}

test('a control hidden before addRow starts as a hidden row', () => {
    const control = new View();
    control.setHidden(true);

    const { row } = rowWithControl(control);

    assert.equal(row.style.display, 'none');
});

test('hiding the control hides the row, title included', () => {
    const control = new View();
    const { row } = rowWithControl(control);
    assert.equal(row.style.display, '');

    control.setHidden(true);

    assert.equal(row.style.display, 'none');
});

test('showing the control shows the row again', () => {
    const control = new View();
    const { row } = rowWithControl(control);

    control.setHidden(true);
    control.setHidden(false);

    assert.equal(row.style.display, '');
});

test('hidden rows do not reserve height or row gaps', () => {
    const params = new ParamsView({ title: '' });
    const first = new View();
    const second = new View();
    const third = new View();
    params.addRow({ key: 'a', title: 'A', control: first });
    params.addRow({ key: 'b', title: 'B', control: second });
    params.addRow({ key: 'c', title: 'C', control: third });
    for (const entry of params._rows) {
        entry.row.getBoundingClientRect = () => ({ height: 10 });
    }

    assert.equal(params._measureHeight(), 30);

    second.setHidden(true);
    assert.equal(params._measureHeight(), 20);

    first.setHidden(true);
    third.setHidden(true);
    assert.equal(params._measureHeight(), null);
});

test('removeRow unsubscribes the visibility listener', () => {
    const control = new View();
    const { params, row } = rowWithControl(control);

    params.removeChild(control);
    control.setHidden(true);

    assert.equal(row.style.display, '');
});
