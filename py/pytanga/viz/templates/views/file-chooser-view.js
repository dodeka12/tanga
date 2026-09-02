// Tanga Viewer — `FileChooserView`: the bare file-selection (directory listing)
// view, embeddable in any view container.  It shows only the backend-driven
// listing — no path field, no browse button — and reports navigation/selection
// through `file_browser_navigate` / `file_browser_select` events.

import { ControlView } from './control-view.js';
import { sendEvent } from '../events.js';
import { registerFileBrowser, unregisterFileBrowser } from '../file-browser.js';

export class FileChooserView extends ControlView {
    constructor({ id, value = '', root = null, accept = '' } = {}) {
        super({ id, label: '', tooltip: '' });
        this.value = value;
        this.root = root;
        this.accept = accept;
        this._currentPath = value || root || '';
        this._parentPath = null;
        this._pathText = null;
        this._listEl = null;

        // A directory listing needs more room than a single form control.
        this.minWidth = { value: 220, unit: 'px' };
        this.minHeight = { value: 160, unit: 'px' };

        // Fill a flex parent (e.g. a dialog body) and scroll internally, so the
        // listing keeps the dimensions its container gives it instead of
        // growing/shrinking with the number of entries.
        Object.assign(this.el.style, {
            display: 'flex',
            flexDirection: 'column',
            flexGrow: '1',
            flexShrink: '1',
            minWidth: '0',
            minHeight: '0',
        });
    }

    render() {
        const wrapper = document.createElement('div');
        wrapper.className = 'tanga-file-browser tanga-file-chooser-view';
        Object.assign(wrapper.style, {
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            flex: '1',
            minHeight: '0',
            overflow: 'hidden',
        });

        // Path bar: current directory + "Up" button.
        this._pathText = document.createElement('span');
        Object.assign(this._pathText.style, {
            flex: '1',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            fontSize: '12px',
            color: '#aaa',
        });
        const upBtn = document.createElement('button');
        upBtn.textContent = '⬆ Up';
        upBtn.title = 'Parent directory';
        upBtn.addEventListener('click', () => this._up());

        const pathBar = document.createElement('div');
        Object.assign(pathBar.style, { display: 'flex', gap: '8px', alignItems: 'center' });
        pathBar.appendChild(upBtn);
        pathBar.appendChild(this._pathText);
        wrapper.appendChild(pathBar);

        // Entry list.
        this._listEl = document.createElement('div');
        Object.assign(this._listEl.style, {
            flex: '1',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '2px',
            minHeight: '0',
        });
        wrapper.appendChild(this._listEl);

        this._pathText.textContent = this._currentPath;
        return wrapper;
    }

    _onMounted() {
        super._onMounted();
        registerFileBrowser(this.controlId, this);
        this._navigate(this._currentPath);
    }

    _navigate(path) {
        sendEvent(this.controlId, 'file_browser_navigate', { path });
    }

    _up() {
        if (this._parentPath) this._navigate(this._parentPath);
    }

    updateListing(path, entries, error, parent) {
        this._currentPath = path;
        this._parentPath = parent || null;
        this._pathText.textContent = path;
        this._listEl.innerHTML = '';

        if (error) {
            const msg = document.createElement('div');
            msg.textContent = error === 'permission' ? 'Permission denied.' : 'Directory not found.';
            msg.style.color = '#f88';
            this._listEl.appendChild(msg);
            return;
        }

        for (const entry of entries) {
            const row = document.createElement('div');
            row.textContent = (entry.is_dir ? '📁 ' : '📄 ') + entry.name;
            Object.assign(row.style, {
                display: 'flex',
                gap: '6px',
                alignItems: 'center',
                padding: '4px 8px',
                borderRadius: '4px',
                cursor: 'pointer',
            });
            row.addEventListener('mouseenter', () => { row.style.background = 'rgba(255,255,255,0.08)'; });
            row.addEventListener('mouseleave', () => { row.style.background = 'transparent'; });
            row.addEventListener('click', () => {
                if (entry.is_dir) {
                    this._navigate(entry.path);
                } else {
                    sendEvent(this.controlId, 'file_browser_select', { path: entry.path });
                    this.emit('select', { path: entry.path });
                }
            });
            this._listEl.appendChild(row);
        }
    }

    destroy() {
        unregisterFileBrowser(this.controlId);
        super.destroy();
    }
}
