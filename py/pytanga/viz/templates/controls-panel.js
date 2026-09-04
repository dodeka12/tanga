// Tanga 3D Viewer — Control Panel
// DOM control factories (sliders, dropdowns, buttons, …) shared by the
// layout/``view_layout`` rendering path (views/*.js) and by banners/dialogs.

import { openFileBrowser } from './file-browser.js';
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
 * Drop a control's registry entry (e.g. when a transient overlay such as a
 * dialog is unmounted) so later `control_update` messages for that id no-op.
 */
export function forgetControl(id) {
    delete _controlRegistry[id];
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
    input.className = 'tanga-text-input';
    Object.assign(input.style, { flex: '1', minWidth: '0' });

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
    if (ctrl.variant === 'menu') wrapper.classList.add('tanga-menu-item');
    if (ctrl.variant === 'toolbar') wrapper.classList.add('tanga-toolbar-item');

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
    if (ctrl.variant === 'toolbar') wrapper.classList.add('tanga-toolbar-item');

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
    if (ctrl.variant === 'menu') wrapper.classList.add('tanga-menu-item');

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

export function createLabel(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-label';

    const text = document.createElement('div');
    text.className = 'tanga-label-text';
    text.textContent = ctrl.value != null ? String(ctrl.value) : '';
    if (ctrl.font_size != null) text.style.fontSize = `${ctrl.font_size}px`;
    wrapper.appendChild(text);

    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'label',
        apply: (value) => { text.textContent = value == null ? '' : String(value); },
    };
    _applyTooltip(wrapper, ctrl);

    return wrapper;
}

function _renderMarkdown(el, text) {
    const src = text == null ? '' : String(text);
    // No `breaks: true` here: it turns the newlines inside a multi-line
    // `$$…$$` display-math block into `<br>`, which splits the two `$$`
    // delimiters into separate text nodes and KaTeX's auto-render can no
    // longer match them (leaving the math as literal source).
    if (typeof marked !== 'undefined') {
        el.innerHTML = marked.parse(src);
    } else {
        el.textContent = src;
    }
    if (typeof renderMathInElement !== 'undefined') {
        try {
            renderMathInElement(el, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        } catch (e) {
            console.warn('KaTeX markdown rendering error:', e);
        }
    }
}

export function createMarkdown(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-markdown';

    const body = document.createElement('div');
    body.className = 'tanga-markdown-body';
    _renderMarkdown(body, ctrl.value);
    wrapper.appendChild(body);

    _controlRegistry[ctrl.id] = {
        owner: ctrl.owner || 'panel',
        kind: 'markdown',
        apply: (value) => _renderMarkdown(body, value),
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
    if (ctrl.variant === 'menu') wrapper.classList.add('tanga-menu-item');

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
            // Double-click (not single click/focus) to edit a cell.  Range
            // selection (below) reacts to single click + drag, so a single
            // click must not also open the editor — otherwise the range's
            // focus transfer immediately blurs and closes it.
            editTriggerEvent: 'dblclick',
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
        // A ResizeObserver fires once immediately on `observe()`, so start it
        // only after `tableBuilt` — calling `redraw` before Tabulator built its
        // holder element throws and mis-measures the container width.
        table.on('tableBuilt', () => {
            new ResizeObserver(() => { table.redraw(true); }).observe(container);
        });
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

    // Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y undo & redo, round-tripped through the
    // backend so Python stays authoritative.  Skipped while focus is inside the
    // Tabulator cell editor so native text undo still works mid-edit.
    wrapper.addEventListener('keydown', (e) => {
        const target = e.target;
        if (target && target.closest && target.closest('.tabulator-editor')) {
            return;
        }
        const action = resolveUndoRedoAction(e);
        if (!action) return;
        e.preventDefault();
        sendControlEvent(
            action === 'undo' ? 'control:undo' : 'control:redo',
            ctrl.id,
            null
        );
    });

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
    'control:undo': 'undo',
    'control:redo': 'redo',
    'control:group_toggle': 'group_toggle',
};

/**
 * Map a keyboard-event shape to the undo/redo action it requests, or ``null``.
 *
 * Pure helper (no DOM/Tabulator) so the key mapping is unit-testable:
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
