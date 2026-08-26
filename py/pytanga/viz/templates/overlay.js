// Tanga Viewer — shared full-screen overlay singleton.
// Banners and the file browser mount their views into this one container.

import { OverlayView } from './views/overlay-view.js';

let _overlay = null;

export function getOverlay() {
    if (!_overlay) {
        _overlay = new OverlayView();
        _overlay.mount(document.body);
    }
    return _overlay;
}
