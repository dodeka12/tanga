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
