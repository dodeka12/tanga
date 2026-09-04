# Phase 4 — `LogView` frontend

## Goal

Render the serialized `log_view` node in the browser: a scrollable two-column
(time | message) list with alternating shading, history-cap mirroring,
auto-scroll, and a runtime registry for later live updates (Phase 5).

## Files

- New: `py/pytanga/viz/templates/views/log-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- New: `py/pytanga/viz/templates/themes/views/log-view.css`
- Edit: `py/pytanga/viz/templates/themes/registry.json`
- Edit: `py/tests/viz/test_themes.py`
- New: `dev/src/js-tests/log-view.test.mjs`

## Steps

- [x] **4.1 — `log-view.js` (class + registry)**
  - `export class LogView extends View`, constructor
    `{ id = null, max_history = null, lines = [] }`; set `this.logId = id`;
    add `tanga-log-view` class and `overflow: auto` on `this.el`.
  - Module-level `const _logViews = new Map()` plus
    `export function registerLogView(id, view)`,
    `export function applyLogUpdate(msg)` (append/clear/replace dispatch),
    `export function forgetLogView(id)`.
  - `destroy()` calls `forgetLogView(this.logId)` then `super.destroy()`.

- [x] **4.2 — Rendering + history**
  - `_onMounted()` renders the initial `this.lines`.
  - `_appendRow(line)`: a `.tanga-log-row` with a `.tanga-log-time` cell
    (`line.time`) and a `.tanga-log-message` cell (`_messageOf(line)`).
  - `_messageOf(line)`: `line.message` if present, else
    `JSON.stringify` of the line minus `time`.
  - `appendLines(lines)` / `clearLines()` / `replaceLines(lines)`; append also
    enforces `max_history` by dropping the oldest DOM rows.

- [x] **4.3 — Auto-scroll**
  - Before appending, capture `atBottom = el.scrollTop + el.clientHeight >=
    el.scrollHeight - 4`; after appending, if `atBottom`, set
    `el.scrollTop = el.scrollHeight`.  A user-scrolled-up position is preserved.

- [x] **4.4 — `build.js` branch**
  - Import `LogView` and `registerLogView`; add a `node.type === 'log_view'`
    branch that constructs `new LogView({ id: node.id, max_history:
    node.max_history, lines: node.lines || [] })`, calls `applySizeSpecs`, then
    `registerLogView(view.logId, view)`.

- [x] **4.5 — Theme CSS**
  - New `themes/views/log-view.css`: `.tanga-log-view`, `.tanga-log-row`
    (grid two columns), `.tanga-log-time` (muted, mono), `.tanga-log-message`,
    and `.tanga-log-row:nth-child(even)` alternating background.
  - Add `"views/log-view.css"` to `registry.json` `components` and
    `test_themes.py::_COMPONENTS`.

- [x] **4.6 — JS test (`log-view.test.mjs`)**
  - Stub `ResizeObserver`/`document` (as in `group-chrome.test.mjs`); assert:
    initial render, `appendLines` adds rows, `clearLines` empties,
    `replaceLines` replaces, `max_history` truncation, `_messageOf` JSON
    fallback, and auto-scroll (set `scrollTop`/`scrollHeight`/`clientHeight`).
  - Assert `applyLogUpdate` routes append/clear/replace to the registered view
    and no-ops for unknown ids.

## Validation

```
node --check py/pytanga/viz/templates/views/log-view.js py/pytanga/viz/templates/views/build.js
node --test 'dev/src/js-tests/*.test.mjs'
uv run pytest py/tests/viz/test_themes.py -q
```

## Notes

- The fake-DOM `makeEl` stub has no scroll props; set them on `this.el` in the
  test before exercising auto-scroll.
- `nth-child(even)` shading is CSS-only (not asserted in the fake-DOM test).
