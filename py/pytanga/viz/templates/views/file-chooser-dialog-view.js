// Tanga Viewer — `FileChooserDialogView`: the `FileChooserDialog` chrome.
// Extends `DialogView` so it keeps the title bar / ✕ / drag / resize behavior,
// and mounts the serialized `FileChooserView` listing plus a footer with a path
// line and OK/Cancel buttons.  OK fires `accept`; Cancel/✕ fire `close`.

import { DialogView } from './dialog-view.js';
import { sendEvent } from '../events.js';

export class FileChooserDialogView extends DialogView {
    constructor({
        id,
        title = 'Select a file',
        content = null,
        align_x = 0.5,
        align_y = 0.5,
        dismissable = true,
        width = null,
        height = null,
        ws = null,
    } = {}) {
        super({ id, title, content, align_x, align_y, dismissable, width, height, ws });
        this._selectedPath = '';
        this._pathEl = null;
    }

    _buildContent() {
        super._buildContent();
        if (this._contentView && typeof this._contentView.on === 'function') {
            this._contentView.on('select', (e) => this._onSelect(e.detail && e.detail.path));
        }
        this._buildFooter();
    }

    _buildFooter() {
        const footer = document.createElement('div');
        footer.className = 'tanga-file-chooser-footer';

        this._pathEl = document.createElement('div');
        this._pathEl.className = 'tanga-file-chooser-path';
        footer.appendChild(this._pathEl);

        const actions = document.createElement('div');
        actions.className = 'tanga-file-chooser-actions';

        const ok = document.createElement('button');
        ok.type = 'button';
        ok.className = 'tanga-action-button';
        ok.textContent = 'OK';
        ok.addEventListener('click', () => {
            sendEvent(this.dialogId, 'accept');
            this._dismiss(false);
        });

        const cancel = document.createElement('button');
        cancel.type = 'button';
        cancel.className = 'tanga-action-button';
        cancel.textContent = 'Cancel';
        cancel.addEventListener('click', () => this._dismiss(true));

        actions.appendChild(ok);
        actions.appendChild(cancel);
        footer.appendChild(actions);
        this.el.appendChild(footer);
    }

    _onSelect(path) {
        this._selectedPath = path || '';
        if (this._pathEl) this._pathEl.textContent = this._selectedPath;
    }
}
