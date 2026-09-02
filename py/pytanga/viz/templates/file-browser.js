// Tanga Viewer — file browser manager.
//
// Owns the routing registry that maps a control id to its browser view (either
// the single open modal `FileBrowserView`, or an embedded `FileChooserView`).
// The registry itself is long-lived because `file_browser_listing` pushes are
// keyed only by `control_id`; the browser *views* are created on demand and
// released when they unmount.

import { getOverlay } from './overlay.js';
import { FileBrowserView } from './views/file-browser-view.js';
import { sendEvent } from './events.js';

export class FileBrowserManager {
    constructor(overlay) {
        this._overlay = overlay;
        // control_id -> view exposing `updateListing(path, entries, error)`.
        this._views = new Map();
        // The single open modal browser (or null).
        this._modal = null;
    }

    register(controlId, view) {
        this._views.set(controlId, view);
    }

    unregister(controlId) {
        if (this._views.get(controlId) === undefined) return;
        this._views.delete(controlId);
    }

    openModal(controlId, path) {
        this.closeModal();
        const view = new FileBrowserView({
            controlId,
            path: path || '',
            onNavigate: (p) => sendEvent(controlId, 'file_browser_navigate', { path: p }),
            onSelect: (p) => {
                sendEvent(controlId, 'file_browser_select', { path: p });
                this.closeModal();
            },
            onClose: () => this.closeModal(),
        });
        this._modal = view;
        this._views.set(controlId, view);
        this._overlay.addChild(view);
    }

    closeModal() {
        if (!this._modal) return;
        const view = this._modal;
        this._modal = null;
        this._views.delete(view.controlId);
        this._overlay.removeChild(view);
        view.destroy();
    }

    handleShow(msg) {
        this.openModal(msg.control_id, msg.path || '');
    }

    handleListing(msg) {
        const view = this._views.get(msg.control_id);
        if (view && typeof view.updateListing === 'function') {
            view.updateListing(msg.path || '', msg.entries || [], msg.error || null, msg.parent);
        }
    }

    handleClose(msg) {
        if (this._modal && this._modal.controlId === msg.control_id) {
            this.closeModal();
        }
    }
}

export const fileBrowser = new FileBrowserManager(getOverlay());

// Convenience re-exports (keep the existing message/control call sites working).
export function openFileBrowser(controlId, path) {
    fileBrowser.openModal(controlId, path);
}

export function registerFileBrowser(controlId, view) {
    fileBrowser.register(controlId, view);
}

export function unregisterFileBrowser(controlId) {
    fileBrowser.unregister(controlId);
}

export function handleFileBrowserShow(msg) {
    fileBrowser.handleShow(msg);
}

export function handleFileBrowserListing(msg) {
    fileBrowser.handleListing(msg);
}

export function handleFileBrowserClose(msg) {
    fileBrowser.handleClose(msg);
}
