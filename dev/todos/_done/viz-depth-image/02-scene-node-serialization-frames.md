# Phase 2 — Scene node + serialization + binary frames

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("New entity kind", "Image canvas
> (extension recipe)" — the `VizImage` node and binary frame flow).  This phase
> adds the `VizDepthImage` payload node and the connect-time frame emission.

## Goal

Add the `VizDepthImage` scene node and let a `Scene` register/serialize a depth
image, emitting its depth/segmentation/image pixels as id-keyed binary frames on
connect.

## Files

- Edit: `py/pytanga/viz/_nodes.py` (add `VizDepthImage`)
- Edit: `py/pytanga/viz/scene.py` (`add_depth_image`, `upsert_depth_image`,
  `depth_image_frames`, import `VizDepthImage`)
- Edit: `py/pytanga/viz/visualizer.py` (`_image_frames_for` includes depth frames)
- New: `py/tests/viz/test_depth_image_node.py`

## Steps

- [x] **2.1 — `VizDepthImage` node.**
  - In `_nodes.py`, add `VizDepthImage(VizSceneObject)` mirroring `VizImage`:
    `__init__(id, payload, *, name="depth_image", images=None)` storing
    `self.payload` and `self.images` (the list of `ImageData` for depth/seg/image
    frames); `serialize()` returns the payload verbatim; `patch("full")` returns
    the full dict and `patch("visible")` the visibility patch, else raises.

- [x] **2.2 — `Scene.add_depth_image` / `upsert_depth_image`.**
  - Import `VizDepthImage` in `scene.py`.  Add `add_depth_image(image_id,
    payload, images=None)` and `upsert_depth_image(...)` mirroring
    `add_image`/`upsert_image`, registering a `VizDepthImage` node.

- [x] **2.3 — `Scene.depth_image_frames`.**
  - Add `depth_image_frames()` returning `[(img.id, encode_image_frame(img.id,
    img.data)) for img in node.images if img.data is not None]` over
    `VizDepthImage` nodes in `_dfs_preorder()` (mirror `image_frames()`).
  - In `visualizer.py::_image_frames_for`, return
    `scene.image_frames() + scene.depth_image_frames()`.

- [x] **2.4 — Tests.**
  - `test_depth_image_node.py`: node `serialize()` round-trips the payload and
    `patch("full")`/`patch("visible")`; `Scene.add_depth_image` + `flush()` emits
    a `full` patch for the node; `depth_image_frames()` encodes depth (float32)
    and segmentation (uint16) frames whose ids match the payload metadata ids
    (use `decode_image_frame` to check the round-trip).

## Validation

`uv run pytest py/tests/viz/test_depth_image_node.py py/tests/viz/test_image_wire.py -q`

## Notes

- The frames passed to `add_depth_image` are the already-downscaled `ImageData`s
  produced by `DepthImage._build` (Phase 1); `Scene` only stores + encodes them.
- No frontend changes in this phase; `factory.js` will dispatch `depth_image`
  in Phase 4.
