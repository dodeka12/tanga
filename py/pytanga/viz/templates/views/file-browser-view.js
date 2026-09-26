// Tanga Viewer — `FileBrowserView`: a modal file-browser dialog rendered as a
// `View`, mounted into the shared `OverlayView`.  Directory listings come from
// the backend via `file_browser_navigate` / `file_browser_listing`.

import { View } from './view.js';

export class FileBrowserView extends View {
    constructor({ controlId, path = '', onNavigate, onSelect, onClose, folders_only = false } = {}) {
        super();
        this.controlId = controlId;
        this.onNavigate = onNavigate;
        this.onSelect = onSelect;
        this.onClose = onClose;
        this.folders_only = folders_only;
        this._currentPath = path;
        this._parentPath = null;
        this._selectedPath = null;
        this._selectedEl = null;

        this.el.classList.add('tanga-file-browser');

        // Dimmed, interaction-blocking backdrop (modal, like a non-dismissable
        // banner): grays out and blocks the surrounding visualization.
        this._backdrop = document.createElement('div');
        this._backdrop.className = 'tanga-file-browser-backdrop';
        Object.assign(this._backdrop.style, {
            position: 'fixed',
            top: '0', left: '0', right: '0', bottom: '0',
            background: 'rgba(0, 0, 0, 0.55)',
            pointerEvents: 'auto',
            zIndex: '1',
        });

        Object.assign(this.el.style, {
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            pointerEvents: 'auto',
            zIndex: '2',
            background: 'rgba(20, 20, 40, 0.97)',
            border: '1px solid rgba(255, 255, 255, 0.18)',
            borderRadius: '8px',
            padding: '14px 18px',
            fontFamily: 'sans-serif',
            fontSize: '14px',
            color: '#ddd',
            boxShadow: '0 6px 24px rgba(0, 0, 0, 0.6)',
            width: 'min(90vw, 560px)',
            maxHeight: '80vh',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
        });

        this._buildContent();
    }
    _buildContent() {
        const title = document.createElement('div');
        title.textContent = 'Select a file';
        Object.assign(title.style, {
            fontWeight: '600', fontSize: '16px', color: '#eee',
        });
        this.el.appendChild(title);

        // Path bar: current directory + "Up" button.
        this._pathText = document.createElement('span');
        Object.assign(this._pathText.style, {
            flex: '1', overflow: 'hidden', textOverflow: 'ellipsis',
            whiteSpace: 'nowrap', fontSize: '12px', color: '#aaa',
        });
        const upBtn = document.createElement('button');
        upBtn.textContent = '⬆ Up';
        upBtn.title = 'Parent directory';
        Object.assign(upBtn.style, { padding: '4px 10px', cursor: 'pointer' });
        upBtn.addEventListener('click', () => this._up());

        const pathBar = document.createElement('div');
        Object.assign(pathBar.style, { display: 'flex', gap: '8px', alignItems: 'center' });
        pathBar.appendChild(upBtn);
        pathBar.appendChild(this._pathText);
        if (this.folders_only) {
            const selectBtn = document.createElement('button');
            selectBtn.textContent = 'Select this folder';
            selectBtn.title = 'Accept the current directory';
            Object.assign(selectBtn.style, { padding: '4px 10px', cursor: 'pointer' });
            selectBtn.addEventListener('click', () => this._accept(this._currentPath));
            pathBar.appendChild(selectBtn);
        }
        this.el.appendChild(pathBar);

        // Entry list.
        this._listEl = document.createElement('div');
        Object.assign(this._listEl.style, {
            display: 'flex', flexDirection: 'column', gap: '2px',
            overflowY: 'auto', minHeight: '200px', maxHeight: '50vh',
        });
        this.el.appendChild(this._listEl);

        // Actions.
        const actions = document.createElement('div');
        Object.assign(actions.style, {
            display: 'flex', justifyContent: 'flex-end', gap: '8px',
        });
        const cancel = document.createElement('button');
        cancel.textContent = 'Cancel';
        Object.assign(cancel.style, { padding: '6px 14px', cursor: 'pointer' });
        cancel.addEventListener('click', () => {
            if (this.onClose) this.onClose();
        });
        actions.appendChild(cancel);
        this.el.appendChild(actions);

        this._pathText.textContent = this._currentPath;
        if (this.onNavigate) this.onNavigate(this._currentPath);
    }

    _up() {
        if (this._parentPath && this.onNavigate) this.onNavigate(this._parentPath);
    }

    _highlight(row, path) {
        if (this._selectedEl && this._selectedEl !== row) {
            this._selectedEl.style.background = 'transparent';
        }
        this._selectedEl = row;
        this._selectedPath = path;
        row.classList.add('selected');
        row.style.background = 'rgba(255,255,255,0.22)';
    }

    _accept(path) {
        if (this.onSelect) this.onSelect(path);
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
                display: 'flex', gap: '6px', alignItems: 'center',
                padding: '4px 8px', borderRadius: '4px', cursor: 'pointer',
            });
            row.addEventListener('mouseenter', () => {
                if (row !== this._selectedEl) row.style.background = 'rgba(255,255,255,0.08)';
            });
            row.addEventListener('mouseleave', () => {
                if (row !== this._selectedEl) row.style.background = 'transparent';
            });
            row.addEventListener('click', () => {
                if (entry.is_dir) {
                    if (this.onNavigate) this.onNavigate(entry.path);
                } else {
                    this._highlight(row, entry.path);
                }
            });
            row.addEventListener('dblclick', () => {
                if (entry.is_dir) {
                    if (this.onNavigate) this.onNavigate(entry.path);
                } else {
                    this._highlight(row, entry.path);
                    this._accept(entry.path);
                }
            });
            this._listEl.appendChild(row);
        }
    }

    _onMounted() {
        if (this._backdrop) {
            this.el.parentElement.insertBefore(this._backdrop, this.el);
        }
    }

    unmount() {
        if (this._backdrop && this._backdrop.parentElement) {
            this._backdrop.remove();
        }
        this._backdrop = null;
        super.unmount();
    }

    destroy() {
        this.unmount();
        super.destroy();
    }
}

