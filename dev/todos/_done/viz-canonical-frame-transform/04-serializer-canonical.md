# Phase 4 — Shape-only serialization + glTF export

## Goal

Make `_serialize_content()` emit **shape-only** content (no placement fields)
and have placement ride on the node `transform`; update the glTF exporter to
read the node transform instead of re-deriving position/rotation from geometry.

## Files

- Edit: `py/pytanga/viz/serializer.py` (shape-only `_serialize_*`)
- Edit: `py/pytanga/viz/_nodes.py` (`_serialize_content` already excludes
  `transform`; ensure shape-only)
- Edit: `py/pytanga/viz/export/_gltf.py` (read node transform)

## Steps

- [x] **4.1 — shape-only content**
  - In each `_serialize_<kind>()`, drop the placement keys
    (`center`/`normal`/`axis`/`origin`/`direction`/`vertex`/`rotation`/
    `startDirection`) and emit only shape keys; reuse `_entity_decompose` for
    the placement side (already set on the node `transform` in Phase 3).
  - `Frustum` is excluded here (re-parameterized in Phase 6); its current
    corner serializer stays for now.

- [x] **4.2 — placement on the node**
  - `serialize()` continues to emit `"transform": self.transform.to_dict()`,
    which is now the entity's placement (non-identity). No content field
    duplicates it.

- [x] **4.3 — glTF exporter**
  - Replace `_get_position`/`_get_rotation` (`_gltf.py:403-460`) with reads of
    `ent["transform"]["position"]` and `ent["transform"]["rotation"]`
    (quaternion); keep the canonical primitives (they already match the new
    canonical frames: cylinder +Y, circle/plane +Z).

- [x] **4.4 — serializer tests**
  - Assert `center`/`normal`/etc. are absent from `_serialize_content` output,
    and that `serialize()` carries the placement in `transform`.

## Validation

`uv run pytest py/tests/viz/test_serializer.py py/tests/viz/test_conic_renderers.py py/tests/viz/test_export_renderers.py -q`

## Notes

- This is the wire-contract change: content no longer carries placement, so the
  frontend must rely on `transform` (Phase 5 renderers + `applyTransformToObject`
  already support this).
- Keep `serialize_entity()` (the standalone function) working; it should return
  a dict whose `transform` reflects placement for direct callers.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
