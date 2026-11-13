# Phase 2 — Tagging mode, palette, selected style, click selection

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make tags visible and selectable: a deterministic tag→color palette, a
`tagging` mode, a custom style for the selected vertex, and backend-side
vertex-click selection.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/pytanga/viz/__init__.py` (export `TAG_PALETTE`)
- Edit: `py/tests/viz/test_act_polygon_tags.py`

## Steps

- [x] **2.1 — Tag palette**
  - Add a module-level `TAG_PALETTE` tuple of at least eight distinct CSS hex
    colors.  Avoid the selected color `#ffff44` so selection remains legible.
  - Add `resolve_tag_color(tag, overrides)`:
    - explicit `overrides[tag]` wins;
    - otherwise `TAG_PALETTE[zlib.crc32(tag.encode("utf-8")) % len(TAG_PALETTE)]`;
    - return `None` for a `None` tag.
  - Export `TAG_PALETTE` from `pytanga.viz` (import + `__all__`).
  - Add `self._tag_colors: dict[str, str]` and a `tag_colors` property
    (copy), plus `set_tag_color(tag, color)`.

- [x] **2.2 — Tagging mode**
  - Add constructor kwarg `tagging: bool = False` and `_tagging`.
  - Add `tagging` property and `set_tagging(tagging: bool)`.
  - `set_tagging` and `set_tag_color` call `_restyle_handles()`.
  - A tag color is shown **only** when `tagging=True`; untagged vertices fall
    back to the normal handle/endpoint style.

- [x] **2.3 — Selected style and click selection**
  - Add constructor kwargs:
    - `selected_handle_style: PointStyle | None = None`
    - `select_on_click: bool = True`
    - `on_vertex_click: Callable[[int, ClickEvent, ActPolygon], Awaitable[None]]
      | None = None`
  - Default selected style: a copy of the resolved base handle style with
    `color="#ffff44"` (use `dataclasses.replace`).  `None` means "no custom
    selected style".
  - Add `selected_handle_style` property and `set_selected_handle_style(style)`.
  - Add `_make_vertex_click_handler(index)` for vertex handles:
    1. if `select_on_click`, call `set_selected_vertex(index)`;
    2. fire `on_vertex_click(index, event, self)` when set;
    3. call the body's `_on_click(event, self)` (if set), preserving the
       existing "click a handle selects the shape" behaviour.
  - Use this handler only for vertex handles; the translate handle keeps
    `_handle_click_handler()`.

- [x] **2.4 — Restyling precedence**
  - Add `_vertex_base_style(index)`:
    - start with `end_handle_style` when the vertex is an open endpoint and
      `tagging=False`, else `handle_style`/`_resolve_handle_style()`;
    - when `tagging=True` and the vertex has a tag, return a copy of that base
      style with the resolved tag color;
    - ensure the returned style has an explicit color (use the canonical
      `#ff4444` fallback when the base style has `color=None`).
  - Add `_vertex_style(index)`: selected style when the vertex is selected,
    else `_vertex_base_style(index)`.
  - Add `_restyle_handles()`: for every vertex handle call
    `self._viz_handle.update_style(entity_id, style)` (or `update(...)` with an
    explicit `color`) and `flush()` once.  Restoring a base style must also
    restore the color when the base style's `color` is `None`.
  - `_spawn_handles` uses `_vertex_style(i)` instead of the endpoint/inner
    branch; `_rebuild_handles` therefore re-spawns with current tags and
    selection.
  - `set_vertex_tag(s)`, `set_tag_color`, `set_tagging`,
    `set_selected_vertex`, and `set_selected_handle_style` call
    `_restyle_handles()`.

- [x] **2.5 — Tests**
  - `tagging=False`: tags do not change handle styles; endpoint styles still
    apply to open endpoints.
  - `tagging=True`: a tagged vertex uses the palette color; an explicit
    `set_tag_color("a", "#123456")` wins; untagged vertices use the base style.
  - Selection: `set_selected_vertex(1)` applies `selected_handle_style`;
    `set_selected_vertex(None)` restores the tag/base color; selected style
    wins over tag color; endpoint style is suppressed in tagging mode.
  - Click: `on_vertex_click` receives the index; `select_on_click=False` leaves
    the selection unchanged but still fires the callback; body `on_click` still
    fires.
  - `on_change` is not fired for tag or selection changes.
  - `TAG_PALETTE` is deterministic: the same tag always resolves to the same
    color.

## Validation

`uv run pytest py/tests/viz/test_act_polygon.py py/tests/viz/test_act_polygon_tags.py -q`

## Notes

- `PointStyle`/`CirclePointStyle`/`SquarePointStyle` are dataclasses; use
  `dataclasses.replace` for the selected copy.
- Do not restyle the translate handle.
- Selection is backend state only; no new frontend event type is added.
