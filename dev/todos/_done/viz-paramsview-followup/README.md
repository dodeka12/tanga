# ParamsView follow-up (buttons, title-less rows, nested groups) — Overview

**Created:** 2026-10-21 | **Status:** Done | **Branch:** `feat/paramsview-follow-up`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (the `ControlUI`
> model, `control_state`/`ControlEvent`, the `ParamsView` composite recipe, the
> row-state wire pattern) and `docs/dev/architecture/viz-architecture.md`
> (`GroupView`/`ParamsView` serialization).  This work extends the existing
> `ParamsView`/`GroupView` (no new control kind, no new wire message); the
> `control_state {enabled}`/`{title}` routing to a group is an extension of the
> already-documented `control_state {visible}`/`{collapsed}` view routing.
> Update the developer docs in Phase 7.

## Goal

Close the remaining gaps that stop `ParamsView` from replacing hand-built
panels end-to-end: button captions + full-width/title-less rows, the shared
`on_change` reaching nested groups (with a dotted `event.key`), a dotted row
API plus `set_state` that rebinds nested groups, and nested `extra_rows`.

## Architecture (short)

- **Python model** — `ControlUI` gains `full_width`; `ButtonUI` gains `label`
  and defaults `full_width=True` (as do `MarkdownUI`/`ProgressBarUI`).
  `GroupUI` gains `extra_rows`.  `GroupView` gains `visible`/`enabled` state and
  `set_visible`/`set_enabled`/`set_title`.  `ParamsView` gains a private
  `key_prefix` and a dotted `_resolve(key)`; `_build_group` forwards `on_change`,
  `key_prefix` and `extra_rows` to the nested view.
- **Wire** — a row serializes `full_width: true` when title-less; `GroupView`
  serializes `visible`/`enabled` only when non-default.  Row/group state reuses
  `control_state`: `{enabled}` and `{title}` (without `row`) now also route to
  the group view via `_viewRegistry` (the existing `{visible}`/`{collapsed}`
  pattern).
- **Frontend** — `params-view.js` `addRow` treats `full_width` like a nested
  group (no key column).  `group-view.js` gains `setEnabled` (grey header +
  collapse + disable the toggle) and `setTitle`; `viewer.js` routes
  `control_state {enabled}`/`{title}` to the group.

## Fixed contract (decided up front)

### `ControlUI` / `ButtonUI` / `GroupUI`

```python
@dataclass
class ControlUI:
    # …existing fields…
    full_width: bool = False        # NEW — render the row without a key column

@dataclass
class ButtonUI(ControlUI):
    kind = "button"
    label: str | None = None        # NEW — the button's own caption
    icon: str | None = None
    icon_only: bool = False
    full_width: bool = True         # default full-width

@dataclass
class MarkdownUI(ControlUI):
    kind = "markdown"
    full_width: bool = True

@dataclass
class ProgressBarUI(ControlUI):
    kind = "progress"
    total: float | None = None
    indeterminate: bool | None = None
    text: str | None = None
    full_width: bool = True

@dataclass
class GroupUI(ControlUI):
    kind = "group"
    collapsed: bool = False
    extra_rows: list[RowSpec] | None = None   # NEW — rows for the nested view
```

### `GroupView` (additions)

```python
class GroupView(StackView):
    visible: bool = True            # NEW
    enabled: bool = True            # NEW

    def set_visible(self, visible: bool) -> None: ...   # push control_state {visible}
    def set_enabled(self, enabled: bool) -> None: ...   # push control_state {enabled}
    def set_title(self, title: str) -> None: ...        # push control_state {title}
```

Serializes `"visible": False` / `"enabled": False` only when non-default.

### `ParamsView` (additions)

```python
class ParamsView(View):
    def __init__(self, source, styles=None, *, id=None, title="",
                 on_change=None, extra_rows=None, title_from_name=False,
                 dense=False, key_prefix: str = "", **view_kwargs): ...
```

- `_make_handler` / `_make_click_handler` set `event.key = f"{self.key_prefix}{key}"`.
- `_build_group` creates the nested view with `key_prefix=f"{key}."`,
  `extra_rows=ui.extra_rows`, and a wrapped `on_change` that calls the parent's
  `on_change` with the parent's `_state()` (dotted keys bubble up).
- `_resolve(dotted_key)` walks `_control_views` down nested `GroupView.children[0]`
  to the leaf view; `set_value`/`set_visible`/`set_enabled`/`set_title`/
  `set_options` route through it.
- `set_state` rebinds nested groups recursively (no `on_change`).

### Wire

- Row: `{"key", "title", "control", "full_width": true}` (only when full-width).
- `control_state` routing additions in `viewer.js`:
  `{enabled}` → `host.setEnabled(...)`; `{title}` **without** `row` →
  `host.setTitle(...)` (the existing `{row, title}` branch stays for params rows).

## Decisions (confirmed)

- **Title-less rows use an explicit `ControlUI.full_width` flag** (not a
  `title=""` sentinel); it defaults `True` for `ButtonUI`/`MarkdownUI`/
  `ProgressBarUI`.
- **A button's caption is `ButtonUI.label`**; a full-width button renders it
  (no key column, `hide_label` off).
- **`set_enabled` on a group** greys the group header, collapses the group, and
  disables the fold toggle while disabled (re-enabling re-arms the toggle but
  does not force-expand).
- **`set_title` on a group** renames the group header (implemented, not deferred).
- **Nested `extra_rows`** live on `GroupUI.extra_rows` and are forwarded to the
  nested `ParamsView`.
- **Dotted keys** use `event.key == "surface.scale"` and a dotted row API.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-full-width-button-caption.md](./01-full-width-button-caption.md) | `full_width` + `ButtonUI.label` + full-width rows (items 1, 2) |
| 2 | [02-nested-onchange-dotted-keys.md](./02-nested-onchange-dotted-keys.md) | nested shared `on_change` + dotted `event.key` (item 3) |
| 3 | [03-group-row-state.md](./03-group-row-state.md) | `GroupView` visible/enabled/title + frontend grey/collapse/disable-unfold (item 4, group rows) |
| 4 | [04-dotted-row-api-setstate.md](./04-dotted-row-api-setstate.md) | dotted `_resolve()` + recursive `set_state` (item 4) |
| 5 | [05-nested-extra-rows.md](./05-nested-extra-rows.md) | `GroupUI.extra_rows` (item 5) |
| 6 | [06-example.md](./06-example.md) | update `params_view_features.py` + regenerate example docs |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | developer/user docs + changelog (item 6) |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression (extend
  `test_params_view.py`, `test_params_ui.py`, `test_views.py`).
- `uv run ruff check py/pytanga/viz py/tests/viz` and `uv run ty check` — lint + type.
- `node js/dev/tests/check-syntax.mjs` + `node --test js/dev/tests/*.test.mjs` — JS gate.
- `uv run python tools/generate-example-docs.py --check` — example docs (phase 6).
- `uv run mkdocs build --strict` — docs gate (phase 7).

## Non-goals

- No new control kind; no new wire message type (only new `control_state` fields).
- No declarative `visible_if` predicates.
- No `full_width` on value-bearing controls (slider/dropdown/…) beyond the flag
  existing on `ControlUI`; full-width rendering is only exercised for
  button/markdown/progress rows.
- No public `ParamsView.group(key)` accessor — dotted keys are the public path.

