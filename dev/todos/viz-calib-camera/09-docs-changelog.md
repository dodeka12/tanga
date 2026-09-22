# Phase 9 — Docs & changelog

## Goal

Document the new camera/lock/visibility/background features and the `Frustum`
entity in the developer architecture docs and public user docs, add the branch
changelog, and prepare the PR.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/py/viz/visualizer/camera.md`
- Edit: `docs/py/viz/ui/split-views.md`
- Edit: `docs/py/viz/entities/index.md` (or the entities nav) — add `Frustum`
- New: `docs/changelog/2026/09/21_feat-calib-cam-view.md`
- (PR-time) Edit: `docs/changelog/index.md`

## Steps

- [x] **9.1 — developer architecture docs**
  - `viz-architecture.md`: optional `intrinsics` on `CameraConfig3d`, the
    `pinhole_camera` factory, per-pane `SceneView.lock` / `hide` / `show` /
    `background_image`, the off-center projection path in `view_mode.js`, the
    `Frustum` entity + `FrustumStyle`, and the NDC background renderer.
  - `viz-controls-and-interactions.md`: note `lock`/`hide`/`show` are per-pane
    camera/visibility controls (not new `(id, event)` controls).

- [x] **9.2 — public docs**
  - `camera.md`: `pinhole_camera(...)` + `CameraConfig3d.intrinsics`.
  - `split-views.md`: `SceneView(lock=…)`, `SceneView(hide=…, show=…)`,
    `SceneView(background_image=…)` with a small example.
  - Entities docs: `Frustum` + `Frustum.from_camera` + `FrustumStyle`.

- [x] **9.3 — branch changelog**
  - `docs/changelog/2026/09/21_feat-calib-cam-view.md` per
    `dev/workflows/changelog.md`: title from `uv run python tools/last-release.py`
    (no hard-coded version), `## New Features` bullets for pinhole camera, lock,
    image background, per-pane visibility, and `Frustum`.

- [ ] **9.4 — PR prep**
  - Follow `dev/workflows/pull-request.md`: squash, rename changelog to hash form,
    add `docs/changelog/index.md` entry.

## Validation

`uv run mkdocs build --strict && uv run python tools/last-release.py`

## Notes

- Update the architecture docs *in this phase* so they land with the code and
  reflect the final contract (including the new `Frustum` entity + visibility
  filter).
- The `index.md` changelog entry is added at PR time, after the hash rename.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
