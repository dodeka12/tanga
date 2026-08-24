import test from 'node:test';
import assert from 'node:assert/strict';
import { ViewEvent } from '../../../py/pytanga/viz/templates/views/view-event.js';

test('ViewEvent carries type and detail', () => {
    const ev = new ViewEvent('constraintschange', { fields: ['minWidth'] });
    assert.equal(ev.type, 'constraintschange');
    assert.deepEqual(ev.detail, { fields: ['minWidth'] });
    assert.ok(ev instanceof Event);
});
