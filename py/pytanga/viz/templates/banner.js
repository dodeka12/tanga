// Tanga Viewer — banner manager.  Owns a singleton full-screen `OverlayView`
// mounted on `document.body` and the id → `BannerView` map for global banners.

import { getOverlay } from './overlay.js';
import { BannerView } from './views/banner-view.js';

let _ws = null;
const _banners = new Map();

export function setWebSocket(ws) {
    _ws = ws;
}

function _notifyClosed(id) {
    if (_ws && _ws.readyState === WebSocket.OPEN) {
        _ws.send(JSON.stringify({ type: 'banner_closed', id }));
    }
}

export function handleBannerDefine(msg) {
    _removeBanner(msg.id);
    const view = new BannerView({
        id: msg.id,
        title: msg.title,
        text: msg.text,
        align_x: msg.align_x,
        align_y: msg.align_y,
        auto_hide: msg.auto_hide,
        dismissable: msg.dismissable,
        controls: msg.controls || [],
        backdropMode: 'fixed',
        onClose: _notifyClosed,
    });
    _banners.set(msg.id, view);
    getOverlay().addChild(view);
}

export function handleBannerRemove(msg) {
    _removeBanner(msg.id);
}

export function handleBannerClear() {
    for (const id of [..._banners.keys()]) _removeBanner(id);
}

function _removeBanner(id) {
    const view = _banners.get(id);
    if (!view) return;
    _banners.delete(id);
    getOverlay().removeChild(view);
    view.destroy();
}
