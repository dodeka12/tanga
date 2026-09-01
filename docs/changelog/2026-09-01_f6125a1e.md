# Changes since version 1.14.0

## Bug Fixes
- **2D `fit_camera` now fits to the pane, not the window** —
  `Visualizer.flush(fit_camera=True)` on a 2D scene now frames the
  orthographic camera to the `SceneView` pane's rendered size, so split-view
  2D scenes are correctly aspected on the first paint instead of appearing
  squashed until the pane is resized. The 2D auto-fit also became a true
  contain-fit of the content bounds, so wide content is no longer clipped in a
  narrow pane.

## Refactor
- **Unified the 2D camera-fit math into one shared module** — the orthographic
  frustum and aspect computation (previously duplicated across `view_mode.js`,
  `fit_camera.js`, and the HTML export bootstrap) now lives in a single pure
  `camera-fit.js` used by the live viewer, the auto-fit, and HTML exports,
  eliminating the copy-and-drift regressions that caused this class of bug.
