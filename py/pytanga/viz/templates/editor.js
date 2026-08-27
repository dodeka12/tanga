// Tanga Viewer — editor manager.  Owns the single open `EditorView`, mounted
// into the shared `OverlayView`.

import { getOverlay } from './overlay.js';
import { EditorView } from './views/editor-view.js';

let _ws = null;
let _view = null;

export function setWebSocket(ws) {
    _ws = ws;
}

function _send(msg) {
    if (_ws && _ws.readyState === WebSocket.OPEN) {
        _ws.send(JSON.stringify(msg));
    }
}

export function handleEditorDefine(msg) {
    _close();
    const view = new EditorView({
        id: msg.id,
        label: msg.label || '',
        value: msg.value || '',
        onClose: (id, text) => {
            _send({ type: 'editor_closed', id, text });
            _close();
        },
    });
    _view = view;
    getOverlay().addChild(view);
}

function _close() {
    if (!_view) return;
    getOverlay().removeChild(_view);
    _view.destroy();
    _view = null;
}
