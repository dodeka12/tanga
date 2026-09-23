# Viz Camera View — Cleanup Overview

**Created:** 2026-09-21 | **Status:** Done | **Branch:** `feat/calib-cam-view`

## Goal

Refactor the calibrated-camera feature (currently scattered across
`CameraConfig3d.intrinsics`, `SceneView.lock`, `SceneView.background_image`, and
ad-hoc aspect/fit handling) into a clean three-layer model:

1. **Camera (data)** — a first-class `PinholeCamera` config (`type: "pinhole"`)
   carrying intrinsics + pose + a `fit` aspect policy.
2. **Camera view (presentation)** — a `CameraView` descriptor bundling a camera,
   a `lock` set, and an optional `background_image`.
3. **Pane (layout)** — `SceneView(scene, camera_view=...)` plus per-pane
   `hide`/`show` (unchanged).

This removes the accumulated workarounds: the `intrinsics` bolt-on, the
`userData._pinhole` resize flag, the `_applyCamera` projection clobber, and the
separate aspect/fit logic for the projection vs the background image.

## Architecture (short)

- **`PinholeCamera`** — `type: "pinhole"`, fields `fx, fy, cx, cy, width,
  height`, pose (`position`/`target`/`up`), `near`/`far`, and
  `fit: "fit" | "fill"` (default `"fit"` = contain/letterbox). `pinhole_camera()`
  returns it; `CameraConfig3d.intrinsics` is removed.
- **`pinhole-framing.js`** — a single pure module (replaces
  `pinhole-projection.js`) that maps `(fx, fy, cx, cy, W, H, near, far,
  paneAspect, fit)` to both the off-center frustum bounds and the background
  quad's letterbox half-extents `{hx, hy}`. One source of truth for aspect, so
  the projection and the image can never diverge.
- **Frontend** — `switchToCamera` gains a clean `type === "pinhole"` branch and
  a single `applyPinhole(camera, aspect)` used by both switch and resize. The
  redundant re-application block in `ThreeJsView._applyCamera` (which clobbered
  the off-center matrix) is deleted.
- **`CameraView`** — a plain descriptor `{camera, lock, background_image}`,
  serialized in the `scene_view` node as `camera_view`; the existing
  `ThreeJsView.setCamera`/`setLock`/`setBackgroundImage` methods stay and are
  fed from it. `SceneView.lock` / `SceneView.background_image` are removed.
- **Frustum** — `Frustum.from_camera` accepts a `PinholeCamera` (reads
  `fx/fy/cx/cy` directly) as well as a symmetric `CameraConfig3d`.

## Canonical contract (fixed up front)

### `PinholeCamera` (type `"pinhole"`)

```json
{
  "type": "pinhole",
  "fx": 500.0, "fy": 500.0, "cx": 320.0, "cy": 240.0,
  "width": 640, "height": 480,
  "position": [0, 0, -6], "target": [0, 0, 0], "up": [0, -1, 0],
  "near": 0.1, "far": 100.0,
  "fit": "fit"
}
```

`PinholeCamera` is a **sibling** of `CameraConfig2d` / `CameraConfig3d` (all
subclass the `CameraConfig` base), **not** a subclass of `CameraConfig3d`. The
camera hierarchy is:

```
CameraConfig      (base: type, position, target, up, near, far)
├── CameraConfig2d   type "2d"       orthographic (rectangle + stretch)
├── CameraConfig3d   type "3d"       perspective, symmetric fov
└── PinholeCamera    type "pinhole"  perspective, off-center (fx/fy/cx/cy/W/H) + fit
```

`CameraConfig3d` stays as the general symmetric-perspective camera (`View3dConfig`
→ `get_camera_view3d`, and plain `CameraConfig3d(position, target, fov)`); it has
no intrinsic principal point. `PinholeCamera` is the calibrated camera, produced
by `pinhole_camera(K, R, t, …)`. The frontend already dispatches on `type`, so
`"pinhole"` is one more case beside `"2d"`/`"3d"` — the same single system.

### `pinholeFraming(...)`

`pinholeFraming(fx, fy, cx, cy, width, height, near, far, paneAspect, fit)`
returns `{ left, right, top, bottom, hx, hy }` where the frustum bounds feed
`Matrix4.makePerspective(...)` and `{hx, hy}` are the image's NDC half-extents
for the background quad letterbox (`hx = min(1, A/a)`, `hy = min(1, a/A)` with
`A = W/H`, `a = paneAspect`; `fit === "fill"` → `hx = hy = 1`).

### `CameraView` (presentation descriptor)

```python
@dataclass
class CameraView:
    camera: CameraConfig | PinholeCamera
    lock: set[str] | None = None            # CameraLock values
    background_image: ImageData | None = None
```

Serialized in the `scene_view` node:

```json
"camera_view": {
  "camera": { ... },
  "lock": ["pan", "rotate", "zoom"],
  "background_image": { "id": "...", "width": 640, "height": 480,
                        "channels": 3, "dtype": 0, "source": "data" }
}
```

## Decisions (confirmed)

- Remove `CameraConfig3d.intrinsics`; move intrinsics to `PinholeCamera`.
- `fit` lives on the camera (mirrors `View2DConfig.stretch`), default `"fit"`.
- `CameraView` is a plain dataclass (not a `View`); `SceneView(camera_view=…)`.
- `SceneView.hide` / `SceneView.show` stay on `SceneView` (they are layout, not
  camera, concerns).
- Clean break (the feature is unreleased on this branch) — no deprecated
  kwargs are kept.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-pinhole-camera-config.md](./01-pinhole-camera-config.md) | `PinholeCamera` config + `fit` + `pinhole_camera` factory + `Frustum.from_camera` |
| 2 | [02-pinhole-framing-math.md](./02-pinhole-framing-math.md) | `pinhole-framing.js` (frustum + letterbox) + Node tests |
| 3 | [03-frontend-pinhole-branch.md](./03-frontend-pinhole-branch.md) | `switchToCamera` `"pinhole"` branch + `applyPinhole` + delete `_applyCamera` clobber |
| 4 | [04-background-letterbox.md](./04-background-letterbox.md) | letterbox the NDC background quad from `{hx, hy}` + resize update |
| 5 | [05-camera-view-descriptor.md](./05-camera-view-descriptor.md) | `CameraView` + `SceneView(camera_view=…)` + remove scattered kwargs |
| 6 | [06-examples-tests.md](./06-examples-tests.md) | fix examples (origin-centred) + docs + tests |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | architecture + public docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz -q` / `py/tests/geometry/test_frustum.py`.
- **JS pure:** Node harness (mirror `py/tests/viz/test_pinhole_math.py`); `node --check`.
- **Bundle:** `uv run python tools/build-viewer-js.py --check`.
- **Docs:** `uv run mkdocs build --strict`.

## Non-goals

- Lens-distortion correction.
- Per-scene (non-per-pane) lock.
- A dedicated `CameraView` *layout* `View` (it stays a serialized descriptor).
- Live-updating the frustum when the camera changes.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
