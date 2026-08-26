// Tanga Viewer — file browser manager.  Owns the single open (modal)
// `FileBrowserView`, mounted into the shared `OverlayView`.

import { getOverlay } from './overlay.js';
import { FileBrowserView } from './views/file-browser-view.js';

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

export function openFileBrowser(controlId, path) {
    _close();
    _view = new FileBrowserView({
        controlId,
        path: path || '',
        onNavigate: (p) => _send({ type: 'file_browser_navigate', control_id: controlId, path: p }),
        onSelect: (p) => {
            _send({ type: 'file_browser_select', control_id: controlId, path: p });
            _close();
        },
        onClose: () => _close(),
    });
    getOverlay().addChild(_view);
}

export function handleFileBrowserShow(msg) {
    openFileBrowser(msg.control_id, msg.path || '');
}

export function handleFileBrowserListing(msg) {
    if (!_view || _view.controlId !== msg.control_id) return;
    _view.updateListing(msg.path || '', msg.entries || [], msg.error || null);
}

export function handleFileBrowserClose(msg) {
    if (_view && _view.controlId === msg.control_id) _close();
}

function _close() {
    if (!_view) return;
    getOverlay().removeChild(_view);
    _view.destroy();
    _view = null;
}
