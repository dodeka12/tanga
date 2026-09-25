# Phase 6 — MJPEG camera stream

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Stream 15–30 Hz camera frames to the frontend over MJPEG
(`multipart/x-mixed-replace`) at `/stream/{id}`, decoupled from the WebSocket
scene channel.

## Files

- New: `py/pytanga/viz/_camera_stream.py` (`CameraStream` publisher)
- Edit: `py/pytanga/viz/server.py` (register `/stream/{id}` route + registry)
- Edit: `py/pytanga/viz/visualizer.py` (public `register_camera_stream` hook)
- Edit: `py/pytanga/viz/templates/renderers/image-background.js` (video/`<img>`
  texture path) and/or a small `stream.js`
- New: `py/tests/viz/test_camera_stream.py`

## Steps

- [x] **6.1 — `CameraStream` publisher (`_camera_stream.py`)**
  - `.publish(image)` (numpy or `ImageData`) encodes JPEG (lazy Pillow, reuse
    Phase 1) and fans the latest frame to subscribers; drop frames for slow
    consumers (keep only the newest).

- [x] **6.2 — server route**
  - `VizServer` gains `register_camera_stream(stream_id, stream)` and a
    `GET /stream/{stream_id}` handler writing
    `multipart/x-mixed-replace; boundary=tanga` parts (`Content-Type:
    image/jpeg`).  Registered before the `/{name:.*}` catch-all.

- [x] **6.3 — public hook**
  - `Visualizer.register_camera_stream(stream_id, *, fps=30)` returns the
    `CameraStream`; no-op before server boot.

- [x] **6.4 — frontend consumption**
  - A background image / pane can point at `/stream/{id}` (an `<img>` or a
    `VideoTexture`-style texture); reuse the existing `source === "url"` path
    and update the texture on each new frame (or use a hidden `<img>` +
    `texImage2D`).

- [x] **6.5 — tests**
  - Unit-test `CameraStream.publish` fan-out and the multipart route with an
    aiohttp test client.  The `camera_stream.py` example is authored in
    [Phase 7](./07-examples.md).

## Validation

```powershell
uv run pytest py/tests/viz/test_camera_stream.py -q
uv run ruff check py/pytanga/viz/_camera_stream.py py/pytanga/viz/server.py
node js/dev/tests/check-syntax.mjs
```

## Notes

- This is the simplest standard camera transport; WebRTC is a later,
  out-of-scope upgrade (README Non-goals).
- Frame encoding is shared with Phase 1's JPEG encoder; do not duplicate it.
