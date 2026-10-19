// Tanga — unit tests for shader-error formatting + hook (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import {
    formatShaderError,
    installShaderErrorHook,
} from '../../../py/pytanga/viz/templates/renderers/shader-error.js';

function fakeGl() {
    const source = Array.from({ length: 10 }, (_, i) => `line ${i + 1}`).join('\n');
    return {
        getShaderInfoLog: () => 'ERROR: 0:5: syntax error',
        getShaderSource: () => source,
        getProgramParameter: () => false,
        getProgramInfoLog: () => 'program link failed',
    };
}

test('formatShaderError marks the error line with surrounding context', () => {
    const out = formatShaderError(fakeGl(), null, 'FRAGMENT');
    assert.ok(out.includes('FRAGMENT'));
    assert.ok(out.includes('> 5: line 5'));
    assert.ok(out.includes('1: line 1'));
});

test('installShaderErrorHook forwards a formatted error and can uninstall', () => {
    const renderer = { debug: {} };
    const calls = [];
    const uninstall = installShaderErrorHook(renderer, (err) => calls.push(err));
    renderer.debug.onShaderError(fakeGl(), {}, {}, {});
    assert.equal(calls.length, 1);
    assert.ok(calls[0].includes('THREE.WebGLProgram: Shader Error'));
    assert.ok(calls[0].includes('> 5: line 5'));
    uninstall();
    assert.notEqual(renderer.debug.onShaderError, null);
});
