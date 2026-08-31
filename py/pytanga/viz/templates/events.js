// Tanga Viewer — unified client→server event sending.
//
// Every frontend element that reports a user action to the backend sends one
// envelope through `sendEvent`:
//
//   { type: "event", target: "<id>", event: "<name>", data: {…} }
//
// `target` is the globally-unique control/object id, `event` is the short event
// name ("change", "click", "close", "interaction:drag_move", …), and `data` is
// the event payload (typically `{ value }`).  Interactions use the
// `interaction:` namespaced names (routed to the coalescing dispatcher).

let _ws = null;

export function setWebSocket(ws) {
    _ws = ws;
}

export function sendEvent(target, event, data = {}) {
    if (!_ws || _ws.readyState !== WebSocket.OPEN) return;
    _ws.send(JSON.stringify({ type: 'event', target, event, data }));
}
