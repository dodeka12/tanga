# Phase 3 — `viz.add`/`viz.new` routing + ref uniform API

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("Add an entity" data flow,
> "`VizObjectRef`") and `viz-controls-and-interactions.md` for the granular
> message pattern.  This phase adds the `depth_image_update` granular message
> (server side) and the public `set_uniform`/`set_selected_segments` surface.

## Goal

Route `DepthImage` through `viz.add`/`viz.new` (like other entities), push its
binary frames + payload on add, and expose live uniform/segment updates through
`VizObjectRef`.

## Files

- Edit: `py/pytanga/viz/scene.py` (`add_viz` routing, `set_depth_image_uniform`,
  `set_depth_image_selected_segments`, live frame push in `add_depth_image`)
- Edit: `py/pytanga/viz/visualizer.py` (optional `add_depth_image` forwarder)
- Edit: `py/pytanga/viz/_object_ref.py` (`set_uniform`, `set_selected_segments`)
- New: `py/tests/viz/test_depth_image_integration.py`

## Steps

- [x] **3.1 — Route `DepthImage` in `Scene.add_viz`.**
  - At the top of `add_viz` (next to the `VizGroup`/`ActSceneObject`/`Label`
    branches), detect `isinstance(obj, DepthImage)`; resolve
    `_style_to_output(style, "DepthImage", self.styles.kind)` (fold in
    `color`/`opacity` as the existing `_normalize_color`/properties logic does);
    build `payload, frames = obj._build(resolved_style, eid)`; call
    `add_depth_image(eid, payload, images=frames)`; `_attach_to_parent`; return
    `eid`.

- [x] **3.2 — Live frame push on add.**
  - In `Scene.add_depth_image`, after registering the node, if
    `self._host` has a live `_transport`, `send_bytes` each frame (bytes first,
    then the JSON flush — matches `ImageCanvas._sync_image` ordering).  Guard
    for `_host is None`/no transport (pre-`show()` adds rely on the connect-time
    `_image_frames_for` path from Phase 2).

- [x] **3.3 — `Scene.set_depth_image_uniform` / `set_depth_image_selected_segments`.**
  - Add `Scene.set_depth_image_uniform(object_id, name, value)` updating the
    node's payload `uniforms[name]`, marking `"full"` (or a dedicated aspect),
    and — via `self._host._transport` if live — sending
    `{type:"depth_image_update", scene:self.name, id, uniforms:{name:value}}`.
  - Add `Scene.set_depth_image_selected_segments(object_id, ids)` normalizing
    `ids` (empty/`None` → disable filter), padding to `MAX_SELECTED_SEGMENTS`,
    and pushing `u_selected_segments`/`u_num_selected`/`u_seg_enabled` in one
    `depth_image_update`.

- [x] **3.4 — `VizObjectRef` surface.**
  - Add `set_uniform(name, value)` and `set_selected_segments(ids)` to
    `VizObjectRef`, delegating to `self._handle.scene.set_depth_image_*` and
    raising `TypeError` when `self._node` is not a `VizDepthImage`.

- [x] **3.5 — Tests.**
  - `test_depth_image_integration.py`: `viz.add(DepthImage(...))` returns an id
    and the node is a `VizDepthImage`; `viz.new(...)` returns a `VizObjectRef`
    whose `set_selected_segments`/`set_uniform` mutate the payload uniforms and
    (with a fake transport) emit a `depth_image_update` message.

## Validation

`uv run pytest py/tests/viz/test_depth_image_integration.py py/tests/viz/test_object_ref.py -q`

## Notes

- Follow the existing granular `image_update` seam (`ImageCanvas.set_uniform`),
  but with the `depth_image_update` type; the frontend dispatch lands in Phase 5.
- `set_depth_image_uniform`/`set_depth_image_selected_segments` live on `Scene`
  (not the entity) so `viz.add` stays transport-free.
