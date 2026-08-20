# Phase 15c — Anchor wiring into `compute_label_position` + callers

**Parent:** [15-label-anchors-rotation.md](./15-label-anchors-rotation.md)
**Status:** Done

## Goal

Replace the implicit "mesh origin" anchor with the per-entity anchor from
`_label_anchor.py`, and thread the needed inputs (resolved `along` + line
length) through the two callers.

## 1. `compute_label_position`

File: `py/pytanga/viz/_label_frame.py`

- [x] Change the signature to accept the anchor inputs:
      `compute_label_position(entity, offset_local=None, *, along=None, line_length=None)`.
- [x] Body: `anchor = compute_label_anchor(entity, along=along, line_length=line_length)`
      then return `anchor + (offset_local in entity frame)` (the existing frame math).
- [x] Import `compute_label_anchor` from `._label_anchor`.

## 2. `visualizer.py _add_to_scene`

- [x] When the entity is a `Line`/`ReflectionLine`, resolve
      `line_length = resolve_line_length(line, styles_map=self._default_styles, props=properties)`.
- [x] Pass `along=resolved_ls.along`, `line_length=line_length` into
      `compute_label_position`.

## 3. `scene.py update_label`

- [x] Recompute position when `offset_local` **or** `along` changed (currently
      only `offset_local`).
- [x] Resolve the parent's line length when the parent is a `Line`, and pass
      `along` from the merged label style.

## 4. Remove dead code

- [x] Delete `get_label_anchor()` from `_label.py` (superseded by
      `_label_anchor.compute_label_anchor`). It has no callers.

## Tests

- [x] Line label serialized `position` == midpoint (finite and default-length).
- [x] `update_label` recomputes position when `along` changes.
- [x] `test_label_frame.py` updated to the new signature.
