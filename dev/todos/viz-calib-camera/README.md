# Viz Calibrated Camera View — Overview

**Created:** 2026-09-21 | **Status:** Done | **Branch:** `feat/calib-cam-view`

## Goal

Let a user set up a Tanga scene pane from a real camera's **internal** (`K`)
and **external** (`R`, `t`) calibration, so 3D objects project through that
camera realistically. Independent, composable features:

1. `pinhole_camera(K, R, t, ...)` — a pure factory that turns calibration data
   into the existing `CameraConfig3d` (pose + `fov` + optional `intrinsics`).
   The camera stays fully orbitable/pan-able/zoom-able by default.
2. **Lock** — `SceneView(lock={"rotate", "pan", "zoom"})` fixes parts of a
   pane's camera (per-pane, so one pane can be locked while another stays free).
3. **Image background** — `SceneView(background_image=ImageData(...))` draws the
   camera image as an NDC background quad behind the 3D scene in one pane.
4. **Frustum** — a visualization-only geometry entity (`Frustum`) with
   `Frustum.from_camera(camera)` and a `FrustumStyle`, drawn in an overview pane.
5. **Per-pane visibility** — `SceneView(hide=...)` shows scene objects (e.g. the
   frustum) only in selected panes of a shared scene.

Used together (locked camera + background image), the camera pane becomes a
pixel-accurate overlay: world objects drawn on top land exactly on the image
pixels. The example shows a shared scene in two panes — a locked camera view
with the image on the left, and a free default-camera overview with the frustum
on the right.

## Architecture (short)

- **Camera** — extend `CameraConfig3d` with an optional `intrinsics` payload
  (no new `type`). When present the frontend sets an **off-center projection**
  (`Matrix4.makePerspective(left, right, top, bottom, near, far)`) because a
  symmetric `THREE.PerspectiveCamera` cannot express a principal-point offset
  `(cx, cy)`. When absent the existing symmetric `fov` path is unchanged.
- **Lock** — a per-pane `SceneView.lock` (a `set` of `CameraLock` strings)
  serialized in the `scene_view` node; the frontend translates it into disabled
  OrbitControls actions, composing with the existing scene-level `controls`
  mapping.
- **Image background** — a per-pane `SceneView.background_image` serialized as
  image metadata; pixel bytes travel on the existing binary frame transport
  (`_image_wire.py` / `Transport.send_bytes` / `image-frames.js`), and
  `ThreeJsView` mounts an NDC quad (screen-space, `depthTest/depthWrite=false`,
  `renderOrder=-1`) behind the WebGL content.
- **Frustum** — a new visualization-only geometry entity `Frustum` (no MV
  representation, like `Rectangle2D`) with `Frustum.from_camera(camera)` and a
  `FrustumStyle` (`fill` / plane `fill_opacity` / line `thickness`). It
  serializes to an explicit corner set (`kind: "Frustum"`) and is rendered by a
  new `renderers/frustum.js`.
