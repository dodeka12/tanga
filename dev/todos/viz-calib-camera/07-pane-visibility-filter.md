# Phase 7 — Per-pane entity visibility (`SceneView.hide` / `SceneView.show`)

## Goal

Add `SceneView(hide=..., show=...)` so a pane renders only a subset of a shared
scene's entities. This is what lets the frustum appear in the overview pane but
not in the locked camera pane, without duplicating the scene.

## Files

- Edit: `py/pytanga/viz/views.py` (`SceneView.hide`/`show` + serialize)
- Edit: `py/pytanga/viz/templates/views/three-view.js` (apply filter in `_upsertObject`)
- Edit: `py/tests/viz/test_views.py`

## Steps

- [x] **7.1 — `SceneView.hide` / `SceneView.show`**
  - Add `hide: set[str] | None = None` and `show: set[str] | None = None`
    (sets of entity ids). `None`/empty = no filter. Validate ids are non-empty
    strings.

- [x] **7.2 — serialize**
  - Emit `"hide": [...]` / `"show": [...]` (sorted) only when non-empty.

- [x] **7.3 — frontend filter**
  - In `ThreeJsView._upsertObject`, if this pane's filter excludes `msg.id`
    (`hide` contains it, or `show` is set and does not contain it), skip building
    the mesh (or set `entry.obj.visible = false`); apply on initial build and on
    layout re-push. Each pane owns its own registry, so the filter is naturally
    per-pane.

- [x] **7.4 — tests**
  - Serialization round-trip; a filtered id is hidden/omitted while unfiltered
    ids still render (assert via the serialized filter only — no browser).

## Validation

`uv run pytest py/tests/viz/test_views.py -q && node --check py/pytanga/viz/templates/views/three-view.js && uv run python tools/build-viewer-js.py --check`

## Notes

- `VizNode.visible` is per-object and global; `hide`/`show` are the per-pane
  mechanism (the original two-scene-sync question's answer).
- Reuse the pane's existing `sceneObjects` registry — no new protocol, just a
  filter in the already per-pane entity build path.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
