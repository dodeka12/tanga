// Tanga 3D Viewer — Control Panel
// DOM-based interactive controls (sliders, dropdowns, buttons) overlaid on the
// Three.js viewer.  Driven by the controls_define / controls_clear WebSocket
// messages defined in Phase 1.

// ── Module state ─────────────────────────────────────────────
let _ws = null;
let _rootEl = null;            // #tanga-control-root (fixed container for all panels)
let _panelEls = [];            // all active panel wrapper elements
let _toggleBtn = null;         // hide/restore toggle button
let _panelsHidden = false;
let _groupToggleCallbacks = {};// group_id → boolean (has on_toggle server handler)

// Throttle helpers (sliders send at ≤25 Hz while dragging; final state always flushed via change event)
const _throttleTimers = {};
const _throttleLast = {};
const _pendingThrottle = {};
const THROTTLE_MS = 40;

// ── Public API (called from viewer.js) ──────────────────────

/**
 * Store the WebSocket instance so the panel can send events back to Python.
 * Called from viewer.js after the WebSocket connects.
 */
export function setWebSocket(ws) {
    _ws = ws;
}

/**
 * Process a controls_define message: tear down the old panel tree and
 * rebuild everything from the message payload.
 */
export function handleControlsDefine(msg) {
    _destroyAll();
    _ensureRoot();

    const controls = msg.controls || [];
    const groups = msg.groups || [];
    const orphanIds = new Set(msg.orphanControls || []);

    // Build a lookup controlDefById for rendering
    const ctrlById = {};
    for (const c of controls) {
        ctrlById[c.id] = c;
    }

    // Render each group (skip attached groups — controls-attached.js handles them)
    for (const g of groups) {
        if (g.parentId) continue;  // handled by controls-attached.js

        const groupCtrls = (g.controls || []).map(id => ctrlById[id]).filter(Boolean);
        const panel = _createGroupPanel(g, groupCtrls);
        if (panel) {
            _positionPanel(panel, g.position || 'bottom-right');
            document.body.appendChild(panel);
            _panelEls.push(panel);
        }
        // Track whether this group has a server-side on_toggle
        _groupToggleCallbacks[g.id] = false;  // Phase 4 wires this
    }

    // Render orphan controls in a default title-less panel
    if (orphanIds.size > 0) {
        const orphanCtrls = [...orphanIds].map(id => ctrlById[id]).filter(Boolean);
        if (orphanCtrls.length > 0) {
            const panel = _createOrphanPanel(orphanCtrls);
            if (panel) {
                _positionPanel(panel, 'bottom-right');
                document.body.appendChild(panel);
                _panelEls.push(panel);
            }
        }
    }

    _ensureToggleButton();
}

/**
 * Process a controls_clear message: remove all control DOM elements.
 */
export function handleControlsClear() {
    _destroyAll();
}

// ── Internal: lifecycle ─────────────────────────────────────

function _ensureRoot() {
    if (_rootEl) return;
    _rootEl = document.createElement('div');
    _rootEl.id = 'tanga-control-root';
    _rootEl.style.position = 'fixed';
    _rootEl.style.top = '0';
    _rootEl.style.left = '0';
    _rootEl.style.width = '0';
    _rootEl.style.height = '0';
    _rootEl.style.pointerEvents = 'none';
    _rootEl.style.zIndex = '100';
    document.body.appendChild(_rootEl);
}

function _destroyAll() {
    for (const el of _panelEls) {
        el.remove();
    }
    _panelEls = [];
    _groupToggleCallbacks = {};
    // Clear throttle timers
    for (const k of Object.keys(_throttleTimers)) {
        clearTimeout(_throttleTimers[k]);
        delete _throttleTimers[k];
    }
}

