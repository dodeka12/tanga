# Phase 7 — Examples, developer docs, changelog

## Goal

Ship it: update the pinhole example to use `"2d"` navigation + a `set_viewport`
reset, document the new per-pane viewport/navigation model in the developer
docs, and write the branch changelog.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/examples/viz/camera/pinhole_overlay.py`
- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New/Edit: `docs/changelog/2026/09/21_feat-calib-cam-view.md` (branch changelog)
- Regenerate: `docs/py/examples/**` (via the docs generator)

## Steps

- [x] **7.1 — example**
  - In `pinhole_overlay.py`, use `CameraView(cam, navigation="2d",
    controls={"left": "pan"}, viewport=ViewportConfig(zoom=1.0, pan=(0,0)))` on
    the locked camera pane, and add a control handler that calls
    `viz.set_viewport(left, zoom=1.0, pan=(0.0, 0.0))` (or
    `scene.set_viewport(...)`) to reset the view.
  - Keep `pinhole_camera.py` as the orbit demo (no `navigation="2d"`).
  - Regenerate example docs (per `dev/workflows/example-docs.md`).
- [x] **7.2 — developer docs**
  - `viz-architecture.md`: extend the "Calibrated camera view" recipe with the
    `"2d"` navigation + `viewport` crop-window + `view_viewport` message.
  - `viz-controls-and-interactions.md`: extend the "Per-pane camera view &
    visibility" section with `navigation`, per-pane `controls`, `viewport`, and
    the `view_viewport` dispatch (no new registry/channel).
- [x] **7.3 — changelog**
  - Append a New Features bullet for viewport navigation + `set_viewport()` and
    a Bug Fixes bullet for the `DataTexture` flipY fix (see
    `dev/workflows/changelog.md`).
- [x] **7.4 — full gate**
  - `uv run pytest -q`, `uv run ruff check .`, `uv run ty check`,
    `uv run mkdocs build --strict`.

## Validation

```
uv run pytest -q && uv run mkdocs build --strict
```

## Notes

- The branch changelog is renamed to its hash form only at PR time
  (`dev/workflows/pull-request.md`) — keep the `21_feat-calib-cam-view.md` name
  during this branch.
- The `DataTexture` flipY renderer fix is committed *before* this plan; still
  list it under Bug Fixes in the changelog (7.3).
