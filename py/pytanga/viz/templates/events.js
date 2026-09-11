// Tanga Viewer — unified client→server event sending.
//
// Control elements (panel controls, layout views, banners, editors, file
// choosers) report every user action through `sendEvent` as one envelope:
//
//   { type: "event", target: "<id>", event: "<name>", data: {…} }
//
// `target` is the globally-unique control id, `event` is the short event name
// ("change", "click", "close", …), and `data` is the event payload (typically
// `{ value }`).
//
// Frontend warnings/errors are sent to the backend log over the same envelope
// via `sendLog(level, message, { source, data })`, which targets the reserved
// `CLIENT_LOG_ID` control with the `"log"` event.
//
// Interactive objects (ActPoint, …) currently send their `interaction:*`
// messages directly; see the follow-up note in
// docs/dev/architecture/viz-controls-and-interactions.md.

let _ws = null;

export function setWebSocket(ws) {
    _ws = ws;
}

export function sendEvent(target, event, data = {}) {
    if (!_ws || _ws.readyState !== WebSocket.OPEN) return;
    _ws.send(JSON.stringify({ type: 'event', target, event, data }));
}

// Reserved backend control id that receives browser log events.
export const CLIENT_LOG_ID = 'client_log';

export function sendLog(level, message, { source = null, data = null } = {}) {
    sendEvent(CLIENT_LOG_ID, 'log', { level, message, source, data });
}

// Opt-in trace forwarding: when enabled, the frontend `_log(...)` init/WS
// trace lines are also sent to the backend log at `info` level (off by default).
let _logForwarding = false;

export function setLogForwarding(enabled) {
    _logForwarding = enabled;
}

export function logForwardingEnabled() {
    return _logForwarding;
}
