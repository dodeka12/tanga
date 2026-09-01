// Tanga 3D Viewer — Control Panel
// DOM-based interactive controls (sliders, dropdowns, buttons) overlaid on the
// Three.js viewer.  Driven by the controls_define / controls_clear WebSocket
// messages defined in Phase 1.

import { openFileBrowser } from './file-browser.js';
import { sendEvent } from './events.js';

// ── Module state ─────────────────────────────────────────────
let _rootEl = null;            // #tanga-control-root (fixed container for all panels)
let _panelEls = [];            // all active panel wrapper elements
let _toggleBtn = null;         // hide/restore toggle button
let _panelsHidden = false;
let _groupToggleCallbacks = {};// group_id → boolean (has on_toggle server handler)
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
 * Process a controls_define message: tear down the old panel tree and
 * rebuild everything from the message payload.
 */
export function handleControlsDefine(msg, targetEl = null) {
    _destroyAll();
    if (!targetEl) _ensureRoot();

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
            _mountPanel(panel, g.position || 'bottom-right', targetEl);
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
                _mountPanel(panel, 'bottom-right', targetEl);
                _panelEls.push(panel);
            }
        }
    }

    if (!targetEl) _ensureToggleButton();
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

function _destroyAll({ owner = 'panel', scene = null } = {}) {
    for (const el of _panelEls) {
        el.remove();
    }
    _panelEls = [];
    _groupToggleCallbacks = {};
    // Clear only entries owned by the scope being rebuilt (default: panel),
    // leaving layout/banner view controls intact.
    for (const [id, entry] of Object.entries(_controlRegistry)) {
        if (entry.owner === owner && (scene === null || entry.scene === scene)) {
            delete _controlRegistry[id];
        }
    }
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
    if (group.tooltip) header.title = group.tooltip;

    const titleWrap = document.createElement('span');
    titleWrap.className = 'tanga-group-title-wrap';

    if (group.icon) {
        const icon = createIconElement(group.icon);
        icon.classList.add('tanga-group-icon');
        titleWrap.appendChild(icon);
    }

    const titleSpan = document.createElement('span');
    titleSpan.className = 'tanga-group-title';
    titleSpan.textContent = group.title || 'Controls';
    titleWrap.appendChild(titleSpan);

    header.appendChild(titleWrap);

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

function _mountPanel(panel, anchor, targetEl) {
    if (targetEl) {
        // Inside a pane: stack panels normally (no fixed positioning).
        panel.style.position = 'relative';
        panel.style.margin = '4px 0';
        targetEl.appendChild(panel);
    } else {
        _positionPanel(panel, anchor);
        document.body.appendChild(panel);
    }
}

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

// ── Icon rendering ──────────────────────────────────────────

const _iconFontLinks = {
    material: 'https://fonts.googleapis.com/icon?family=Material+Icons',
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
        span.className = 'material-icons';
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

function _attachDebouncedChange(input, controlId) {
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

// ── Internal: control element dispatch ──────────────────────

function _createControlElement(ctrl) {
    switch (ctrl.kind) {
        case 'slider':
            return createSlider(ctrl);
        case 'dropdown':
            return createDropdown(ctrl);
        case 'button':
            return createButton(ctrl);
        case 'file_chooser':
            return createFileChooser(ctrl);
        case 'text':
            return createTextField(ctrl);
        case 'textarea':
            return createTextArea(ctrl);
        case 'color':
            return createColorPicker(ctrl);
        case 'checkbox':
            return createCheckbox(ctrl);
        case 'value_edit':
            return createValueEdit(ctrl);
        case 'table':
            return createTable(ctrl);
        default:
            console.warn('Unknown control kind:', ctrl.kind);
            return null;
    }
}

// ── File chooser ─────────────────────────────────────────────

export function createFileChooser(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-file-chooser';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const row = document.createElement('div');
    Object.assign(row.style, { display: 'flex', gap: '6px', alignItems: 'center' });

    const input = document.createElement('input');
    input.type = 'text';
    input.value = ctrl.value || '';
    input.placeholder = ctrl.placeholder || 'Path…';
    Object.assign(input.style, {
        flex: '1', minWidth: '0', padding: '4px 6px',
        background: 'rgba(255,255,255,0.08)',
        border: '1px solid rgba(255,255,255,0.15)',
        borderRadius: '4px', color: '#ccc', fontSize: '13px',
        outline: 'none',
    });

    let debounceTimer = null;
    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            sendControlEvent('control:change', ctrl.id, input.value);
        }, 400);
    });
    input.addEventListener('change', () => {
        clearTimeout(debounceTimer);
        sendControlEvent('control:change', ctrl.id, input.value);
    });

    const browse = document.createElement('button');
    browse.textContent = 'Browse…';
    browse.className = 'tanga-action-button';
    Object.assign(browse.style, {
        width: 'auto', padding: '4px 12px', whiteSpace: 'nowrap', cursor: 'pointer',
    });
    browse.addEventListener('click', () => {
        openFileBrowser(ctrl.id, input.value || ctrl.root || '');
    });

    row.appendChild(input);
    row.appendChild(browse);
    wrapper.appendChild(row);
    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'file_chooser',
        apply: (value) => { input.value = value == null ? '' : String(value); },
    };
    _applyTooltip(wrapper, ctrl);
    return wrapper;
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
    const ctrlValue = ctrl.value !== undefined ? ctrl.value : ctrl.min;
    valueSpan.textContent = String(ctrlValue);

    labelRow.appendChild(label);
    labelRow.appendChild(valueSpan);
    wrapper.appendChild(labelRow);

    const input = document.createElement('input');
    input.type = 'range';
    input.min = ctrl.min !== undefined ? ctrl.min : 0;
    input.max = ctrl.max !== undefined ? ctrl.max : 1;
    input.step = ctrl.step !== undefined ? ctrl.step : 0.01;
    input.value = ctrlValue;
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

    // Flush final value when the user releases the slider (change event), and
    // send a distinct release notification for drag-end handling.
    input.addEventListener('change', () => {
        throttledFlush('control:change', ctrl.id);
        sendControlEvent('control:release', ctrl.id, parseFloat(input.value));
    });

    // Notify the backend when the user presses the slider (start of drag).
    input.addEventListener('pointerdown', () => {
        sendControlEvent('control:press', ctrl.id, parseFloat(input.value));
    });

    // Stop propagation to prevent orbit control interference
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'slider',
        apply: (value) => {
            const coerced = Number(value);
            input.value = coerced;
            valueSpan.textContent = String(coerced);
        },
    };
    _applyTooltip(wrapper, ctrl);

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
        if (opt === ctrl.value) option.selected = true;
        select.appendChild(option);
    }
    wrapper.appendChild(select);

    select.addEventListener('change', () => {
        sendControlEvent('control:change', ctrl.id, select.value);
    });

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'dropdown',
        apply: (value) => { select.value = value == null ? '' : String(value); },
    };
    _applyTooltip(wrapper, ctrl);

    return wrapper;
}

