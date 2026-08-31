// Tanga Viewer — editor manager.  Owns the single open `EditorView`, mounted
// into the shared `OverlayView`.

import { getOverlay } from './overlay.js';
import { EditorView } from './views/editor-view.js';
import { sendEvent } from './events.js';

let _view = null;

export function handleEditorDefine(msg) {
    _close();
    const view = new EditorView({
        id: msg.id,
        label: msg.label || '',
        value: msg.value || '',
        onClose: (id, text) => {
            sendEvent(id, 'close', { value: text });
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
