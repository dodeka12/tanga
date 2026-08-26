# Changes since version 1.5.0

## New Features
- **Awaitable scene flush (`flush_async()`)** — `Visualizer.flush_async()` and
  `VizSceneHandle.flush_async()` await the WebSocket push to completion, so an
  async control/interaction handler can force a redraw before blocking the
  event loop with a long synchronous computation (e.g. show a "Calculating…"
  annotation first).  It runs inline on the server loop and cross-loop safely
  otherwise.
- **Blocking flush for synchronous scripts (`flush(wait=True)`)**
  — `Visualizer.flush()`, `VizSceneHandle.flush()`, and `VizObjectRef.flush()`
  now accept `wait=True` to block until the push has been processed.  Calling
  `flush(wait=True)` from the server's own event loop raises a clear
  `RuntimeError` (use `flush_async()` there) instead of deadlocking.
- **Banners & dialogs** — `Visualizer.show_banner()` / `alert()` / `confirm()`
  show transient, backend-removable overlays with markdown/KaTeX text, custom
  option controls, fractional alignment, auto-hide, and a modal
  (`dismissable=False`) variant; `show_banner_async()` awaits the push, and
  `VisualizerApp.submit_user()` / `run_user()` / `run_user_sync()` (plus
  `Visualizer.run_blocking()`) let a control handler offload compute to the
  user loop without stalling the viewer.
- **Slider press/release events** — `Slider` / `add_slider` gain `on_press` and
  `on_release` handlers (dispatched from the slider's pointerdown / change
  events), so a handler can react to the start and end of a drag.
- **File chooser** — `Visualizer.add_file_chooser()` adds a file-path control
  (text field + "Browse…") backed by a custom, backend-driven file browser
  (`open_file_chooser()` opens it programmatically).  The browser lists the
  server's filesystem over WebSocket, is modal, and is rooted at the home
  directory (configurable via `root=`).  Selecting or typing a path fires an
  `on_change` handler.