export function createButton(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-button';

    const btn = document.createElement('button');
    btn.className = 'tanga-action-button';

    if (ctrl.icon) {
        btn.appendChild(createIconElement(ctrl.icon));
        if (!ctrl.icon_only && (ctrl.label || ctrl.id)) {
            btn.appendChild(document.createTextNode(' ' + (ctrl.label || ctrl.id)));
        }
    } else {
        btn.textContent = ctrl.label || ctrl.id;
    }

    if (ctrl.icon_only) {
        btn.classList.add('tanga-icon-button');
        btn.title = ctrl.tooltip || ctrl.label || ctrl.id || '';
    }

    wrapper.appendChild(btn);

    btn.addEventListener('click', () => {
        sendControlEvent('control:click', ctrl.id, null);
    });

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    _applyTooltip(wrapper, ctrl);

    return wrapper;
}

export function createTextField(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-text-field';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const input = document.createElement('input');
    input.type = 'text';
    input.value = ctrl.value || '';
    input.placeholder = ctrl.placeholder || '';
    input.className = 'tanga-text-input';
    wrapper.appendChild(input);

    _attachDebouncedChange(input, ctrl.id);
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'text',
        apply: (value) => { input.value = value == null ? '' : String(value); },
    };
    _applyTooltip(wrapper, ctrl);

    return wrapper;
}

