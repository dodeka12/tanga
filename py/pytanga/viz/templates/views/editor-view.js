// Tanga Viewer — `EditorView`: a transient multi-line text editor overlay.

import { View } from './view.js';

export class EditorView extends View {
    constructor({ id, label = '', value = '', onClose = null } = {}) {
        super();
        this.editorId = id;
        this.label = label;
        this.value = value;
        this.onClose = onClose;
        this._textarea = null;

        this.el.classList.add('tanga-editor');
        Object.assign(this.el.style, {
            position: 'absolute',
            bottom: '0',
            left: '50%',
            transform: 'translateX(-50%)',
            width: '90%',
            maxWidth: '900px',
            zIndex: '2',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
            background: 'rgba(20, 20, 40, 0.97)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '6px',
            padding: '10px 12px',
            boxShadow: '0 6px 24px rgba(0, 0, 0, 0.6)',
            fontFamily: 'sans-serif',
            color: '#ddd',
            pointerEvents: 'auto',
            boxSizing: 'border-box',
        });

        if (label) {
            const labelEl = document.createElement('div');
            labelEl.textContent = label;
            Object.assign(labelEl.style, { fontSize: '13px', color: '#aaa' });
            this.el.appendChild(labelEl);
        }

        const textarea = document.createElement('textarea');
        textarea.value = value || '';
        textarea.rows = 6;
        Object.assign(textarea.style, {
            width: '100%',
            minHeight: '120px',
            maxHeight: '40vh',
            resize: 'vertical',
            background: 'rgba(255, 255, 255, 0.08)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '4px',
            color: '#ddd',
            fontFamily: 'monospace',
            fontSize: '13px',
            padding: '8px 10px',
            outline: 'none',
            boxSizing: 'border-box',
        });
        this._textarea = textarea;
        this.el.appendChild(textarea);

        const btnRow = document.createElement('div');
        Object.assign(btnRow.style, {
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '8px',
        });

        const keep = this._makeButton('\u2713', 'Keep changes', () => {
            if (this.onClose) this.onClose(this.editorId, textarea.value);
        });
        const discard = this._makeButton('\u2715', 'Discard changes', () => {
            if (this.onClose) this.onClose(this.editorId, null);
        });
        btnRow.appendChild(keep);
        btnRow.appendChild(discard);
        this.el.appendChild(btnRow);
    }

    _makeButton(glyph, title, onClick) {
        const btn = document.createElement('button');
        btn.textContent = glyph;
        btn.title = title;
        Object.assign(btn.style, {
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '4px',
            color: '#ddd',
            cursor: 'pointer',
            fontSize: '14px',
            padding: '4px 12px',
            lineHeight: '1',
        });
        btn.addEventListener('click', onClick);
        return btn;
    }

    _onMounted() {
        if (this._textarea) this._textarea.focus();
    }
}
