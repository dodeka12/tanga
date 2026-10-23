# Phase 5 — Nested dataclasses → nested `GroupView`s

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (`GroupView`/`ParamsView`
> serialization) and `docs/dev/architecture/viz-theme-system.md` (group title
> token).  Nested groups reuse existing `GroupView` + `params_view` nodes; no new
> wire format.

## Goal

Render dataclass-valued fields as nested `GroupView`s with a smaller title font.

## Files

- **Edit** `py/pytanga/viz/_params_ui.py` — `GroupUI`.
- **Edit** `py/pytanga/viz/views/params_view.py` — detect dataclass fields, build
  nested `GroupView(ParamsView(...))`, add the nested class.
- **Edit** `py/pytanga/viz/templates/themes/views/group-view.css` (or base.css) —
  `.tanga-group-nested` title font.
- **Edit** `py/pytanga/viz/templates/themes/base.css` (+ `compact/tokens.css`) —
  `--tanga-group-nested-title-size`.
- **Edit** `py/tests/viz/test_params_view.py`.

## Steps

- [x] **5.1 — `GroupUI`**
  - Add `GroupUI(ControlUI)` with `kind = "group"` and `collapsed: bool = False`.
- [x] **5.2 — nested group building**
  - In `_build_children`, a field whose value is a dataclass instance (or whose
    `ui.kind == "group"`) becomes a nested `GroupView(title, children=[ParamsView(nested)])`
    (nested `id = f"{view.id}.{key}"`, `hide_label`-less rows); flatten it in
    `_serialize` as a `group` child node.
- [x] **5.3 — nested title font**
  - Tag nested groups `tanga-group-nested`; add `.tanga-group.tanga-group-nested
    .tanga-group-title { font-size: var(--tanga-group-nested-title-size) }` and the
    token (`--tanga-group-nested-title-size: var(--tanga-font-size-body)`).
- [x] **5.4 — tests**
  - Nested field serializes as a `group` node with a nested `params_view`; nested
    field handlers register (via `iter_control_views`); title override via `GroupUI`.

## Validation

```bash
uv run pytest py/tests/viz/test_params_view.py -q
```