export function createTextArea(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-text-area';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const input = document.createElement('textarea');
    input.value = ctrl.value || '';
    input.placeholder = ctrl.placeholder || '';
    input.rows = ctrl.rows !== undefined ? ctrl.rows : 4;
    input.className = 'tanga-text-input tanga-textarea';
    wrapper.appendChild(input);

    _attachDebouncedChange(input, ctrl.id);
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'textarea',
        apply: (value) => { input.value = value == null ? '' : String(value); },
    };
    _applyTooltip(wrapper, ctrl);

    return wrapper;
}

export function createColorPicker(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-color-picker';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const input = document.createElement('input');
    input.type = 'color';
    input.value = ctrl.value || '#ffffff';
    input.className = 'tanga-color-input';
    wrapper.appendChild(input);

    _attachDebouncedChange(input, ctrl.id);
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'color',
        apply: (value) => { input.value = value == null ? '#ffffff' : String(value); },
    };
    _applyTooltip(wrapper, ctrl);

    return wrapper;
}

export function createCheckbox(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-checkbox';

    const row = document.createElement('label');
    row.className = 'tanga-checkbox-row';

    const input = document.createElement('input');
    input.type = 'checkbox';
    input.checked = !!ctrl.value;
    input.className = 'tanga-checkbox-input';

    const text = document.createElement('span');
    text.className = 'tanga-checkbox-label';
    text.textContent = ctrl.label || ctrl.id;

    row.appendChild(input);
    row.appendChild(text);
    wrapper.appendChild(row);

    input.addEventListener('change', () => {
        sendControlEvent('control:change', ctrl.id, input.checked);
    });

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'checkbox',
        apply: (value) => { input.checked = !!value; },
    };
    _applyTooltip(wrapper, ctrl);

    return wrapper;
}

export function createValueEdit(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-value-edit';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const min = ctrl.min !== undefined ? ctrl.min : 0;
    const max = ctrl.max !== undefined ? ctrl.max : 1;
    const step = ctrl.step !== undefined ? ctrl.step : 0.1;
    const digits = ctrl.digits !== undefined ? ctrl.digits : 2;
    const editable = ctrl.editable !== false;

    const clamp = (v) => Math.min(max, Math.max(min, v));
    const round = (v) => Number(v.toFixed(digits));

    let value = round(clamp(ctrl.value !== undefined ? ctrl.value : min));

    const input = document.createElement('input');
    input.type = 'text';
    input.inputMode = 'decimal';
    input.readOnly = !editable;
    input.className = 'tanga-value-input';
    input.value = value.toFixed(digits);

    const row = document.createElement('div');
    row.className = 'tanga-value-edit-row';

    const upBtn = document.createElement('button');
    upBtn.type = 'button';
    upBtn.className = 'tanga-step-button';
    upBtn.title = 'Increase';
    upBtn.appendChild(createIconElement('uc:▲'));

    const downBtn = document.createElement('button');
    downBtn.type = 'button';
    downBtn.className = 'tanga-step-button';
    downBtn.title = 'Decrease';
    downBtn.appendChild(createIconElement('uc:▼'));

    row.appendChild(input);
    row.appendChild(upBtn);
    row.appendChild(downBtn);
    wrapper.appendChild(row);

    const commit = () => {
        input.value = value.toFixed(digits);
        sendControlEvent('control:change', ctrl.id, value);
    };

    const stepValue = (direction) => {
        value = round(clamp(value + direction * step));
        commit();
    };

    const commitText = () => {
        const parsed = parseFloat(input.value);
        if (Number.isFinite(parsed)) {
            value = round(clamp(parsed));
            input.value = value.toFixed(digits);
            sendControlEvent('control:change', ctrl.id, value);
        } else {
            input.value = value.toFixed(digits);
        }
    };

    upBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        stepValue(1);
    });
    downBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        stepValue(-1);
    });

    // Arrow keys step the value while the control is hovered/focused.
    input.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowUp' || e.key === 'ArrowRight') {
            e.preventDefault();
            stepValue(1);
        } else if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') {
            e.preventDefault();
            stepValue(-1);
        } else if (e.key === 'Enter' && editable) {
            e.preventDefault();
            commitText();
        }
    });

    // When editable, parse a typed value on blur/Enter (clamped + rounded).
    if (editable) {
        input.addEventListener('change', commitText);
    }

    // Focus the input on hover so arrow keys work without an explicit click.
    wrapper.addEventListener('mouseenter', () => {
        input.focus({ preventScroll: true });
    });

    // Scroll wheel steps the value (up = increase).
    wrapper.addEventListener(
        'wheel',
        (e) => {
            e.preventDefault();
            stepValue(e.deltaY < 0 ? 1 : -1);
        },
        { passive: false }
    );

    // Stop propagation to prevent orbit control interference.
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());

    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'value_edit',
        apply: (v) => {
            value = round(clamp(Number(v)));
            input.value = value.toFixed(digits);
        },
    };
    _applyTooltip(wrapper, ctrl);

    return wrapper;
}

