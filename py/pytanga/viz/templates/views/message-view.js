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
    constructor({
        id = null,
        max_history = null,
        lines = [],
        show_date = false,
        show_utc_offset = false,
    } = {}) {
        super();
        this.messageId = id;
        this.maxHistory = max_history;
        this.initialLines = lines || [];
        this.showDate = show_date;
        this.showUtcOffset = show_utc_offset;
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

    /**
     * Column 1 text: the stored UTC ISO-8601 timestamp rendered in the
     * browser's local timezone.  `show_date` / `show_utc_offset` add the local
     * date and the local offset to UTC; the time (with microseconds, when the
     * source string carries them) is always shown.
     */
    _timeOf(line) {
        const raw = line && line.time != null ? String(line.time) : '';
        const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?$/.exec(raw);
        if (!m) return raw;

        const [, year, month, day, hour, minute, second, frac, zone] = m;

        // Stored offset → minutes east of UTC (default 0 = UTC).
        let zoneMin = 0;
        if (zone && zone !== 'Z') {
            const sign = zone[0] === '-' ? -1 : 1;
            const [hh, mm] = zone.slice(1).split(':');
            zoneMin = sign * (Number(hh) * 60 + Number(mm || 0));
        }

        // Wall-clock time (in the stored zone) → UTC instant → local time.
        const utcMs = Date.UTC(+year, +month - 1, +day, +hour, +minute, +second) - zoneMin * 60000;
        const d = new Date(utcMs);

        const pad = (n) => String(n).padStart(2, '0');
        const time = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}${frac ? '.' + frac : ''}`;
        const date = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

        const offMin = -d.getTimezoneOffset();
        const off = `${offMin >= 0 ? '+' : '-'}${pad(Math.floor(Math.abs(offMin) / 60))}:${pad(Math.abs(offMin) % 60)}`;

        const parts = [];
        if (this.showDate) parts.push(date);
        parts.push(time);
        if (this.showUtcOffset) parts.push(off);
        return parts.join(' ');
    }

    _appendRow(line) {
        const row = document.createElement('div');
        row.className = 'tanga-message-row';

        const time = document.createElement('div');
        time.className = 'tanga-message-time';
        time.textContent = this._timeOf(line);
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