function _ensureToggleButton() {
    if (_toggleBtn) return;
    _toggleBtn = document.createElement('button');
    _toggleBtn.textContent = '\u2699'; // gear ⚙
    _toggleBtn.style.position = 'fixed';
    _toggleBtn.style.bottom = '10px';
    _toggleBtn.style.right = '10px';
    _toggleBtn.style.zIndex = '200';
    _toggleBtn.style.width = '32px';
    _toggleBtn.style.height = '32px';
    _toggleBtn.style.border = '1px solid rgba(255,255,255,0.15)';
    _toggleBtn.style.borderRadius = '4px';
    _toggleBtn.style.background = 'rgba(20,20,40,0.85)';
    _toggleBtn.style.color = '#ccc';
    _toggleBtn.style.fontSize = '18px';
    _toggleBtn.style.cursor = 'pointer';
    _toggleBtn.style.lineHeight = '1';
    _toggleBtn.style.display = 'flex';
    _toggleBtn.style.alignItems = 'center';
    _toggleBtn.style.justifyContent = 'center';
    _toggleBtn.style.padding = '0';
    _toggleBtn.title = 'Toggle control panels';
    _toggleBtn.addEventListener('click', () => {
        _panelsHidden = !_panelsHidden;
        for (const el of _panelEls) {
            el.style.display = _panelsHidden ? 'none' : '';
        }
        _toggleBtn.style.opacity = _panelsHidden ? '0.5' : '1';
    });
    document.body.appendChild(_toggleBtn);
}

// ── Internal: group panel ───────────────────────────────────

function _createGroupPanel(group, controls) {
    const panel = document.createElement('div');
    panel.className = 'tanga-control-panel tanga-group-panel';
    panel.setAttribute('data-group-id', group.id);

    // ── Header (drag handle + toggle) ──
    const header = document.createElement('div');
    header.className = 'tanga-group-header';

    const titleSpan = document.createElement('span');
    titleSpan.className = 'tanga-group-title';
    titleSpan.textContent = group.title || 'Controls';
    header.appendChild(titleSpan);

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'tanga-group-toggle';
    toggleBtn.textContent = '\u25BE'; // ▾
    toggleBtn.title = 'Collapse / Expand';
    header.appendChild(toggleBtn);

    panel.appendChild(header);

    // ── Controls container ──
    const ctrlContainer = document.createElement('div');
    ctrlContainer.className = 'tanga-group-controls';

    for (const ctrl of controls) {
        const el = _createControlElement(ctrl);
        if (el) ctrlContainer.appendChild(el);
    }
    panel.appendChild(ctrlContainer);

    // ── Collapse toggle ──
    let collapsed = !!group.collapsed;
    function _applyCollapsed() {
        if (collapsed) {
            ctrlContainer.style.display = 'none';
            toggleBtn.textContent = '\u25B4'; // ▴
        } else {
            ctrlContainer.style.display = '';
            toggleBtn.textContent = '\u25BE'; // ▾
        }
    }
    _applyCollapsed();

    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        collapsed = !collapsed;
        _applyCollapsed();
        if (_groupToggleCallbacks[group.id]) {
            sendControlEvent('control:group_toggle', group.id, collapsed);
        }
    });

    // ── Drag setup (header is the drag handle) ──
    _setupDrag(panel, header);

    // ── Prevent pointer events on the panel from reaching Three.js ──
    panel.addEventListener('pointerdown', (e) => e.stopPropagation());
    panel.addEventListener('pointermove', (e) => e.stopPropagation());

    return panel;
}

// ── Internal: orphan panel ──────────────────────────────────

function _createOrphanPanel(controls) {
    if (controls.length === 0) return null;

    const panel = document.createElement('div');
    panel.className = 'tanga-control-panel tanga-orphan-panel';

    // Simple drag handle bar
    const handle = document.createElement('div');
    handle.className = 'tanga-orphan-handle';
    handle.style.height = '8px';
    panel.appendChild(handle);

    for (const ctrl of controls) {
        const el = _createControlElement(ctrl);
        if (el) panel.appendChild(el);
    }

    _setupDrag(panel, handle);
    panel.addEventListener('pointerdown', (e) => e.stopPropagation());
    panel.addEventListener('pointermove', (e) => e.stopPropagation());

    return panel;
}