export function createTable(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-table';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const container = document.createElement('div');
    container.className = 'tanga-table-container';
    wrapper.appendChild(container);

    const columns = ctrl.columns || [];
    const rows = ctrl.rows || [];
    const height = ctrl.height || '220px';
    const fieldOf = (i) => 'c' + i;
    const colOf = (field) => {
        const idx = parseInt(String(field).slice(1), 10);
        return Number.isFinite(idx) ? idx : 0;
    };

    const buildDefs = (cols) =>
        cols.map((title, i) => ({
            title: String(title),
            field: fieldOf(i),
            editor: 'input',
        }));
    const buildData = (cols, rowsData) =>
        (rowsData || []).map((r) => {
            const obj = {};
            cols.forEach((_, i) => {
                obj[fieldOf(i)] = r && r[i] !== undefined ? String(r[i]) : '';
            });
            return obj;
        });

    let table = null;

    if (typeof Tabulator === 'undefined') {
        const notice = document.createElement('div');
        notice.className = 'tanga-table-unavailable';
        notice.textContent = 'Tabulator unavailable — editable table disabled.';
        container.appendChild(notice);
    } else {
        table = new Tabulator(container, {
            height,
            layout: 'fitColumns',
            data: buildData(columns, rows),
            columns: buildDefs(columns),
            // Spreadsheet-style keyboard editing. Tab / Shift+Tab already move
            // between cells (Tabulator defaults `navNext` / `navPrev`);
            // `tabEndNewRow` appends a blank row when Tab moves past the last
            // cell; Enter is bound to `navDown` to move to the next row.
            tabEndNewRow: ctrl.allow_add_rows !== false,
            keybindings: {
                navDown: [40, 13],
            },
            // Drag to select a range of cells; "− Selected" deletes every row
            // that has at least one selected cell.
            selectableRange: ctrl.allow_delete_rows !== false,
            selectableRangeInitializeDefault: false,
            selectableRangeAutoFocus: false,
        });

        table.on('cellEdited', (cell) => {
            sendControlEvent('control:cell_change', ctrl.id, {
                row: cell.getRow().getPosition(),
                col: colOf(cell.getColumn().getField()),
                value: String(cell.getValue()),
            });
        });

        // Tabulator's virtual DOM needs a concrete height; re-layout when the
        // surrounding pane is resized (split drag / window resize / first size).
        new ResizeObserver(() => { table.redraw(true); }).observe(container);
    }

    const buttonRow = document.createElement('div');
    buttonRow.className = 'tanga-table-buttons';

    if (table && ctrl.allow_add_rows !== false) {
        const addRowBtn = document.createElement('button');
        addRowBtn.type = 'button';
        addRowBtn.className = 'tanga-action-button';
        addRowBtn.textContent = '+ Row';
        addRowBtn.addEventListener('click', () => {
            const blank = {};
            table.getColumns().forEach((c) => { blank[c.getField()] = ''; });
            const rowIndex = table.getRows().length;
            table.addRow(blank);
            sendControlEvent('control:row_add', ctrl.id, {
                row: rowIndex,
                values: table.getColumns().map(() => ''),
            });
        });
        buttonRow.appendChild(addRowBtn);
    }

    if (table && ctrl.allow_add_columns !== false) {
        const addColBtn = document.createElement('button');
        addColBtn.type = 'button';
        addColBtn.className = 'tanga-action-button';
        addColBtn.textContent = '+ Column';
        addColBtn.addEventListener('click', () => {
            const colIndex = table.getColumns().length;
            const field = fieldOf(colIndex);
            const header = 'C' + (colIndex + 1);
            table.addColumn({ title: header, field, editor: 'input' });
            sendControlEvent('control:column_add', ctrl.id, {
                col: colIndex,
                header,
                values: Array(table.getRows().length).fill(''),
            });
        });
        buttonRow.appendChild(addColBtn);
    }

    if (table && ctrl.allow_delete_rows !== false) {
        const delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.className = 'tanga-action-button';
        delBtn.textContent = '− Selected';
        delBtn.addEventListener('click', () => {
            const selected = new Set();
            table.getRanges().forEach((range) => {
                range.getRows().forEach((row) => selected.add(row));
            });
            if (!selected.size) return;
            const indexes = [...selected].map((row) => row.getIndex());
            selected.forEach((row) => row.delete());
            sendControlEvent('control:row_delete', ctrl.id, { rows: indexes });
        });
        buttonRow.appendChild(delBtn);
    }

    if (buttonRow.children.length > 0) {
        wrapper.appendChild(buttonRow);
    }

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());

    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'table',
        apply: (value) => {
            if (!table || !value) return;
            const cols = value.columns || [];
            const rowsData = value.rows || [];
            table.setColumns(buildDefs(cols));
            table.setData(buildData(cols, rowsData));
        },
    };
    _applyTooltip(wrapper, ctrl);

    return wrapper;
}

