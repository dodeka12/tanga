import test from 'node:test';
import assert from 'node:assert/strict';
import { Size } from '../../../py/pytanga/viz/templates/views/size.js';

test('factories', () => {
    assert.ok(Size.px(320).equals(new Size(320, 'px')));
    assert.ok(Size.percent(50).equals(new Size(50, '%')));
    assert.ok(Size.fr(2).equals(new Size(2, 'fr')));
    assert.ok(Size.auto().equals(new Size(0, 'auto')));
});

test('toJSON', () => {
    assert.deepEqual(Size.px(320).toJSON(), { value: 320, unit: 'px' });
    assert.deepEqual(Size.percent(50).toJSON(), { value: 50, unit: '%' });
    assert.deepEqual(Size.fr(2).toJSON(), { value: 2, unit: 'fr' });
    assert.deepEqual(Size.auto().toJSON(), { value: 0, unit: 'auto' });
});

test('fromJSON', () => {
    assert.ok(Size.fromJSON({ value: 320, unit: 'px' }).equals(Size.px(320)));
    assert.ok(Size.fromJSON({ value: 320 }).equals(Size.px(320))); // unit defaults
    assert.equal(Size.fromJSON(null), null);
    assert.equal(Size.fromJSON(undefined), null);
});

test('unknown unit throws', () => {
    assert.throws(() => new Size(1, 'em'), /Unknown size unit/);
});

test('resolve', () => {
    assert.equal(Size.px(320).resolve(1000), 320);
    assert.equal(Size.percent(50).resolve(1000), 500);
    assert.equal(Size.fr(2).resolve(1000, 123), 123);
    assert.equal(Size.auto().resolve(1000, null), null);
});

test('equals and clone', () => {
    const s = Size.px(10);
    assert.ok(s.equals(s.clone()));
    assert.notStrictEqual(s.clone(), s);
    assert.ok(!s.equals(Size.px(11)));
    assert.ok(!s.equals(null));
});
