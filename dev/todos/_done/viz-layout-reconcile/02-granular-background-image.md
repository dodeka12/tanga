# Phase 2 — Granular background-image update (B)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add `Visualizer.set_background_image(view, image)` so a single pane's
`CameraView.background_image` can be swapped at runtime **without** a full
`view_layout` re-push. It sends one binary frame (the pixels) followed by one
`view_background_image` JSON message, mirroring `view_camera`/`view_viewport`.

## Files

- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/tests/viz/test_image_background.py` (or add a focused test)

## Steps

- [x] **2.1 — `LayoutHost.push_background_image(view, image)` (`_layout.py`)**
  - Add a method that: (a) asserts `view` is a `SceneView`; (b) sets
    `view.camera_view = CameraView()` if it is `None`, then
    `view.camera_view.background_image = image`; (c) when `image.data is not
    None`, encodes with `_image_wire.encode_image_frame(image.id, image.data)`,
    stores it in `self._background_frames[image.id]` (so
    `background_image_frames()` re-sends on reconnect), and calls
    `self._transport.send_bytes(frame)`; (d) sends
    `self._transport.send({"type": "view_background_image", "view_id": view.id,
    "image": _image_meta(image)})`.
  - Reuse the imports already used by `_collect_background_frames`
    (`encode_image_frame`, `_image_meta`); add `SceneView`/`CameraView` imports
    as needed.

- [x] **2.2 — `Visualizer.set_background_image(view, image)` (`visualizer.py`)**
  - Add a public forwarder (mirrors `set_view_camera`): validate `SceneView`,
    delegate to `self._layout.push_background_image(view, image)`, with a
    docstring noting it does **not** re-push the layout.

- [x] **2.3 — Frontend dispatch (`viewer.js`)**
  - Next to the `view_camera`/`view_viewport` branches, add:
    `if (msg.type === 'view_background_image') { const t = _viewById.get(msg.view_id);
    if (t) t.setBackgroundImage(msg.image); return; }`
  - `ThreeJsView.setBackgroundImage` already exists and re-creates the NDC quad
    from `makeDataTexture` (`takeImageFrame(image.id)` reads the freshly sent
    frame).

- [x] **2.4 — Test**
  - Add a test asserting `set_background_image` on a `SceneView` (with a fake
    server/transport) records exactly one `view_background_image` message and
    one binary frame, and updates `_background_frames` (model on
    `test_image_canvas_integration.py::test_set_image_sends_one_binary_frame`).

## Validation

```
uv run pytest py/tests/viz/test_image_background.py -q
uv run pytest py/tests/viz -q
```

## Notes

- Binary-first ordering matters: `image-frames.js` must hold the frame before
  `setBackgroundImage` runs `takeImageFrame`, otherwise the texture is empty.
  WebSocket delivery is ordered, and we send bytes before the JSON message.
- A fixed image `id` ("camera") is fine for streaming — each frame overwrites
  `_background_frames[image.id]` and the stored `image-frames.js` entry.