// ── WebSocket event dispatch ────────────────────────────────

const _CONTROL_EVENTS = {
    'control:change': 'change',
    'control:click': 'click',
    'control:press': 'press',
    'control:release': 'release',
    'control:cell_change': 'cell_change',
    'control:row_add': 'row_add',
    'control:column_add': 'column_add',
    'control:row_delete': 'row_delete',
    'control:group_toggle': 'group_toggle',
};

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
        .tanga-group-title-wrap {
            display: flex;
            align-items: center;
            gap: 6px;
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

        .material-icons {
            font-size: 16px;
            line-height: 1;
            vertical-align: middle;
        }
        .tanga-icon-uc {
            vertical-align: middle;
        }
        .tanga-icon-button {
            width: 28px;
            height: 28px;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .tanga-icon-button .material-icons {
            font-size: 18px;
        }
        .tanga-text-input {
            width: 100%;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 4px;
            color: #ccc;
            padding: 4px 6px;
            font-size: 13px;
            outline: none;
        }
        .tanga-text-input:focus {
            border-color: #4488ff;
        }
        .tanga-textarea {
            resize: vertical;
            font-family: sans-serif;
        }
        .tanga-color-input {
            width: 100%;
            height: 28px;
            padding: 2px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 4px;
            cursor: pointer;
        }
        .tanga-checkbox-row {
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
        }
        .tanga-checkbox-input {
            cursor: pointer;
        }
        .tanga-checkbox-label {
            font-size: 12px;
            color: #ccc;
        }
        .tanga-value-edit-row {
            display: flex;
            gap: 4px;
            align-items: stretch;
        }
        .tanga-value-input {
            flex: 1;
            min-width: 0;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 4px;
            color: #ccc;
            padding: 4px 6px;
            font-size: 13px;
            outline: none;
            text-align: right;
        }
        .tanga-value-input:focus {
            border-color: #4488ff;
        }
        .tanga-step-button {
            width: 24px;
            padding: 0;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 4px;
            color: #ddd;
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .tanga-step-button:hover {
            background: rgba(255,255,255,0.18);
        }
        .tanga-step-button .tanga-icon-uc {
            font-size: 10px;
            line-height: 1;
        }
        .tanga-table-container {
            min-height: 220px;
        }
        .tanga-table-buttons {
            display: flex;
            gap: 6px;
            margin-top: 6px;
        }
        .tanga-table-buttons .tanga-action-button {
            width: auto;
            padding: 4px 12px;
            white-space: nowrap;
        }
        .tanga-table-unavailable {
            color: #c88;
            font-size: 12px;
            padding: 8px;
        }
        .tanga-control-view .tanga-table {
            height: 100%;
            margin: 0;
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }
        .tanga-control-view .tanga-table .tanga-table-container {
            flex: 1;
            min-height: 0;
        }
    `;
    document.head.appendChild(style);
}

// ── Initialize on import ────────────────────────────────────
_injectStyles();