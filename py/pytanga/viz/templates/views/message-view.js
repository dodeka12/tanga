// Tanga Viewer — `MessageView`: a live, scrollable two-column (time | message)
// list.  Rows alternate shading via CSS; appends auto-scroll only when already
// at the bottom, and `max_history` (when set) mirrors the backend's FIFO
// drop-oldest.

import { View } from './view.js';

const _messageViews = new Map(); // id → MessageView (runtime registry)

export function registerMessageView(id, view) {
    _messageViews.set(id, view);
}

export function forgetMessageView(id) {
    _messageViews.delete(id);
}

/** Route a server update message to the registered `MessageView` (no-op if unknown). */
export function applyMessageUpdate(msg) {
    const view = _messageViews.get(msg.id);
    if (!view) return;
    if (msg.action === 'clear') {
        view.clearLines();
    } else if (msg.action === 'replace') {
        view.replaceLines(msg.lines || []);
    } else {
        view.appendLines(msg.lines || []);
    }
}

export class MessageView extends View {
    constructor({ id = null, max_history = null, lines = [] } = {}) {
        super();
        this.messageId = id;
        this.maxHistory = max_history;
        this.initialLines = lines || [];
        this.el.classList.add('tanga-message-view');
        this.el.style.overflow = 'auto';
    }

    _onMounted() {
        for (const line of this.initialLines) this._appendRow(line);
    }

    /** Column 2 text: `message` if present, else JSON of the non-`time` keys. */
    _messageOf(line) {
        if (line && line.message != null) return String(line.message);
        const rest = {};
        for (const key of Object.keys(line || {})) {
            if (key !== 'time') rest[key] = line[key];
        }
        return JSON.stringify(rest);
    }

    _appendRow(line) {
        const row = document.createElement('div');
        row.className = 'tanga-message-row';

        const time = document.createElement('div');
        time.className = 'tanga-message-time';
        time.textContent = line && line.time != null ? String(line.time) : '';
        row.appendChild(time);

        const message = document.createElement('div');
        message.className = 'tanga-message-text';
        message.textContent = this._messageOf(line);
        row.appendChild(message);

        this.el.appendChild(row);
        return row;
    }

    _atBottom() {
        const el = this.el;
        const threshold = 4;
        return el.scrollTop + el.clientHeight >= el.scrollHeight - threshold;
    }

    appendLines(lines) {
        if (!lines || !lines.length) return;
        const atBottom = this._atBottom();
        for (const line of lines) this._appendRow(line);
        if (this.maxHistory != null) {
            while (this.el.children.length > this.maxHistory) {
                this.el.removeChild(this.el.children[0]);
            }
        }
        if (atBottom) this.el.scrollTop = this.el.scrollHeight;
    }

    clearLines() {
        this.el.replaceChildren();
    }

    replaceLines(lines) {
        this.el.replaceChildren();
        for (const line of lines || []) this._appendRow(line);
        this.el.scrollTop = this.el.scrollHeight;
    }

    destroy() {
        if (this.messageId != null) forgetMessageView(this.messageId);
        super.destroy();
    }
}
