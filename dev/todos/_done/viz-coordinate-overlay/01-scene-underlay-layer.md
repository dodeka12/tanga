# Phase 1 — Scene-object `underlay` layer

## Goal

Add a general `layer="underlay"` to the scene-object model (besides `scene` and
`overlay`) so payload-style objects can be routed to a per-pane underlay region.
This phase establishes the model seam only; the grid renderer that uses it lands
in later phases.

## Files

- Edit: `py/pytanga/viz/scene.py`
- Edit: `py/pytanga/viz/_nodes.py`

## Steps

- [x] **1.1 — widen the layer literal**
  - In `SceneObject`, change `layer: Literal["scene", "overlay"]` to
    `Literal["scene", "overlay", "underlay"]` and update the docstring.

- [x] **1.2 — generalize `VizOverlayObject` for underlay**
  - Add a `layer: str = "overlay"` kwarg to `VizOverlayObject.__init__`, pass it
    through to `super().__init__(..., layer=layer, ...)`, and use `self.layer`
    (not the hardcoded `"overlay"`) in `serialize()`.
  - Add `axes_overlay` / `grid_underlay` branches in `serialize()` that emit
    `result["spec"] = self.payload` (before the generic `else`).

- [x] **1.3 — route underlay in `Scene._make_node`**
  - In `_make_node`, route `obj.layer == "underlay"` to `_make_overlay_node`
    (the same payload-style node builder), passing `layer="underlay"`.
  - In `_make_overlay_node`, accept/generalize so a dict `data` with a `"spec"`
    key becomes the node `payload` (for `axes_overlay`/`grid_underlay`), keeping
    the existing `label` branch unchanged.

- [x] **1.4 — tests**
  - Add an underlay object via `Scene.add_object`; assert its serialized node has
    `layer == "underlay"`, appears in `full_state()` and `flush()` diffs, and is
    removed by `remove()`.

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- `VizNode.serialize()` already emits `self.layer`, and `Scene._dfs_preorder()`
  already visits non-`VizSceneObject` nodes, so no flush/full-state change is
  needed beyond the node construction/`layer` plumbing.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
