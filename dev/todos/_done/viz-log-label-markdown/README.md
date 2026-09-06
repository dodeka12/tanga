# Viz display views — LogView / LabelView / MarkdownView — Overview

**Created:** 2026-09-03 | **Status:** Done | **Branch:** `feat/view-architecture`

## Goal

Add three read-only **content views** that render in the same `view_layout`
tree as everything else:

- **`LabelView`** — a single line of text with a configurable font size.
- **`MarkdownView`** — a multi-line block of rendered markdown (with KaTeX math).
- **`LogView`** — a live, scrollable two-column (time | message) log that the
  backend appends to programmatically; alternating row shading, auto-scroll,
  history cap, dict folding, and JSON-lines file I/O.

`LabelView` and `MarkdownView` are **settable controls** (a `value` updated in
place via `set_control` / `set_control_value` / `update_control`, exactly like
the other controls).  `LogView` is a stateful view with its own append/clear
API and a lightweight `log_update` push.

## Architecture (short)

- **Backend model** — `_controls.py` gains two display-only `Control`
  dataclasses (`Label`, `Markdown`) and `views.py` gains their `ControlView`
  wrappers plus a plain `LogView`.  All three serialize through
  `serialize_layout` → `view_layout`.
- **Label/Markdown updates** — reuse the existing `control_update` path:
  `Visualizer.set_control_value` resolves the view (via `_resolve_control`) and
  pushes `control_update`; the frontend `_controlRegistry` `apply(value)`
  re-renders.  No new message type or `Visualizer` wiring is needed for these.
- **Markdown** — reuse the already-loaded optional `marked@12.0.2` +
  KaTeX (`renderMathInElement`), the same pattern as `banner-view.js` /
  `three-view.js`: `marked.parse(text, {breaks:true})` then KaTeX over `$…$` /
  `$$…$$`, with `textContent` fallback when `marked` is absent.
- **LogView updates** — a new `log_update` message + an id → view runtime
  registry (mirrors `control_update` / `_controlRegistry`), pushed via the
  generic `server.push_raw`.  `LogView` is **not** a control.

## Fixed contract (up front)

### 1. `LabelView` (a `ControlView`)

```python
LabelView("my_label", value="hello", font_size=20)   # font_size in px
# {"type": "label_view", "id": "my_label", "value": "hello", "font_size": 20, …}
viz.set_control("my_label", "new text")              # live via control_update
```

Backend `Control`: `Label(kind="label", value="", font_size=14)`.
`get_control_value` → `value`; `set_control_value` → `value = str(v)`.

### 2. `MarkdownView` (a `ControlView`)

```python
MarkdownView("my_md", value="# Title\n- item\n\n$E=mc^2$")
# {"type": "markdown_view", "id": "my_md", "value": "# Title…", …}
viz.set_control("my_md", "**bold** $x^2$")           # live re-render
```

Backend `Control`: `Markdown(kind="markdown", value="")`.

### 3. `LogView` (a plain `View`)

```python
LogView(id=None, *, max_history=None, **kwargs)        # id auto "logN"; None = unlimited
log_view.log(message)   # str → {"time": ts, "message": str}
                        # dict → {"time": ts, **dict}  (keys folded in)
log_view.get_log()      # -> list[dict] (copies)
log_view.write_file(p)  # JSON lines (one dict per line)
log_view.load_file(p)   # replace lines (truncated to max_history)
log_view.clear()
# {"type": "log_view", "id": "log0", "max_history": 1000,
#  "lines": [{"time": "…", "message": "…", …}], …size fields}
```

- `time` = `datetime.now(timezone.utc).isoformat()` (backend-captured at `log()`).
- Display column 2 = `line["message"]`, else JSON of the non-`time` keys
  (computed on the frontend for display only — the stored dict is unchanged).

### 4. `log_update` message

```json
{"type": "log_update", "id": "log0", "action": "append",  "lines": [<new lines>]}
{"type": "log_update", "id": "log0", "action": "clear"}
{"type": "log_update", "id": "log0", "action": "replace", "lines": [<all lines>]}
```

## Decisions (confirmed)

- `LabelView` / `MarkdownView` are **display-only controls**: they carry a
  `value` and receive `control_update`, but send no client events (no input
  element).  They are settable after creation via `set_control` /
  `set_control_value` / `update_control`.
- `Label` / `Markdown` control dataclasses live in `_controls.py` and are **not
  re-exported** from `pytanga.viz` (the `Label` name already belongs to the 3D
  `pytanga.viz.Label`); the public API is `LabelView` / `MarkdownView`.
- `font_size` is a `Label` control field (default `14` px, settable via
  `update_control`); `value` is the text.
- Markdown = `marked.parse` + `renderMathInElement` (KaTeX) with `$…$`/`$$…$$`
  delimiters; falls back to plain text without `marked`, and skips math without
  KaTeX.
- `LogView` is a plain `View` (not a control): its append/clear/replace
  semantics don't map to a single `value`, so it gets its own `log_update`
  path.  Timestamps are captured on the **backend**.
- `max_history` drops the oldest lines (FIFO); `None` = unlimited.  Enforced on
  append (backend) and on `load_file`; the frontend mirrors it on append.
- Auto-scroll: append scrolls to the bottom only if the container was already
  at (or near) the bottom; a user-scrolled-up position is preserved.
- Any of the three views can appear in **any scene/layout** (each scene's layout
  tree holds its own instances); update messages are addressed by
  **globally-unique id** — the same "single global id namespace" as every
  control (`scene` is a hint, not a routing key).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-label-view-control.md](./01-label-view-control.md) | `LabelView` display control (backend + frontend + theme + export + tests) |
| 2 | [02-markdown-view-control.md](./02-markdown-view-control.md) | `MarkdownView` display control (marked + KaTeX) |
| 3 | [03-log-view-model.md](./03-log-view-model.md) | `LogView` backend data model + serialization + file I/O + tests |
| 4 | [04-log-view-frontend.md](./04-log-view-frontend.md) | `LogView` frontend render/scroll/history + `build.js` + theme + tests |
| 5 | [05-log-view-live-updates.md](./05-log-view-live-updates.md) | `log_update` message + `Visualizer` push + `viewer.js` dispatch + tests |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Docs, examples, changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` (per-phase subsets below)
- **JS:** `node --check <files>` and `node --test 'dev/src/js-tests/*.test.mjs'`
- **Docs:** `uv run mkdocs build --strict` and
  `uv run python tools/generate-example-docs.py --check`

## Non-goals

- No user editing of `LabelView` / `MarkdownView` (display-only; no client
  events), and no `on_change` handlers on them.
- No KaTeX without `marked`, and no raw-HTML sanitization (consistent with the
  existing `banner`/annotation `marked.parse` behavior).
- No frontend-side timestamps or per-scene `log_update` routing (global by id).
- No rich/structured `LogView` rendering beyond text vs. JSON fallback (no
  per-level colors, filtering, or search).
- No `add_label` / `add_markdown` / `add_log` panel facades (views only; facades
  can be a follow-up).