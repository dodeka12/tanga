import test from 'node:test';
import assert from 'node:assert/strict';

// `WebSocket.OPEN` is a browser global; stub it for Node.
globalThis.WebSocket = { OPEN: 1 };

const { sendEvent, sendLog, setLogForwarding, logForwardingEnabled, setWebSocket } = await import('../../../py/pytanga/viz/templates/events.js');

test('sendEvent emits the unified envelope', () => {
    const sent = [];
    setWebSocket({ readyState: 1, send: (d) => sent.push(JSON.parse(d)) });
    sendEvent('fc', 'change', { value: '/x' });
    assert.deepEqual(sent, [{ type: 'event', target: 'fc', event: 'change', data: { value: '/x' } }]);
});

test('sendEvent no-ops when the socket is closed', () => {
    const sent = [];
    setWebSocket({ readyState: 3, send: (d) => sent.push(d) });
    sendEvent('fc', 'click', {});
    assert.deepEqual(sent, []);
});

test('sendLog emits the log envelope', () => {
    const sent = [];
    setWebSocket({ readyState: 1, send: (d) => sent.push(JSON.parse(d)) });
    sendLog('warn', 'msg', { source: 'x' });
    assert.deepEqual(sent, [{
        type: 'event',
        target: 'client_log',
        event: 'log',
        data: { level: 'warn', message: 'msg', source: 'x', data: null },
    }]);
});

test('sendLog no-ops when the socket is closed', () => {
    const sent = [];
    setWebSocket({ readyState: 3, send: (d) => sent.push(d) });
    sendLog('error', 'msg');
    assert.deepEqual(sent, []);
});

test('log forwarding defaults off and toggles', () => {
    assert.equal(logForwardingEnabled(), false);
    setLogForwarding(true);
    assert.equal(logForwardingEnabled(), true);
    setLogForwarding(false);
    assert.equal(logForwardingEnabled(), false);
});
