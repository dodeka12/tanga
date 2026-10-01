// Tanga Viewer — `FileChooserDialogView`: the `FileChooserDialog` chrome.
// Extends `DialogView` so it keeps the title bar / ✕ / drag / resize behavior,
// and mounts the serialized `FileChooserView` listing plus a footer with an
// editable filename field and OK/Cancel buttons.  OK fires `accept` carrying the
// full path; Cancel/✕ fire `close`.

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
        this._nameInput = null;
        this._dirEl = null;
        this._okBtn = null;
        // Open mode (default) requires an existing file; save mode allows a new name.
        this.existing_only = (content && content.existing_only) !== false;
        this._directory = '';
        this._fileNames = [];
        this._filename = '';
    }

    _buildContent() {
        super._buildContent();
        if (this._contentView && typeof this._contentView.on === 'function') {
            this._contentView.on('select', (e) => this._onSelect(e.detail && e.detail.path));
            this._contentView.on('accept', (e) => this._onAccept(e.detail && e.detail.path));
            this._contentView.on('navigate', (e) => this._onNavigate(e.detail || {}));
        }
        this._buildFooter();
        // A pre-set value counts as the current selection.
        if (this._contentView && this._contentView.value) {
            this._onSelect(this._contentView.value);
        }
    }

    _buildFooter() {
        const footer = document.createElement('div');
        footer.className = 'tanga-file-chooser-footer';

        this._dirEl = document.createElement('div');
        this._dirEl.className = 'tanga-file-chooser-path';
        footer.appendChild(this._dirEl);

        this._nameInput = document.createElement('input');
        this._nameInput.type = 'text';
        this._nameInput.className = 'tanga-text-input';
        this._nameInput.placeholder = 'Filename';
        this._nameInput.addEventListener('input', () => this._onInput());
        footer.appendChild(this._nameInput);

        const actions = document.createElement('div');
        actions.className = 'tanga-file-chooser-actions';

        const ok = document.createElement('button');
        ok.type = 'button';
        ok.className = 'tanga-action-button';
        ok.textContent = 'OK';
        ok.disabled = true;
        ok.addEventListener('click', () => this._submit());
        this._okBtn = ok;

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

    _onNavigate(detail) {
        this._directory = detail.path || '';
        this._fileNames = detail.files || [];
        if (this._dirEl) this._dirEl.textContent = this._directory;
        this._updateOk();
    }

    _onInput() {
        this._filename = this._nameInput.value;
        if (this._contentView && typeof this._contentView.filter === 'function') {
            this._contentView.filter(this._filename);
        }
        this._updateOk();
    }

    _onSelect(path) {
        this._selectedPath = path || '';
        this._filename = _basename(path || '');
        if (this._nameInput) this._nameInput.value = this._filename;
        this._updateOk();
    }

    _onAccept(path) {
        if (path) this._onSelect(path);
        this._submit();
    }

    _updateOk() {
        const name = this._filename.trim();
        let ok = name.length > 0;
        if (ok && this.existing_only) {
            ok = this._fileNames.includes(name);
        }
        if (this._okBtn) this._okBtn.disabled = !ok;
    }

    _submit() {
        const name = this._filename.trim();
        if (!name) return;
        if (this.existing_only && !this._fileNames.includes(name)) return;
        const path = this._directory ? this._directory + '/' + name : name;
        sendEvent(this.dialogId, 'accept', { value: path });
        this._dismiss(false);
    }
}

/** Last path segment of a `/`- or `\`-separated path ("" when none). */
function _basename(path) {
    const parts = String(path || '').split(/[\\/]/).filter((p) => p !== '');
    return parts.length ? parts[parts.length - 1] : '';
}

