# Changes since version 2.18.0

## New Features
- **`ImageData.update()` and a per-instance `version`** — each `ImageData` now
  carries a `version` (a uuid assigned at construction) plus an
  `update(data=…)`/`update(url=…)` method that swaps the content in place and
  bumps the version.  Reusing the same instance across a `set_layout` re-push
  lets the viewer skip re-encoding/re-sending an unchanged background image.

## Bug Fixes
- **`CameraView.background_image` no longer goes black after a WebSocket
  reconnect** — the pane now rebuilds the background quad on `clear_all`
  instead of updating a disposed mesh, and an unchanged background keeps its
  previous texture (instead of re-decoding, or blanking when no frame is
  re-sent).