// ── Internal: drag-to-move ──────────────────────────────────

function _setupDrag(panelEl, handleEl) {
    let dragging = false;
    let startX, startY, startLeft, startTop;

    handleEl.style.cursor = 'grab';

    handleEl.addEventListener('mousedown', (e) => {
        dragging = true;
        startX = e.clientX;
        startY = e.clientY;
        const rect = panelEl.getBoundingClientRect();
        startLeft = rect.left;
        startTop = rect.top;
        panelEl.classList.add('dragging');
        handleEl.style.cursor = 'grabbing';
        e.preventDefault();
    });

    const onMove = (e) => {
        if (!dragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        panelEl.style.left = (startLeft + dx) + 'px';
        panelEl.style.top = (startTop + dy) + 'px';
        // Clear anchor-based positioning once dragged
        panelEl.style.right = '';
        panelEl.style.bottom = '';
    };

    const onUp = () => {
        dragging = false;
        panelEl.classList.remove('dragging');
        handleEl.style.cursor = 'grab';
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', function cleanup() {
        onUp();
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', cleanup);
    }, { once: true });
}

// ── Internal: position panel ────────────────────────────────

function _positionPanel(panel, anchor) {
    panel.style.position = 'fixed';
    switch (anchor) {
        case 'top-left':
            panel.style.top = '60px';
            panel.style.left = '10px';
            break;
        case 'top-right':
            panel.style.top = '60px';
            panel.style.right = '10px';
            break;
        case 'bottom-left':
            panel.style.bottom = '50px';
            panel.style.left = '10px';
            break;
        case 'bottom-right':
        default:
            panel.style.bottom = '50px';
            panel.style.right = '10px';
            break;
    }
}

// ── Internal: control element dispatch ──────────────────────

function _createControlElement(ctrl) {
    switch (ctrl.kind) {
        case 'slider':
            return createSlider(ctrl);
        case 'dropdown':
            return createDropdown(ctrl);
        case 'button':
            return createButton(ctrl);
        default:
            console.warn('Unknown control kind:', ctrl.kind);
            return null;
    }
}

// ── Exported control factories (reused by controls-attached.js) ─

export function createSlider(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-slider';

    const labelRow = document.createElement('div');
    labelRow.className = 'tanga-control-label-row';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;

    const valueSpan = document.createElement('span');
    valueSpan.className = 'tanga-value';
    const defaultVal = ctrl.default !== undefined ? ctrl.default : ctrl.min;
    valueSpan.textContent = String(defaultVal);

    labelRow.appendChild(label);
    labelRow.appendChild(valueSpan);
    wrapper.appendChild(labelRow);

    const input = document.createElement('input');
    input.type = 'range';
    input.min = ctrl.min !== undefined ? ctrl.min : 0;
    input.max = ctrl.max !== undefined ? ctrl.max : 1;
    input.step = ctrl.step !== undefined ? ctrl.step : 0.01;
    input.value = defaultVal;
    input.className = 'tanga-range-input';
    wrapper.appendChild(input);

    // Immediate visual update
    input.addEventListener('input', () => {
        valueSpan.textContent = input.value;
    });

    // Throttled WebSocket send while dragging (~25 Hz max)
    input.addEventListener('input', () => {
        throttledSend('control:change', ctrl.id, parseFloat(input.value));
    });

    // Flush final value when the user releases the slider (change event)
    input.addEventListener('change', () => {
        throttledFlush('control:change', ctrl.id);
    });

    // Stop propagation to prevent orbit control interference
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());

    return wrapper;
}

export function createDropdown(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-dropdown';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const select = document.createElement('select');
    select.className = 'tanga-select-input';
    const options = ctrl.options || [];
    for (const opt of options) {
        const option = document.createElement('option');
        option.value = opt;
        option.textContent = opt;
        if (opt === ctrl.default) option.selected = true;
        select.appendChild(option);
    }
    wrapper.appendChild(select);

    select.addEventListener('change', () => {
        sendControlEvent('control:change', ctrl.id, select.value);
    });

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());

    return wrapper;
}

