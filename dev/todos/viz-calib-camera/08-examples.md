# Phase 8 — Examples

## Goal

Ship the specific calibration-view example — camera view with a background image
on the **left**, 3D view from a different perspective with the **default** camera
on the **right** — plus a free-orbit variant. Both use `Frustum.from_camera(...)`
in the overview pane.

## Files

- New: `py/examples/viz/camera/pinhole_overlay.py` (the specific left/right example)
- New: `py/examples/viz/camera/pinhole_camera.py` (free-orbit + frustum variant)
- New: `docs/py/examples/viz/camera/pinhole_overlay.md`
- New: `docs/py/examples/viz/camera/pinhole_camera.md`
- Edit: `docs/py/examples/index.md` (add both under camera keywords)

## Steps

- [x] **8.1 — `pinhole_overlay.py` (left camera image / right default 3D)**
  - Synthesize `K`, `R`, `t`, `image_size`, and a camera image (numpy buffer with
    projected world points drawn into it via `ImageData`).
  - One shared scene with the 3D objects; `cam = pinhole_camera(K, R, t, image_size=…)`;
    `frustum_ref = scene.new(Frustum.from_camera(cam))`.
  - Layout `SplitView("horizontal", [ left, right ])`:
    - `left = SceneView(scene_name, camera=cam, lock={"rotate","pan","zoom"},
      background_image=ImageData(...), hide={frustum_ref.id})`
    - `right = SceneView(scene_name)`  (default camera, auto-fit; shows the frustum)
  - Docstring + `Run with:` + `Keywords:` (e.g.
    `camera, pinhole, calibration, image background, lock, frustum, split view`).

- [x] **8.2 — `pinhole_camera.py` (free orbit + frustum)**
  - Same synthetic world/camera, but no lock and no background image: left pane
    uses `pinhole_camera(...)` free, right pane default camera + frustum.
  - Docstring + `Keywords:`.

- [x] **8.3 — generated docs**
  - Follow `dev/workflows/example-docs.md`; add both to `docs/py/examples/index.md`.

## Validation

`uv run pytest py/tests/test_jupyter_examples.py -q && uv run mkdocs build --strict`

## Notes

- Keep the left pane sized to the image aspect so the overlay aligns (note the
  stretch/letterbox caveat in the docstring).
- These examples are the primary manual smoke test for the whole feature.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
