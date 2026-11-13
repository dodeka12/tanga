// Tanga 3D Viewer — shared control core.
// Registry, event dispatch, icon rendering, and shared helpers used by the
// per-control DOM factories in controls/*.js and by the layout views.

import { sendEvent } from './events.js';
import { getStatefulView } from './views/view-state.js';

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

/**
 * Apply a server-driven `control_state` change to a rendered control's DOM.
 * `enabled=false` greys the control out and disables its inputs; `visible=false`
 * hides it (`display:none`) without removing it from the layout.
 */
export function applyControlStateToElement(wrapper, state) {
    if (!wrapper) return;
    if (state.enabled !== undefined) {
        const enabled = !!state.enabled;
        wrapper.classList.toggle('tanga-control-disabled', !enabled);
        wrapper.querySelectorAll('input, select, textarea, button').forEach((el) => {
            el.disabled = !enabled;
            // Chromium does not fully re-arm a native `<input type="range">`
            // after `disabled` is cleared: the first thumb drag advances a
            // single step, then stops until the track is clicked.  Re-insert
            // the node so the browser rebuilds the slider's drag state.
            if (enabled && el.type === 'range' && el.parentNode) {
                el.parentNode.insertBefore(el, el.nextSibling);
            }
        });
    }
    if (state.visible !== undefined) {
        wrapper.style.display = state.visible ? '' : 'none';
    }
    if (state.selected !== undefined) {
        wrapper.classList.toggle('tanga-control-selected', !!state.selected);
    }
    if (state.tooltip !== undefined) {
        applyTooltip(wrapper, state.tooltip);
    }
    if (state.min !== undefined || state.max !== undefined || state.step !== undefined) {
        const range = wrapper.querySelector('input[type="range"]');
        if (range) {
            if (state.min !== undefined) range.min = String(state.min);
            if (state.max !== undefined) range.max = String(state.max);
            if (state.step !== undefined) range.step = String(state.step);
            // The browser auto-clamps `range.value` when min/max change; sync
            // the readout so it matches.
            const readout = wrapper.querySelector('.tanga-value');
            if (readout) readout.textContent = range.value;
        }
    }
}

/**
 * Apply a server-driven `control_state` change to a rendered control by id.
 * No-ops for unknown/unrendered ids.
 *
 * Visibility is deliberately left to the hosting view when there is one (every
 * built control has one): the view hides itself and its enclosing Parameters
 * row, so toggling `display` on the bare widget here would fight the layout.
 */
export function applyControlState(id, state) {
    const entry = _controlRegistry[id];
    if (!entry || !entry.el) {
        console.debug('[tanga] control_state for unknown id:', id);
        return;
    }
    const widgetState = (getStatefulView(id) && state.visible !== undefined)
        ? { ...state, visible: undefined }
        : state;
    if (typeof entry.applyState === 'function') {
        entry.applyState(widgetState);
    } else {
        applyControlStateToElement(entry.el, widgetState);
    }
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

// ── Tooltips ─────────────────────────────────────────────────
// Every framework tooltip goes through `applyTooltip`: it records the intended
// text in `data-tanga-tooltip` and mirrors it to the native `title` attribute.
// Keeping the text in an attribute lets `setTooltipsEnabled()` mute or restore
// every tooltip on the page without any per-view bookkeeping.

const TOOLTIP_ATTR = 'data-tanga-tooltip';
let _tooltipsEnabled = true;

function _syncTooltipTitle(el) {
    const text = el.getAttribute(TOOLTIP_ATTR);
    if (text && _tooltipsEnabled) el.title = text;
    else el.removeAttribute('title');
}

/**
 * Set (or clear, for an empty text) an element's native tooltip.
 *
 * `source` is either a serialization object with a `tooltip` field or a plain
 * string.  Pass `''` to clear the tooltip.
 */
export function applyTooltip(el, source) {
    if (!el) return;
    const text = typeof source === 'string'
        ? source
        : ((source && source.tooltip) || '');
    if (text) el.setAttribute(TOOLTIP_ATTR, text);
    else el.removeAttribute(TOOLTIP_ATTR);
    _syncTooltipTitle(el);
}

/** Enable/disable every framework tooltip on the page (page-level switch). */
export function setTooltipsEnabled(enabled) {
    _tooltipsEnabled = !!enabled;
    document.querySelectorAll(`[${TOOLTIP_ATTR}]`).forEach(_syncTooltipTitle);
}

/** Whether framework tooltips are currently shown. */
export function tooltipsEnabled() {
    return _tooltipsEnabled;
}
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
