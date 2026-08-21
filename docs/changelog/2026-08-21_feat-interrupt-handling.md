# Changes since version 0.12.0

## New Features
- **Per-scene browser interrupt key** — `Visualizer.animate()` and
  `VizSceneHandle.animate()` now accept `stop_key` (default `"q"`) and
  `stop_modifiers` (`KeyModifier` values) so an animation loop can be stopped
  from the browser without shutting the server down; terminal Ctrl+C / SIGTERM
  remains a global interrupt that stops every scene loop.

## Breaking Changes
- **`animate()` no longer stops the server on loop exit** — server teardown is
  handled by the `atexit` hook registered when the server starts, so a
  per-scene `q` interrupt (or a Python exception escaping the loop) leaves the server
  running. The main-scene `finally: stop_server()` behaviour was removed.

## Refactor
- **General `KeyModifier` enum** — added `pytanga.viz.KeyModifier` (values
  `ctrl`, `shift`, `alt`, `meta`) as the shared source of truth for keyboard
  modifiers, exported from the `pytanga.viz` package.