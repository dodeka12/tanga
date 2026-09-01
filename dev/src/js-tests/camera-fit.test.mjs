import test from 'node:test';
import assert from 'node:assert/strict';

import { finiteAspect, orthoFrustum } from '../../../py/pytanga/viz/templates/camera-fit.js';

test('finiteAspect returns width / height for valid sizes', () => {
    assert.equal(finiteAspect(200, 100), 2);
    assert.equal(finiteAspect(200, 800), 0.25);
});

test('finiteAspect returns NaN for non-positive or non-finite sizes', () => {
    assert.ok(Number.isNaN(finiteAspect(0, 100)));
    assert.ok(Number.isNaN(finiteAspect(100, 0)));
    assert.ok(Number.isNaN(finiteAspect(-1, 100)));
    assert.ok(Number.isNaN(finiteAspect(NaN, 100)));
    assert.ok(Number.isNaN(finiteAspect(100, Infinity)));
});

test('orthoFrustum letterboxes a rect to the viewport aspect', () => {
    // 20x10 world rect in a 200x100 (aspect 2) pane: no extra margin needed.
    assert.deepEqual(
        orthoFrustum(-10, 10, -5, 5, true, 0, 200, 100),
        { left: -10, right: 10, top: 5, bottom: -5 },
    );
});

test('orthoFrustum uses the pane aspect, not the window aspect', () => {
    // A square 10x10 world rect in a narrow 200x800 pane (aspect 0.25) must
    // produce a frustum whose aspect is 0.25 — i.e. taller than it is wide.
    assert.deepEqual(
        orthoFrustum(-5, 5, -5, 5, true, 0, 200, 800),
        { left: -5, right: 5, top: 20, bottom: -20 },
    );
    const f = orthoFrustum(-5, 5, -5, 5, true, 0, 200, 800);
    assert.equal((f.right - f.left) / (f.top - f.bottom), 0.25);
});

test('orthoFrustum stretch mode scales X and Y independently', () => {
    // border_px 0 in stretch mode maps the rect onto the full viewport 1:1.
    assert.deepEqual(
        orthoFrustum(-10, 10, -5, 5, false, 0, 200, 100),
        { left: -10, right: 10, top: 5, bottom: -5 },
    );
});

test('orthoFrustum border_px insets the content area in both modes', () => {
    // 10px border on a 200x100 viewport: content area is 180x80.
    const uniform = orthoFrustum(-10, 10, -5, 5, true, 10, 200, 100);
    assert.ok(uniform.top > 5, 'uniform letterbox expands the frustum for the border');
    assert.equal(uniform.left, -uniform.right);
    assert.equal(uniform.top, -uniform.bottom);

    const stretch = orthoFrustum(-10, 10, -5, 5, false, 10, 200, 100);
    assert.ok(stretch.left < -10, 'stretch mode expands to cover the border');
    assert.ok(stretch.top > 5);
});
