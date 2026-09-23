# Phase 7 — Docs & changelog

## Goal

Update the developer architecture docs and public user docs for the cleaned-up
model, refresh the branch changelog, and prepare the PR.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/py/viz/visualizer/camera.md`
- Edit: `docs/py/viz/ui/split-views.md`
- Edit: `docs/py/viz/entities/index.md`
- Edit: `docs/changelog/2026/09/21_feat-calib-cam-view.md` (append/refresh)

## Steps

- [x] **7.1 — architecture docs**
  - Rewrite the "Calibrated camera view" recipe to describe `PinholeCamera` +
    `CameraView` + `pinholeFraming` (replacing the `intrinsics` / `SceneView.lock`
    / `SceneView.background_image` wording).

- [x] **7.2 — public docs**
  - `camera.md`: `PinholeCamera` + `fit`; `split-views.md`: `SceneView(camera_view=…)`
    with `lock`/`background_image` inside `CameraView`.

- [x] **7.3 — changelog**
  - Refresh the branch changelog bullets to reflect `PinholeCamera`/`CameraView`.

- [ ] **7.4 — PR prep (deferred)**
  - Per `dev/workflows/pull-request.md`: squash, rename changelog to its hash
    form, add the `docs/changelog/index.md` entry.

## Validation

`uv run mkdocs build --strict`

## Notes

- `index.md` changelog entry is added at PR time.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