export function createButton(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-button';

    const btn = document.createElement('button');
    btn.textContent = ctrl.label || ctrl.id;
    btn.className = 'tanga-action-button';
    wrapper.appendChild(btn);

    btn.addEventListener('click', () => {
        sendControlEvent('control:click', ctrl.id, null);
    });

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());

    return wrapper;
}

// ── WebSocket event dispatch ────────────────────────────────

export function sendControlEvent(type, controlId, value) {
    if (!_ws || _ws.readyState !== WebSocket.OPEN) return;
    const msg = { type, control_id: controlId };
    if (value !== null && value !== undefined) {
        msg.value = value;
    }
    _ws.send(JSON.stringify(msg));
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

// ── CSS Injection (self-contained, dark theme) ──────────────

function _injectStyles() {
    if (document.getElementById('tanga-control-styles')) return;
    const style = document.createElement('style');
    style.id = 'tanga-control-styles';
    style.textContent = `
        .tanga-control-panel {
            position: absolute;
            z-index: 20;
            background: rgba(20, 20, 40, 0.92);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            padding: 8px 12px;
            min-width: 220px;
            max-width: 320px;
            font-family: sans-serif;
            font-size: 13px;
            color: #ccc;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
            user-select: none;
            pointer-events: auto;
        }
        .tanga-control-panel.dragging {
            cursor: grabbing;
            opacity: 0.95;
        }

        .tanga-group-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 6px;
            margin-bottom: 6px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            cursor: grab;
        }
        .tanga-group-header:active {
            cursor: grabbing;
        }
        .tanga-group-title {
            font-weight: 600;
            font-size: 14px;
            color: #ddd;
        }
        .tanga-group-toggle {
            background: none;
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 3px;
            color: #aaa;
            cursor: pointer;
            font-size: 14px;
            width: 22px;
            height: 22px;
            line-height: 1;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .tanga-group-toggle:hover {
            background: rgba(255,255,255,0.1);
            color: #fff;
        }

        .tanga-orphan-handle {
            cursor: grab;
        }
        .tanga-orphan-handle:active {
            cursor: grabbing;
        }

        .tanga-control {
            margin: 6px 0;
        }
        .tanga-control label {
            display: block;
            font-size: 12px;
            color: #aaa;
            margin-bottom: 2px;
        }
        .tanga-control-label-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .tanga-control-label-row label {
            margin-bottom: 0;
        }
        .tanga-value {
            font-size: 12px;
            color: #88aaff;
            font-weight: 600;
            min-width: 36px;
            text-align: right;
        }

        .tanga-range-input {
            width: 100%;
            height: 4px;
            -webkit-appearance: none;
            appearance: none;
            background: rgba(255,255,255,0.15);
            border-radius: 2px;
            outline: none;
            margin: 4px 0;
        }
        .tanga-range-input::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #4488ff;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.3);
        }
        .tanga-range-input::-moz-range-thumb {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #4488ff;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.3);
        }

        .tanga-select-input {
            width: 100%;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 4px;
            color: #ccc;
            padding: 4px 6px;
            font-size: 13px;
            outline: none;
            cursor: pointer;
        }
        .tanga-select-input:focus {
            border-color: #4488ff;
        }
        .tanga-select-input option {
            background: #1a1a2e;
            color: #ccc;
        }

        .tanga-action-button {
            width: 100%;
            padding: 5px 12px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 4px;
            color: #ddd;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.15s;
        }
        .tanga-action-button:hover {
            background: rgba(255,255,255,0.18);
        }
        .tanga-action-button:active {
            background: rgba(255,255,255,0.08);
        }
    `;
    document.head.appendChild(style);
}

// ── Initialize on import ────────────────────────────────────
_injectStyles();