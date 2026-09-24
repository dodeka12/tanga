# Phase 4 — Example: streaming noise background + pane swap

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add a new `.py` example (based on `pinhole_calibrated.py`'s two-pane structure)
that (a) streams a different random-noise background image at 4 fps via
`set_background_image`, and (b) has a toolbar in a split pane above the views
whose button swaps the left/right panes — updating the layout while the
reconciliation keeps the expensive `ThreeJsView` panes alive.

## Files

- New: `py/examples/viz/camera/pinhole_calibrated_streaming.py`

## Steps

- [x] **4.1 — Docstring header (per `dev/workflows/example-docs.md`)**
  - License header + module docstring: one-line description first, a `Run with:`
    line, and a trailing `Keywords:` line (e.g.
    `camera, pinhole, calibration, frustum, image background, streaming, split view, pane swap`).

- [x] **4.2 — Self-contained calibrated scene**
  - Synthesize a `PinholeCamera` (640×480, focal 500 px) and a small scene
    (points + wireframe sphere + the camera's `Frustum`), mirroring
    `pinhole_camera.py`/`pinhole_overlay.py` with **no `data/tless/` dependency**.

- [x] **4.3 — Persistent panes + toolbar layout**
  - Keep `left = SceneView("world", camera_view=CameraView(cam, navigation="2d",
    background_image=noise))` and `right = SceneView("world")` as local
    persistent variables (stable ids).
  - `body = SplitView("horizontal", [left, right])`;
    `toolbar = ToolbarView([ButtonView("swap", label="Swap panes", on_click=_on_swap)])`;
    `layout = SplitView("vertical", [toolbar, body])`.

- [x] **4.4 — Swap handler re-pushes with the same objects**
  - `async def _on_swap(_value, _event): body.children.reverse(); viz.set_layout(layout)`.
  - `left`/`right` objects are reused → reconciliation re-attaches both panes;
    only their DOM order changes.

- [x] **4.5 — 4 fps noise loop**
  - `viz.show(layout=layout)` then
    `for _ in viz.animate(fps=4): viz.set_background_image(left, ImageData("camera", data=rng.integers(...)))`.
  - Reuse a fixed image id `"camera"`; `set_background_image` sends bytes first
    then the `view_background_image` message (Phase 2).

- [x] **4.6 — Regenerate docs + verify**
  - Regenerate the example gallery and confirm the page renders.

## Validation

```
uv run python tools/generate-example-docs.py
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
uv run pytest py/tests/viz -q
```

## Notes

- The noise resolution matches the pinhole `image_size` so the NDC background
  letterboxes correctly (avoids the report's dimension-matching question).
- `viz.animate(fps=4)` runs in the main thread; `_on_swap` runs on the server's
  loop thread — they mutate different objects (`left.camera_view` vs
  `body.children`), so no serialization race.
