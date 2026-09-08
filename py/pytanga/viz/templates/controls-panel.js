// Tanga 3D Viewer — shared control core.
// Registry, event dispatch, icon rendering, and shared helpers used by the
// per-control DOM factories in controls/*.js and by the layout views.

import { sendEvent } from './events.js';

// ── Module state ─────────────────────────────────────────────
let _controlRegistry = {};      // control id → { kind, apply(value) }

// Throttle helpers (sliders send at ≤25 Hz while dragging; final state always flushed via change event)
const _throttleTimers = {};
const _throttleLast = {};
const _pendingThrottle = {};
const THROTTLE_MS = 40;

// ── Public API (called from viewer.js) ──────────────────────

/**
 * Apply a server-driven `control_update` to a rendered control's DOM value
 * without firing a `control:change` event.  No-ops for unknown/unrendered ids.
 */
export function applyControlValue(id, value) {
    const entry = _controlRegistry[id];
    if (!entry) {
        console.debug('[tanga] control_update for unknown id:', id);
        return;
    }
    entry.apply(value);
}

/**
 * Deliver a server-driven `enum_options` reply to a rendered table's open
 * custom-enum editor.  No-ops when the control is unknown or has no pending
 * request matching `requestId`.
 */
export function applyEnumOptions(id, requestId, values) {
    const entry = _controlRegistry[id];
    if (!entry || typeof entry.applyEnumOptions !== 'function') return;
    entry.applyEnumOptions(requestId, values);
}

/**
 * Drop a control's registry entry (e.g. when a transient overlay such as a
 * dialog is unmounted) so later `control_update` messages for that id no-op.
 */
export function forgetControl(id) {
    delete _controlRegistry[id];
}

export function registerControl(id, entry) {
    _controlRegistry[id] = entry;
}

// ── Icon rendering ──────────────────────────────────────────

const _iconFontLinks = {
    material: 'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200',
};

function _ensureIconFont(family) {
    const href = _iconFontLinks[family];
    if (!href) return;
    const id = 'tanga-icon-font-' + family;
    if (document.getElementById(id)) return;
    const link = document.createElement('link');
    link.id = id;
    link.rel = 'stylesheet';
    link.href = href;
    document.head.appendChild(link);
}

export function createIconElement(iconId) {
    const id = String(iconId || '');
    const idx = id.indexOf(':');
    const family = idx >= 0 ? id.slice(0, idx) : 'material';
    const name = idx >= 0 ? id.slice(idx + 1) : id;

    if (family === 'material') {
        _ensureIconFont('material');
        const span = document.createElement('span');
        span.className = 'material-symbols-outlined';
        span.textContent = name;
        return span;
    }
    if (family === 'uc') {
        const span = document.createElement('span');
        span.className = 'tanga-icon-uc';
        span.textContent = name;
        return span;
    }
    const span = document.createElement('span');
    span.className = 'tanga-icon-uc';
    span.textContent = id;
    return span;
}

// ── Shared control helpers ───────────────────────────────────

function _applyTooltip(wrapper, ctrl) {
    if (ctrl && ctrl.tooltip) wrapper.title = ctrl.tooltip;
}
export { _applyTooltip as applyTooltip };

export function attachDebouncedChange(input, controlId) {
    let debounceTimer = null;
    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            sendControlEvent('control:change', controlId, input.value);
        }, 400);
    });
    input.addEventListener('change', () => {
        clearTimeout(debounceTimer);
        sendControlEvent('control:change', controlId, input.value);
    });
}

// ── WebSocket event dispatch ────────────────────────────────

const _CONTROL_EVENTS = {
    'control:change': 'change',
    'control:click': 'click',
    'control:press': 'press',
    'control:release': 'release',
    'control:cell_change': 'cell_change',
    'control:cell_select': 'cell_select',
    'control:row_add': 'row_add',
    'control:column_add': 'column_add',
    'control:row_delete': 'row_delete',
    'control:column_delete': 'column_delete',
    'control:column_title_change': 'column_title_change',
    'control:column_type_change': 'column_type_change',
    'control:enum_options': 'enum_options',
    'control:undo': 'undo',
    'control:redo': 'redo',
    'control:table_view_change': 'table_view_change',
    'control:group_toggle': 'group_toggle',
};

/**
 * Map a keyboard-event shape to the undo/redo action it requests, or ``null``.
 *
 * Pure helper (no DOM) so the key mapping is unit-testable:
 * Ctrl+Z → ``"undo"``, Ctrl+Shift+Z or Ctrl+Y → ``"redo"``, otherwise ``null``.
 */
export function resolveUndoRedoAction(e) {
    if (!e.ctrlKey) return null;
    const key = (e.key || '').toLowerCase();
    if (key === 'z') {
        return e.shiftKey ? 'redo' : 'undo';
    }
    if (key === 'y') {
        return 'redo';
    }
    return null;
}

export function sendControlEvent(type, controlId, value) {
    const event = _CONTROL_EVENTS[type];
    if (!event) return;
    const data = {};
    if (value !== null && value !== undefined) {
        data.value = value;
    }
    sendEvent(controlId, event, data);
}

/**
 * Throttled send: sends immediately if no recent send, otherwise queues
 * a trailing send so the final value is always delivered.
 */
export function throttledSend(type, controlId, value) {
    const key = type + ':' + controlId;
    const now = Date.now();

    // Always remember the latest value for the final flush
    _pendingThrottle[key] = value;

    if (!_throttleLast[key]) {
        // First event — send immediately
        _throttleLast[key] = now;
        sendControlEvent(type, controlId, value);
        return;
    }

    const elapsed = now - _throttleLast[key];
    if (elapsed >= THROTTLE_MS) {
        // Enough time passed — send immediately
        _throttleLast[key] = now;
        // Clear any pending trailing timer since we just sent
        if (_throttleTimers[key]) {
            clearTimeout(_throttleTimers[key]);
            delete _throttleTimers[key];
        }
        sendControlEvent(type, controlId, value);
    } else {
        // Within the throttle window — schedule a trailing send
        // that fires when the silence window expires
        if (!_throttleTimers[key]) {
            _throttleTimers[key] = setTimeout(() => {
                delete _throttleTimers[key];
                _throttleLast[key] = Date.now();
                if (_pendingThrottle[key] !== undefined) {
                    sendControlEvent(type, controlId, _pendingThrottle[key]);
                }
            }, THROTTLE_MS - elapsed);
        }
    }
}

/**
 * Flush any pending throttled value immediately (called on 'change' event
 * when the user releases the slider).
 */
export function throttledFlush(type, controlId) {
    const key = type + ':' + controlId;
    if (_throttleTimers[key]) {
        clearTimeout(_throttleTimers[key]);
        delete _throttleTimers[key];
    }
    if (_pendingThrottle[key] !== undefined) {
        sendControlEvent(type, controlId, _pendingThrottle[key]);
        _throttleLast[key] = Date.now();
    }
}
