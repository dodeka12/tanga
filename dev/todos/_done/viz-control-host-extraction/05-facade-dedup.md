# Phase 5 — Collapse `_add_scene_*` → `_add_scene_control`

## Goal

Replace the 11 near-identical `_add_scene_*` methods with one table-driven
generic, keeping the public `add_*` / `VizSceneHandle.add_*` signatures intact.

## Files

- Edit: `py/pytanga/viz/_hosts.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`

## Steps

- [x] **5.1 — Kind → view table**
  - In `ControlHost`, add a `_KIND_VIEWS: dict[str, type[ControlView]]` mapping
    `"slider"`, `"dropdown"`, `"button"`, `"file_chooser"`, `"text"`,
    `"textarea"`, `"table"`, `"color"`, `"checkbox"`, `"value_edit"` to their
    `*View` classes.

- [x] **5.2 — Generic `_add_scene_control(kind, cid, **fields) -> str`**
  - Build `view = _KIND_VIEWS[kind](cid, **fields)`, call
    `_mount_orphan_control(scene_name, view)`, return `cid`.
  - Raise `KeyError`/`TypeError` on unknown `kind`.

- [x] **5.3 — Thin typed `add_*`**
  - Keep each `add_slider` / `add_table` / … with its exact signature, but its
    body becomes `return self._add_scene_control("slider", cid, label=..., …)`.
  - Delete the 11 `_add_scene_*` methods (their `_add_scene_control` call sites
    replaced).

- [x] **5.4 — `VizSceneHandle.add_*`**
  - Keep the per-scene `add_*` methods as thin forwarders to
    `self._viz._controls.add_*(...)` (or `self._viz.add_*(...)`), unchanged in
    signature.

- [x] **5.5 — Tests**
  - Full `py/tests/viz` suite passes unchanged (facade signatures are stable).

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- Only the `_add_scene_*` plumbing is deduped; the public `add_*` methods keep
  their typed signatures/docstrings for IDE + API stability.
