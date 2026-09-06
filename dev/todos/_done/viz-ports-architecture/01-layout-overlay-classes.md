# Phase 1 — `Layout` + `OverlayContainer` classes

## Goal

Introduce the first-class `Layout` (a `base` view + an `overlay` container) and
the explicit `OverlayContainer`; move the flat overlay state (`_global_overlay` /
`_scene_overlays` / `_injected_overlay_ids`) into it.  Behavior-preserving.

## Files

- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/_hosts.py` (`ControlHost` adapts to `layout`)
- Edit: `py/pytanga/viz/visualizer.py`

## Steps

- [x] **1.1 — `OverlayContainer`**
  - New class owning the overlay views + anchor bookkeeping; absorbs
    `_global_overlay`/`_scene_overlays`/`_injected_overlay_ids` and
    `_mount_orphan_group`/`_remove_group_view`; exposes `add(view, *, anchor)` and
    `_serialize_children()` (what `serialize_layout` consumes).
- [x] **1.2 — `Layout`**
  - New class with `base: View` and `overlay: OverlayContainer`.
- [x] **1.3 — `LayoutHostImpl` holds layouts**
  - Change `_layouts: dict[str, View]` → `dict[str, Layout]`; adapt
    `_sync_overlays`/`_inject_scene_overlays`/`_scene_layout_for`/`serialize_layout`
    to read `layout.base`/`layout.overlay`.
- [x] **1.4 — Wire + green**
  - `Visualizer` + `ControlHost` keep calling the same serialization entry points.

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- No wire change: `view_layout` output is identical.