- **Per-pane visibility** — `SceneView(hide=...)` / `SceneView(show=...)` filter
  which entities a pane builds. Each pane owns its own object registry, so hiding
  is per-pane with no scene duplication (the answer to "show some objects only in
  one view").

Both panes of the split view reference the **same scene** (`SceneView(name)`);
each pane is an independent `ThreeJsView` with its own `THREE.Scene`, camera,
controls, and object registry, so per-pane lock/image need no scene duplication
and no sync handlers.
## Canonical contract (fixed up front)

### `CameraConfig3d` gains `intrinsics`

```json
{
  "type": "3d",
  "position": [x, y, z], "target": [x, y, z], "up": [x, y, z],
  "fov": 50.0, "near": 0.1, "far": 100.0,
  "intrinsics": { "fx": 1000.0, "fy": 1000.0, "cx": 960.0, "cy": 540.0,
                  "width": 1920, "height": 1080 }
}
```

`intrinsics` is omitted when `None` (existing `to_dict` already omits `None`;
`PinholeIntrinsics.to_dict()` supplies the nested dict).

### `pinhole_camera(K, R, t, ...)`

OpenCV convention: `K` is 3×3, `R` world→camera (3×3), `t` world→camera (3),
so `u = fx·(X/Z)+cx`, `v = fy·(Y/Z)+cy` for `[X,Y,Z]ᵀ = R·Xw + t`. The factory
returns `CameraConfig3d` with:

- `fx,fy,cx,cy = K[0,0],K[1,1],K[0,2],K[1,2]`; `W,H = image_size`
- `fov = 2·atan((H/2)/fy)` (vertical, degrees)
- `position = -Rᵀ·t`; `target = position + Rᵀ·[0,0,1]`; `up = Rᵀ·[0,-1,0]`
- `intrinsics = PinholeIntrinsics(fx,fy,cx,cy,W,H)` when `include_intrinsics=True`

### `CameraLock` + `SceneView.lock`

- `CameraLock(StrEnum)`: `ROTATE="rotate"`, `PAN="pan"`, `ZOOM="zoom"`.
- `SceneView(lock: set[str] | None = None)`; each value validated via
  `CameraLock(value)` (raise `ValueError` otherwise). Serialized sorted:
  `"lock": ["pan", "rotate", "zoom"]` (omitted when empty).

### `SceneView.background_image`

Serialized in the `scene_view` node:

```json
"background_image": { "id": "...", "width": 1920, "height": 1080,
                      "channels": 3, "dtype": 0, "source": "data" }
```

### `SceneView.hide` / `SceneView.show`

```json
"hide": ["<entity-id>", ...], "show": ["<entity-id>", ...]
```

Per-pane entity visibility filter: `hide` removes matching ids from this pane
only; `show` (whitelist) shows only those ids. Both omitted by default.

### `Frustum` (geometry entity, no MV)

`py/pytanga/geometry/entities/frustum.py`, frozen dataclass, viz-only (cannot be
passed to `pytanga.geometry.create` / `analyze`, like `Rectangle2D`):

- `Frustum(near, far)` — each end is a `Point` (apex) or a `Rectangle2D`, or a
  4-corner sequence of `Point`s.
- `Frustum.from_camera(camera, *, near=None, far=None)` classmethod (lazy
  `CameraConfig3d` import; reads `position`/`target`/`up`/`fov`/`intrinsics`;
  `near <= 0` yields the apex form).
- Serializes to `kind: "Frustum"`:

```json
{
  "kind": "Frustum",
  "apex": false,
  "near": [[x,y,z], [x,y,z], [x,y,z], [x,y,z]],
  "far":  [[x,y,z], [x,y,z], [x,y,z], [x,y,z]]
}
```

The renderer always draws 4 lines from the near corners (or the apex) to the far
corners plus the end-plane outlines; `fill=True` adds translucent end/side faces.

### `FrustumStyle`

```json
{ "style_type": "FrustumStyle", "color": "#ffffff", "opacity": 1.0,
  "fill": false, "fill_opacity": null, "thickness": null }
```

- `fill: bool = False` — fill the frustum faces vs. draw planes + corner lines.
- `fill_opacity: float | None` — opacity of the filled planes/faces.
- `thickness: float | None` — line thickness for outlines / corner lines.

### Frontend pure math

- `templates/pinhole-projection.js` — `pinholeFrustum(fx, fy, cx, cy, width,
  height, near, far)` → `{left, right, top, bottom, near, far}` (pure, no
  `three`/DOM), Node-testable like `camera-fit.js`. Frustum bounds:
  `left=-cx·near/fx`, `right=(W-cx)·near/fx`, `top=cy·near/fy`,
  `bottom=-(H-cy)·near/fy` (signs pinned by the Node test projecting a known
  point to a known pixel).

## Decisions (confirmed)

- Distortion-free pinhole only (no radial/tangential terms).
- NDC background quad (not a DOM `<img>` and not `scene.background`).
- One camera config + a factory — no new camera `type`; intrinsics is an
  optional field on `CameraConfig3d`.
- Lock and image background are **independent** per-pane `SceneView` features;
  they do not live on the camera config.
- Lock uses a `set[str]` (`{"rotate","pan","zoom"}`) validated against
  `CameraLock`; default empty = free camera.
- Split-view export (multi-pane) is out of scope; static single-scene export
  keeps the symmetric `fov` path and ignores `intrinsics`.
- `Frustum` is a **visualization-only** geometry entity (no multivector, not
  analyzable); `Frustum.from_camera(camera)` builds it from a `CameraConfig3d`.
- Per-pane object visibility uses `SceneView.hide` / `SceneView.show` — not two
  scenes kept in sync by handlers.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-camera-model-pinhole-factory.md](./01-camera-model-pinhole-factory.md) | `PinholeIntrinsics`, `CameraConfig3d.intrinsics`, `pinhole_camera()`, `CameraLock` |
| 2 | [02-pinhole-projection-frontend.md](./02-pinhole-projection-frontend.md) | `pinhole-projection.js` + off-center projection + resize guard |
| 3 | [03-camera-lock.md](./03-camera-lock.md) | `SceneView.lock` per-pane serialization + frontend controls disable |
| 4 | [04-image-background.md](./04-image-background.md) | `SceneView.background_image` + NDC background quad renderer |
| 5 | [05-frustum-entity.md](./05-frustum-entity.md) | `Frustum` geometry entity + `Frustum.from_camera()` + `FrustumStyle` |
| 6 | [06-frustum-serializer-renderer.md](./06-frustum-serializer-renderer.md) | `Frustum` serializer + `_resolve` passthrough + `frustum.js` renderer |
| 7 | [07-pane-visibility-filter.md](./07-pane-visibility-filter.md) | `SceneView.hide` / `SceneView.show` per-pane entity filter |
| 8 | [08-examples.md](./08-examples.md) | Example: camera image left / default 3D + frustum right |
| 9 | [09-docs-changelog.md](./09-docs-changelog.md) | Architecture + public docs + changelog + PR |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz -q` (targeted files per phase).
- **JS pure modules:** Node `--input-type=module -e` harness (mirror
  `py/tests/viz/test_camera_fit_math.py`); `node --check` for syntax.
- **Bundle:** `uv run python tools/build-viewer-js.py --check` (keeps the
  committed `js/tanga-viewer.js` fresh for `delivery="cdn"`).
- **Docs:** `uv run mkdocs build --strict`.

## Non-goals

- Lens distortion correction.
- Per-scene (non-per-pane) lock; scene-level `controls` already exists.
- Split-view / per-pane camera or image in static HTML export (single-scene
  export only; it keeps the symmetric `fov` path).
- `Frustum` live-update on camera edit (a one-shot entity; callers re-add via
  `Frustum.from_camera(...)`).
- `Frustum` is not interactive (no `ActPoint` handles) and not analyzable.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
