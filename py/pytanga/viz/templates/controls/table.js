// Tanga Viewer — the native table DOM factory (column types, editors, zoom).

import { fitColumnWidths, fitContentColumnWidths, resizeColumnWidths, TABLE_MIN_COLUMN, cellCoordinates, moveCell, sortRows, clamp } from '../table-grid.js';
import { sendControlEvent, resolveUndoRedoAction, applyTooltip, registerControl, createIconElement } from '../controls-panel.js';

const TABLE_FIT_MAX = 240;
const TABLE_FIT_PADDING = 32;
const TABLE_FIT_BOOL = 28;

let _measureCtx = null;
function measureContext() {
    if (!_measureCtx) _measureCtx = document.createElement('canvas').getContext('2d');
    return _measureCtx;
}
function measureText(ctx, text) {
    return ctx.measureText(String(text)).width;
}

function normalizeColumnType(t) {
    if (t && typeof t === 'object' && t.kind) {
        return {
            kind: String(t.kind),
            values: Array.isArray(t.values) ? t.values.map(String) : [],
            format: typeof t.format === 'string' ? t.format : null,
        };
    }
    return { kind: 'string', values: [], format: null };
}

export function createTable(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-table';
    wrapper.tabIndex = 0;

    const titleBar = document.createElement('div');
    titleBar.className = 'tanga-table-title-bar';
    const title = document.createElement('span');
    title.className = 'tanga-table-title';
    title.textContent = ctrl.label || ctrl.id;
    titleBar.appendChild(title);
    const titleControls = document.createElement('div');
    titleControls.className = 'tanga-table-zoom';
    titleBar.appendChild(titleControls);
    wrapper.appendChild(titleBar);

    const container = document.createElement('div');
    container.className = 'tanga-table-container tanga-table-grid tanga-scroll';
    wrapper.appendChild(container);

    const table = document.createElement('table');
    table.className = 'tanga-table-element';
    container.appendChild(table);

    const colgroup = document.createElement('colgroup');
    table.appendChild(colgroup);
    const thead = document.createElement('thead');
    thead.className = 'tanga-table-head';
    table.appendChild(thead);
    const tbody = document.createElement('tbody');
    tbody.className = 'tanga-table-body';
    table.appendChild(tbody);

    const ROW_NUMBER_WIDTH = 40;
    let columns = (ctrl.columns || []).map(String);
    let rows = (ctrl.rows || []).map((r) => (r || []).map(String));
    let colWidths = null; // explicit column widths (px); filled on first render
    let columnWidths = ctrl.column_widths || null; // relative weights from the backend
    let columnTypes = (ctrl.column_types || []).map(normalizeColumnType);
    const showRowNumbers = ctrl.show_row_numbers === true;
    let editorCell = null;
    let activeTd = null;
    let sortState = ctrl.sort ? { colIndex: ctrl.sort.column, dir: ctrl.sort.order } : null;
    let rowHeight = ctrl.row_height || 24;
    let colScale = 1;

    const clearChildren = (el) => {
        while (el.firstChild) el.removeChild(el.firstChild);
    };

    const columnKind = (ci) => (columnTypes[ci] && columnTypes[ci].kind) || 'string';
    const enumValues = (ci) => {
        const t = columnTypes[ci];
        return (t && t.kind === 'enum' && Array.isArray(t.values)) ? t.values : [];
    };
    const alignFor = (kind) => (kind === 'number' ? 'right' : kind === 'bool' ? 'center' : 'left');
    const isNumeric = (text) => {
        const trimmed = String(text).trim();
        return trimmed !== '' && Number.isFinite(Number(trimmed));
    };

    const cellFont = () => {
        const cs = getComputedStyle(table);
        return cs.font || '12px sans-serif';
    };
    const relativeWidths = () => {
        const sum = colWidths.reduce((a, b) => a + b, 0) || 1;
        return colWidths.map((w) => w / sum);
    };
    const reportViewState = (changes) => {
        sendControlEvent('control:table_view_change', ctrl.id, changes);
    };
    const fitToContent = () => {
        const ctx = measureContext();
        ctx.font = cellFont();
        const measured = columns.map((header, c) => {
            const kind = columnKind(c);
            if (kind === 'bool') return TABLE_FIT_BOOL;
            let w = measureText(ctx, String(header));
            for (const row of rows) {
                const v = row[c];
                if (v !== undefined && v !== null && String(v) !== '') {
                    w = Math.max(w, measureText(ctx, String(v)));
                }
            }
            return w;
        });
        colWidths = fitContentColumnWidths(measured, {
            min: TABLE_MIN_COLUMN,
            max: TABLE_FIT_MAX,
            padding: TABLE_FIT_PADDING,
        });
        fit();
        reportViewState({ column_widths: relativeWidths() });
    };

    function renderColgroup() {
        clearChildren(colgroup);
        if (showRowNumbers) {
            const col = document.createElement('col');
            col.className = 'tanga-col-row-number';
            col.style.width = ROW_NUMBER_WIDTH + 'px';
            colgroup.appendChild(col);
        }
        for (let i = 0; i < columns.length; i += 1) {
            const col = document.createElement('col');
            col.className = 'tanga-col';
            colgroup.appendChild(col);
        }
    }

    function renderHeader() {
        clearChildren(thead);
        if (ctrl.show_column_titles === false) {
            thead.style.display = 'none';
            return;
        }
        thead.style.display = '';
        const tr = document.createElement('tr');
        if (showRowNumbers) {
            const th = document.createElement('th');
            th.className = 'tanga-row-number';
            th.textContent = '#';
            tr.appendChild(th);
        }
        columns.forEach((title, i) => {
            const th = document.createElement('th');
            th.className = 'tanga-table-head-cell';
            th.dataset.col = String(i);
            const titleSpan = document.createElement('span');
            titleSpan.className = 'tanga-table-title-text';
            titleSpan.textContent = String(title);
            th.appendChild(titleSpan);
            if (ctrl.sortable !== false) {
                th.classList.add('tanga-sortable');
                const sorted = sortState && sortState.colIndex === i;
                if (sorted && sortState.dir) {
                    th.classList.add(sortState.dir === 'asc' ? 'tanga-sort-asc' : 'tanga-sort-desc');
                }
                const arrow = document.createElement('span');
                arrow.className = 'tanga-sort-arrow';
                arrow.textContent = !sorted ? '↕' : (sortState.dir === 'asc' ? '▲' : '▼');
                arrow.addEventListener('click', (e) => {
                    e.stopPropagation();
                    toggleSort(i);
                });
                th.appendChild(arrow);
            }
            const handle = document.createElement('span');
            handle.className = 'tanga-col-resize';
            handle.addEventListener('pointerdown', (e) => startResize(e, i));
            th.appendChild(handle);
            if (ctrl.editable_titles !== false) {
                th.addEventListener('dblclick', (e) => {
                    if (e.target && e.target.closest && e.target.closest('.tanga-sort-arrow, .tanga-col-resize')) {
                        return;
                    }
                    startTitleEdit(th, i);
                });
            }
            th.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                e.stopPropagation();
                openTypeMenu(i, e.clientX, e.clientY);
            });
            tr.appendChild(th);
        });
        thead.appendChild(tr);
    }

    let editingTitle = null;

    function startTitleEdit(th, i) {
        if (editingTitle) return;
        editingTitle = th;
        const titleSpan = th.querySelector('.tanga-table-title-text');
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'tanga-table-title-editor';
        input.value = columns[i];
        titleSpan.textContent = '';
        titleSpan.appendChild(input);
        input.focus();
        input.select();
        let done = false;
        const finish = (commit) => {
            if (done) return;
            done = true;
            editingTitle = null;
            if (commit && input.value !== columns[i]) {
                columns[i] = input.value;
                sendControlEvent('control:column_title_change', ctrl.id, { col: i, title: input.value });
            }
            renderHeader();
            fit();
        };
        input.addEventListener('blur', () => finish(true));
        input.addEventListener('keydown', (e) => {
            e.stopPropagation();
            if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault();
                finish(true);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                finish(false);
            }
        });
    }

    let typeMenu = null;

    function closeTypeMenu() {
        if (typeMenu) {
            typeMenu.remove();
            typeMenu = null;
        }
    }

    function openTypeMenu(i, clientX, clientY) {
        closeTypeMenu();
        const current = columnTypes[i] ? columnTypes[i].kind : 'string';
        const options = ['number', 'string', 'bool', 'enum'].filter((t) => t !== current);
        const menu = document.createElement('div');
        menu.className = 'tanga-table-type-menu';
        menu.style.left = clientX + 'px';
        menu.style.top = clientY + 'px';
        options.forEach((t) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'tanga-table-type-menu-item';
            btn.textContent = t.charAt(0).toUpperCase() + t.slice(1);
            btn.addEventListener('click', () => {
                closeTypeMenu();
                sendControlEvent('control:column_type_change', ctrl.id, { col: i, type: t });
            });
            menu.appendChild(btn);
        });
        document.body.appendChild(menu);
        typeMenu = menu;
    }

    document.addEventListener('click', closeTypeMenu);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeTypeMenu();
    });
    document.addEventListener('contextmenu', (e) => {
        if (typeMenu && !(e.target && e.target.closest && e.target.closest('.tanga-table-type-menu'))) {
            closeTypeMenu();
        }
    });

    function displayOrder() {
        return sortState ? sortRows(rows, sortState.colIndex, sortState.dir) : rows.map((_, i) => i);
    }

    function toggleSort(colIndex) {
        if (ctrl.sortable === false) return;
        let dir;
        if (sortState && sortState.colIndex === colIndex && sortState.dir === 'asc') {
            dir = 'desc';
        } else if (sortState && sortState.colIndex === colIndex && sortState.dir === 'desc') {
            dir = null;
        } else {
            dir = 'asc';
        }
        sortState = dir ? { colIndex, dir } : null;
        reportViewState({ sort: sortState ? { column: sortState.colIndex, order: sortState.dir } : null });
        renderHeader();
        renderBody();
    }

    function renderBoolCheckbox(td, checked, onChange) {
        td.textContent = '';
        const box = document.createElement('input');
        box.type = 'checkbox';
        box.className = 'tanga-cell-checkbox';
        box.checked = checked;
        let pending = null;
        box.addEventListener('click', (e) => {
            e.stopPropagation();
            // Defer the model/event update so a double-click (which opens the
            // editor) doesn't send two toggle events and rebuild the grid under
            // the pointer. The checkbox's visual state still toggles immediately.
            if (pending) {
                clearTimeout(pending);
                pending = null;
                return;
            }
            pending = setTimeout(() => {
                pending = null;
                onChange(box.checked);
            }, 300);
        });
        td.appendChild(box);
    }

    function renderBody() {
        clearChildren(tbody);
        const order = displayOrder();
        order.forEach((originalIndex, displayPos) => {
            const row = rows[originalIndex];
            const tr = document.createElement('tr');
            tr.className = 'tanga-table-row';
            if (showRowNumbers) {
                const td = document.createElement('td');
                td.className = 'tanga-row-number';
                td.textContent = String(displayPos + 1);
                tr.appendChild(td);
            }
            columns.forEach((_, ci) => {
                const td = document.createElement('td');
                td.className = 'tanga-cell';
                td.dataset.col = String(ci);
                td.dataset.originalIndex = String(originalIndex);
                const kind = columnKind(ci);
                td.style.textAlign = alignFor(kind);
                if (kind === 'bool') {
                    renderBoolCheckbox(td, String(row[ci]) === 'true', (checked) => toggleBool(originalIndex, ci, checked));
                } else {
                    td.textContent = row[ci] !== undefined ? String(row[ci]) : '';
                }
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    function toggleBool(originalIndex, ci, checked) {
        const value = checked ? 'true' : 'false';
        rows[originalIndex][ci] = value;
        sendControlEvent('control:cell_change', ctrl.id, { row: originalIndex, col: ci, value });
        renderBody();
    }

    function contentAvail() {
        return container.clientWidth - (showRowNumbers ? ROW_NUMBER_WIDTH : 0);
    }

    function fit() {
        const cols = colgroup.children;
        let offset = 0;
        if (showRowNumbers) {
            if (cols[0]) cols[0].style.width = ROW_NUMBER_WIDTH + 'px';
            offset = 1;
        }
        let total = showRowNumbers ? ROW_NUMBER_WIDTH : 0;
        colWidths.forEach((w, i) => {
            const col = cols[offset + i];
            if (col) col.style.width = w + 'px';
            total += w;
        });
        table.style.minWidth = total + 'px';
        table.style.width = total + 'px';
    }

    // Refill the available width, scaling every column proportionally so their
    // relative widths (including manual resizes) are preserved.  Runs on
    // container resizes (window/splitter), not on zoom or per-column drags.
    function refit() {
        if (!colWidths || colWidths.length === 0) return;
        const target = Math.max(0, contentAvail()) * colScale;
        const sum = colWidths.reduce((a, b) => a + b, 0) || 1;
        const factor = target / sum;
        colWidths = colWidths.map((w) => Math.max(TABLE_MIN_COLUMN, w * factor));
        fit();
    }

    function zoomColumns(factor) {
        colScale = clamp(colScale * factor, 0.25, 8);
        colWidths = colWidths.map((w) => Math.max(TABLE_MIN_COLUMN, w * factor));
        fit();
    }

    function zoomRows(delta) {
        rowHeight = clamp(rowHeight + delta, 16, 60);
        table.style.setProperty('--tanga-table-row-height', rowHeight + 'px');
        reportViewState({ row_height: rowHeight });
    }

    function render() {
        table.style.setProperty('--tanga-table-row-height', rowHeight + 'px');
        renderColgroup();
        renderHeader();
        renderBody();
        if (!colWidths || colWidths.length !== columns.length) {
            const weights = columnWidths && columnWidths.length === columns.length
                ? columnWidths
                : columns.map(() => 1);
            colWidths = fitColumnWidths(Math.max(0, contentAvail()) * colScale, weights);
        }
        fit();
    }

    function startResize(e, colIndex) {
        e.preventDefault();
        e.stopPropagation();
        const startX = e.clientX;
        const startWidths = colWidths.slice();

        function onMove(ev) {
            const dx = ev.clientX - startX;
            // Resizing only changes the dragged column; its right neighbours
            // keep their widths and shift as the table's total width grows or
            // shrinks (the grid scrolls horizontally when it exceeds the
            // container width).
            colWidths = resizeColumnWidths(startWidths, colIndex, dx);
            fit();
        }
        function onUp() {
            document.removeEventListener('pointermove', onMove);
            document.removeEventListener('pointerup', onUp);
            reportViewState({ column_widths: relativeWidths() });
        }
        document.addEventListener('pointermove', onMove);
        document.addEventListener('pointerup', onUp);
    }

    function displayIndex(td) {
        return {
            row: Array.prototype.indexOf.call(tbody.children, td.parentElement),
            col: parseInt(td.dataset.col, 10),
        };
    }

    function cellAt(row, col) {
        const tr = tbody.children[row];
        if (!tr) return null;
        return tr.querySelector(`td.tanga-cell[data-col="${col}"]`) || null;
    }

    function setActive(td) {
        if (activeTd === td) {
            // Already active — re-focus it (e.g. re-clicking the same cell after
            // focus moved elsewhere) so the arrow keys keep working.
            if (td && td.focus) td.focus();
            return;
        }
        if (activeTd && activeTd.classList) activeTd.classList.remove('tanga-cell-active');
        activeTd = td || null;
        if (activeTd && activeTd.classList) {
            activeTd.classList.add('tanga-cell-active');
            // Make the active cell focusable and focus it, so the wrapper's
            // arrow-key handler receives keydown events without relying on the
            // (unreliable) wrapper-level focus.
            activeTd.tabIndex = -1;
            activeTd.focus();
        }
        // Report the selection to the backend (data indices, not the display
        // position) so row/column add & delete can target the active cell.
        const pos = activeTd ? cellCoordinates(activeTd) : null;
        sendControlEvent('control:cell_select', ctrl.id, pos ? { row: pos.row, col: pos.col } : null);
    }

    function appendRow() {
        const rowIndex = rows.length;
        const blank = columns.map(() => '');
        rows.push(blank);
        sendControlEvent('control:row_add', ctrl.id, { row: rowIndex, values: blank });
        renderBody();
        return rowIndex;
    }

    function moveEditor(fromTd, dCol, dRow) {
        const pos = displayIndex(fromTd);
        let row = pos.row + dRow;
        let col = pos.col + dCol;

        if (dCol === 1 && col >= columns.length) {
            col = 0;
            row += 1;
        } else if (dCol === -1 && col < 0) {
            col = columns.length - 1;
            row -= 1;
        }

        if (row < 0) return;
        if (row >= tbody.children.length) {
            if (ctrl.allow_add_rows !== false) {
                appendRow();
            } else {
                return;
            }
        }
        openEditor(cellAt(row, col));
    }

    function moveActive(key) {
        if (!activeTd) return;
        const pos = displayIndex(activeTd);
        const target = moveCell(pos.row, pos.col, key, tbody.children.length, columns.length);
        setActive(cellAt(target.row, target.col));
    }

    function openEditor(td) {
        if (!td || editorCell === td) return false;
        const { row: ri, col: ci } = cellCoordinates(td);
        const kind = columnKind(ci);
        const original = rows[ri] && rows[ri][ci] !== undefined ? rows[ri][ci] : '';

        let widget;
        if (kind === 'enum') {
            widget = document.createElement('select');
            widget.className = 'tanga-table-editor';
            const values = enumValues(ci);
            values.forEach((v) => {
                const opt = document.createElement('option');
                opt.value = String(v);
                opt.textContent = String(v);
                widget.appendChild(opt);
            });
            if (String(original) !== '' && !values.includes(String(original))) {
                const opt = document.createElement('option');
                opt.value = String(original);
                opt.textContent = String(original);
                widget.appendChild(opt);
            }
            widget.value = String(original);
        } else if (kind === 'bool') {
            widget = document.createElement('input');
            widget.type = 'checkbox';
            widget.className = 'tanga-table-editor tanga-cell-checkbox';
            widget.checked = String(original) === 'true';
            // The native space-toggle fires a click that bubbles to the body,
            // which would re-focus the cell and blur this editor (committing
            // early). Stop it so space toggles without closing the editor.
            widget.addEventListener('click', (e) => e.stopPropagation());
        } else {
            widget = document.createElement('input');
            widget.type = 'text';
            widget.className = 'tanga-table-editor';
            widget.value = String(original);
        }

        let done = false;
        const finish = (commit) => {
            if (done) return false;
            const raw = kind === 'bool' ? (widget.checked ? 'true' : 'false') : String(widget.value);
            const fmt = columnTypes[ci] && columnTypes[ci].format;
            // A formatted number column lets the backend parse the value (it may
            // be entered in the formatted form, e.g. "3.50m"), so skip the local
            // numeric check there; unformatted number columns keep it.
            const invalid = kind === 'number' && !fmt && !isNumeric(raw);
            const value = commit && !invalid ? raw : String(original);
            done = true;
            if (editorCell === td) editorCell = null;
            if (commit && !invalid) {
                rows[ri][ci] = value;
                sendControlEvent('control:cell_change', ctrl.id, { row: ri, col: ci, value });
            }
            if (kind === 'bool') {
                // Keep the checkbox widget (don't render the raw "true"/"false").
                renderBoolCheckbox(td, value === 'true', (checked) => toggleBool(ri, ci, checked));
            } else {
                td.textContent = value;
            }
            // Return focus to the active cell so the cursor keys keep working.
            if (activeTd && activeTd.focus) activeTd.focus();
            return commit && !invalid;
        };

        widget.addEventListener('blur', () => finish(true));
        widget.addEventListener('keydown', (e) => {
            e.stopPropagation();
            if (e.key === 'Enter') {
                e.preventDefault();
                if (finish(true)) moveEditor(td, 0, 1);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                finish(false);
            } else if (e.key === 'Tab') {
                e.preventDefault();
                if (finish(true)) moveEditor(td, e.shiftKey ? -1 : 1, 0);
            }
        });

        // Commit any other open editor before opening this one.
        if (editorCell) {
            const prev = editorCell;
            editorCell = null;
            const prevInput = prev.querySelector('.tanga-table-editor');
            if (prevInput) prevInput.blur();
        }

        setActive(td);
        editorCell = td;
        td.textContent = '';
        td.appendChild(widget);
        widget.focus();
        if (widget.tagName === 'INPUT' && widget.type === 'text') widget.select();
        return true;
    }

    render();

    tbody.addEventListener('dblclick', (e) => {
        const td = e.target && e.target.closest ? e.target.closest('td.tanga-cell') : null;
        if (td) openEditor(td);
    });

    tbody.addEventListener('click', (e) => {
        const td = e.target && e.target.closest ? e.target.closest('td.tanga-cell') : null;
        if (td) setActive(td);
    });

    let lastAvail = null;
    const resizeObserver = new ResizeObserver(() => {
        // Only refit when the available width actually changes; a horizontal
        // scrollbar appearing (e.g. after widening the last column) changes the
        // height, not the width, and must not trigger a reflow that reverts it.
        const avail = contentAvail();
        if (avail !== lastAvail) {
            lastAvail = avail;
            refit();
        }
    });
    resizeObserver.observe(container);

    // Title-bar zoom controls (column width + row height).
    function addIconButton(group, icon, titleText, onClick) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'tanga-action-button tanga-zoom-btn tanga-icon-button';
        btn.appendChild(createIconElement('material:' + icon));
        btn.title = titleText;
        btn.addEventListener('click', onClick);
        group.appendChild(btn);
    }
    addIconButton(titleControls, 'arrow_left', 'Narrower columns', () => zoomColumns(1 / 1.25));
    addIconButton(titleControls, 'arrow_right', 'Wider columns', () => zoomColumns(1.25));
    addIconButton(titleControls, 'arrow_drop_up', 'Shorter rows', () => zoomRows(-4));
    addIconButton(titleControls, 'arrow_drop_down', 'Taller rows', () => zoomRows(4));
    addIconButton(titleControls, 'fit_screen', 'Fit columns to content', fitToContent);

    // Bottom-right corner to resize the whole table.  Dragging reports a new
    // pixel size to the view (`onResize`), which sets its preferred size and
    // lets the enclosing flow container re-layout.  In a SplitView the splitter
    // owns the size, so the corner is inert there.
    if (ctrl.onResize) {
        const corner = document.createElement('div');
        corner.className = 'tanga-table-resize';
        corner.title = 'Resize';
        corner.addEventListener('pointerdown', (e) => {
            if (e.button !== 0) return;
            e.preventDefault();
            e.stopPropagation();
            const rect = wrapper.getBoundingClientRect();
            const startX = e.clientX;
            const startY = e.clientY;
            const startW = rect.width;
            const startH = rect.height;
            function onMove(ev) {
                const w = Math.max(200, startW + ev.clientX - startX);
                const h = Math.max(120, startH + ev.clientY - startY);
                ctrl.onResize(w, h);
            }
            function onUp() {
                document.removeEventListener('pointermove', onMove);
                document.removeEventListener('pointerup', onUp);
            }
            document.addEventListener('pointermove', onMove);
            document.addEventListener('pointerup', onUp);
        });
        wrapper.appendChild(corner);
    }

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());

    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'table',
        apply: (value) => {
            if (!value) return;
            columns = (value.columns || []).map(String);
            rows = (value.rows || []).map((r) => (r || []).map(String));
            columnTypes = (value.column_types || []).map(normalizeColumnType);
            columnWidths = value.column_widths || null;
            rowHeight = value.row_height || 24;
            sortState = value.sort ? { colIndex: value.sort.column, dir: value.sort.order } : null;
            editorCell = null;
            setActive(null);
            render();
        },
    });
    applyTooltip(wrapper, ctrl);

    // Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y undo & redo, round-tripped through the
    // backend so Python stays authoritative.  (Phase 4 adds the editor guard.)
    wrapper.addEventListener('keydown', (e) => {
        const target = e.target;
        if (target && target.closest && target.closest('input.tanga-table-editor, input.tanga-table-title-editor')) {
            return;
        }
        if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            if (activeTd) {
                e.preventDefault();
                moveActive(e.key);
            }
            return;
        }
        if (e.key === 'Enter' || e.key === 'Tab') {
            if (activeTd) {
                e.preventDefault();
                openEditor(activeTd);
            }
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
