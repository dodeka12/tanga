# Viz: CameraConfig Restructure — Typed Base + 2D/3D Subclasses + View Builders

**Date:** 13 August 2026

**Status:** Implemented

## Goal

Replace the view-spec compositing currently embedded in `CameraConfig` with a
clean, typed separation:

- A `CameraConfig` **base class** carries only a discriminator `type` and the
  fields common to 2D and 3D cameras.
- `CameraConfig2d` and `CameraConfig3d` derive from it and carry their
  respective raw parameters.
- Free builder functions translate the higher-level `View2DConfig` /
  `ViewPlaneConfig` input specs into a fully-populated `CameraConfig2d` /
  `CameraConfig3d`.

The frontend consumes these raw parameters and derives the final camera
frustum using the live browser viewport, so the requested view is shown
correctly regardless of the requested extents and the browser window
aspect/size.

## New Module Layout

Camera / view config classes and their builder functions now live in a new
file, separate from `scene.py`:

- **`py/pytanga/viz/camera.py`** (new) — contains:
  - `CameraConfig` (base), `CameraConfig2d`, `CameraConfig3d`
  - `View2DConfig`, `ViewPlaneConfig` (input specs)
  - `get_camera_view2d`, `get_camera_view3d`, `get_camera`

- **`py/pytanga/viz/scene.py`** — imports and re-exports `CameraConfig` from
  `camera.py` for backward-compatible access (`SceneConfig.camera` still
  references it). `View2DConfig` / `ViewPlaneConfig` and the builder functions
  are no longer defined here.

- **`py/pytanga/viz/__init__.py`** — exports the new names from `camera.py`.

## Class Hierarchy

### `CameraConfig` (base)

```python
@dataclass(kw_only=True)
class CameraConfig:
    """Base camera config: a ``type`` discriminator + fields shared by 2D/3D."""

    type: str  # "2d" | "3d" — discriminator; set by the subclass

    # Shared transform / clipping
    position: tuple[float, float, float] | None = None
    target: tuple[float, float, float] | None = None
    up: tuple[float, float, float] | None = None
    near: float | None = None
    far: float | None = None

    def to_dict(self) -> dict:
        # {"type": self.type} + non-None shared fields; subclasses extend
```

### `CameraConfig2d(CameraConfig)`

Orthographic top-down camera. Carries the **visible world rectangle** plus the
2D aspect/scaling policy.

```python
@dataclass(kw_only=True)
class CameraConfig2d(CameraConfig):
    type: Literal["2d"] = "2d"

    # Final visible world rectangle (after border_world has been applied by
    # the builder; border_px is applied by the frontend).
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    # True  = preserve aspect ratio via letterboxing (uniform world scale)
    # False = stretch the rect to exactly fill the viewport (non-uniform scale)
    uniform: bool = True

    # Additional fixed border in pixels, applied by the frontend (needs the
    # live viewport size to convert px -> world units).
    border_px: float = 0.0
```

### `CameraConfig3d(CameraConfig)`

Perspective camera.

```python
@dataclass(kw_only=True)
class CameraConfig3d(CameraConfig):
    type: Literal["3d"] = "3d"

    fov: float = 50.0        # vertical field of view in degrees
    # position / target / up / near / far inherited from CameraConfig
```

**Notes on structure:**

- `kw_only=True` is used so required fields (e.g. `xmin`) may follow defaulted
  inherited fields without dataclass ordering errors, and `type` can be
  overridden with a subclass default.
- `to_dict()` is implemented generically on the base class by scanning the
  instance's dataclass fields, so subclasses do not need their own serializer.
  Each dict always includes `"type"`.
- `SceneConfig.camera` and `Visualizer.__init__(camera=...)` accept
  `CameraConfig | None` (the base type). The concrete instance determines the
  discriminated type.

## Input Specs — `View2DConfig` / `ViewPlaneConfig`

Input specs are what the user constructs; they are pure data and are **not**
serialized by `CameraConfig`.

### `View2DConfig` (changed)

Renamed fields to support graph-style views (min/max bounds, borders, and
stretch mode):

```python
@dataclass
class View2DConfig:
    """2D orthographic view defined by visible data bounds."""

    xmin: float
    xmax: float
    ymin: float
    ymax: float

    border_world: float = 0.0   # world-unit margin added on all four sides
    border_px: float = 0.0      # pixel margin added on all four sides (frontend)
    uniform: bool = True        # letterbox=True | stretch=False
```

This **replaces** the previous `extent_x` / `extent_y` / `center` fields.
`to_dict()` is removed (input specs are not serialized by `CameraConfig`).

### `ViewPlaneConfig` (unchanged)

```python
@dataclass
class ViewPlaneConfig:
    point: tuple[float, float, float]
    normal: tuple[float, float, float]
    extent_u: float
    extent_v: float
    center: tuple[float, float, float] | None = None
    span_u: tuple[float, float, float] | None = None
    fov: float = 50.0
```

## 2D Scaling Modes

Two supported modes, selected by `CameraConfig2d.uniform` (sourced from
`View2DConfig.uniform`):

### `uniform=True` (default) — undistorted, letterboxed

A single world-units-per-pixel scale is used so geometry is never distorted,
and the full requested rectangle is contained. With browser pixels `W × H`
(`aspect = W / H`), requested `xmin..xmax` / `ymin..ymax`
(`extent_x = xmax - xmin`, `extent_y = ymax - ymin`, `center` = rect center):

```
fit = max(extent_x / aspect, extent_y)    # visible full height, world units
visible_width  = fit * aspect   (≥ extent_x)
visible_height = fit            (≥ extent_y)
```

Example: extent `2×1`, window `100×100` (`aspect=1`) → `fit = 2`, so visible
width = 2, visible height = 2 (width 2 maps to 100 px).

### `uniform=False` — stretch-to-fill

The rectangle is mapped directly onto the viewport: `left=xmin`, `right=xmax`,
`top=ymax`, `bottom=ymin`. X and Y are scaled independently, so a long, thin
plot fills the window (axes intentionally non-uniform). This is the mode for
"just fill the browser view" plots.

## 2D Min/Max + Borders

- `border_world`: fixed world-unit margin added to all four sides. Applied in
  Python (deterministic, no viewport needed), producing the stored
  `xmin/xmax/ymin/ymax`.
- `border_px`: fixed pixel margin added to all sides. Conversion from px to
  world units depends on the live viewport, so it is stored as a field and
  applied by the frontend.

Frontend `border_px` algorithm (uniform mode): reduce the effective content
area to `(W - 2*border_px) × (H - 2*border_px)`, then perform the contain-fit
above on that reduced area. For the stretch mode, `border_px` has no additional
effect (the exact rect fills the viewport; `border_world` still applies).

## Backend — `py/pytanga/viz/camera.py`

### Builder functions

Each specific builder takes an instance of its matching input spec class.

```python
def get_camera_view2d(config: View2DConfig) -> CameraConfig2d:
    """Build an orthographic 2D camera from a :class:`View2DConfig`."""

def get_camera_view3d(config: ViewPlaneConfig) -> CameraConfig3d:
    """Build a perspective 3D camera from a :class:`ViewPlaneConfig`."""

def get_camera(
    view_config: View2DConfig | ViewPlaneConfig,
) -> CameraConfig:
    """Dispatch on view config type to build the matching CameraConfig."""
```

### Behavior

- `get_camera_view2d` applies `border_world` to produce the stored rectangle,
  derives the rect center `(cx, cy)`, sets `position = (cx, cy, 20)` and
  `target = (cx, cy, 0)`, and copies `uniform` and `border_px` through.
- `get_camera_view3d` replicates the current `view_mode.js` plane geometry:
  normalize `normal`, resolve `center` (default `point`), orthogonalize
  `span_u` (auto-derived when absent), build `v̂ = n̂ × û`, compute `distance`
  from `fov`/`extent_u`/`extent_v`, and set `position = center + n̂·distance`,
  `target = center`, `up = v̂`, plus `near`/`far` from `distance`. The plane
  distance is computed with a documented default aspect ratio (the same
  aspect the glTF exporter already assumes); exact cross-aspect 3D refit can
  be revisited later.
- `get_camera` dispatches: `View2DConfig` → `get_camera_view2d`, and
  `ViewPlaneConfig` → `get_camera_view3d`.

## Frontend — `py/pytanga/viz/templates/viewer.js` + `view_mode.js`

### `switchToCamera()`

Rewrite the dispatch to read `camera.type` instead of `view_2d` / `view_plane`:

- `type === "2d"` (orthographic):
  - switch to `THREE.OrthographicCamera` if needed,
  - if `xmin/xmax/ymin/ymax` present:
    - `uniform=true`: contain-fit via `fit = max(extent_x / aspect, extent_y)`,
      account for `border_px` by shrinking the effective content area,
      derive frustum from `fit`/`aspect` centered on the rect center,
    - `uniform=false`: set `left=xmin, right=xmax, top=ymax, bottom=ymin`,
  - set `near`/`far` from config,
  - preserve per-resize extents in `camera.userData._view2d` for `handleResize`,
  - `position`/`target` from config (builder already set them).
- `type === "3d"` (perspective):
  - switch to `THREE.PerspectiveCamera` if needed,
  - apply `fov`, `aspect`, `near`, `far`,
  - apply `up` if present, then `position`/`target`,
- Keep the default-2D branch for `spaceDim === 2` with no explicit config.

### `handleResize()`

Already reads `camera.userData._view2d` — verify it still works; for
`uniform=false`, resize should re-stretch rather than preserve extents.

## glTF Export — `py/pytanga/viz/export/_gltf.py`

`add_camera()` currently reads `fov`, `near`, `far`, `position`, `target`.
Update to dispatch on `type`:

- `CameraConfig2d` → glTF orthographic camera (`xmag`/`ymag` from the rect,
  translation from `position`/`center`).
- `CameraConfig3d` → glTF perspective camera (existing `fov`/`near`/`far`/
  `position`/`target` logic; add `up` handling if needed).

## Exports — `py/pytanga/viz/__init__.py` and `scene.py`

- **`camera.py`** is the canonical definition site.
- **`scene.py`** re-imports `CameraConfig` from `camera.py` so the existing
  `from pytanga.viz.scene import CameraConfig` import path keeps working.
- **`__init__.py`** exports `CameraConfig`, `CameraConfig2d`, `CameraConfig3d`,
  `View2DConfig`, `ViewPlaneConfig`, `get_camera`, `get_camera_view2d`,
  `get_camera_view3d`.

## Examples — `py/examples/viz/`

| File | Change |
|------|--------|
| `demo_camera_config.py` | Replace `view_2d=` / `view_plane=` with `get_camera(...)` / `get_camera_view2d(...)` / `get_camera_view3d(...)`. |
| `demo_camera_2d.py` | Use `get_camera_view2d(...)` (or `get_camera(...)`); update `View2DConfig` to `xmin/xmax/ymin/ymax` + borders. |
| `demo_camera_3d_plane.py` | Use `get_camera_view3d(...)` (or `get_camera(...)`). |
| `demo_camera_axes_grid_2d.py` | Use `get_camera_view2d(...)`; update `View2DConfig`. |

Add (or extend) a 2D example demonstrating stretch mode (`uniform=False`) and
`border_world` / `border_px`.

## Tests — `py/tests/viz/test_scene_session.py`

- Remove `test_to_dict_includes_view_2d` and `test_to_dict_includes_view_plane`.
- Update `View2DConfig` construction for new fields (`xmin/xmax/ymin/ymax`).
- Add tests for the new schema:
  - `CameraConfig2d(...)` / `CameraConfig3d(...)` carry the correct `type`.
  - `to_dict()` emits `"type"`, omits `None` shared fields, and includes the
    subclass-specific fields (no nested `view_2d`/`view_plane`).
- Add tests for builders:
  - `get_camera_view2d(View2DConfig(...))` returns `CameraConfig2d` with
    correct `xmin/xmax/ymin/ymax` (incl. `border_world`), `uniform`,
    `border_px`, `position`, `target`.
  - `get_camera_view3d(ViewPlaneConfig(...))` returns `CameraConfig3d` with
    computed `position`/`target`/`up`.
  - `get_camera(View2DConfig(...))` → `CameraConfig2d`;
    `get_camera(ViewPlaneConfig(...))` → `CameraConfig3d`.

## Docs — `docs/py/viz/camera.md`

- Document the typed hierarchy (`CameraConfig` base, `CameraConfig2d`,
  `CameraConfig3d`).
- Document `View2DConfig` `xmin/xmax/ymin/ymax` + `border_world` / `border_px`
  / `uniform`.
- Replace `view_2d=` / `view_plane=` examples with `get_camera(...)`,
  `get_camera_view2d(...)`, `get_camera_view3d(...)`.
- Document `uniform` (letterbox vs stretch) and `border_world` / `border_px`
  for graph-like 2D views.

## Implementation Order

- [x] 1. **`py/pytanga/viz/camera.py`** (new) — base + subclasses + builders +
  input specs.
- [x] 2. **`py/pytanga/viz/scene.py`** — remove camera/view config definitions;
  re-import `CameraConfig` from `camera.py`.
- [x] 3. **`py/pytanga/viz/__init__.py`** — export new types/functions.
- [x] 4. **`py/pytanga/viz/templates/view_mode.js`** — rewrite `switchToCamera()`.
- [x] 5. **`py/pytanga/viz/export/_gltf.py`** — update `add_camera()`.
- [x] 6. **`py/examples/viz/`** — update the camera demos.
- [x] 7. **`py/tests/viz/test_scene_session.py`** — update/add tests.
- [x] 8. **`docs/py/viz/camera.md`** — update documentation.
- [x] 9. Run test suite.

## Open Questions / Assumptions

- `border_px` is applied by the frontend only in `uniform=True` mode; in
  stretch mode the exact rect fills the viewport with no additional pixel
  border. Confirm this is the intended behavior.
- The 3D plane `distance` is computed with a default aspect ratio; exact
  cross-aspect 3D contain-fit is deferred. Confirm acceptable for now.
- Naming uses `CameraConfig2d` / `CameraConfig3d` as requested, departing from
  the `View2DConfig` capitalization convention.
- `scene.py` keeps a re-export of `CameraConfig` to avoid breaking the existing
  `from pytanga.viz.scene import CameraConfig` import in tests and elsewhere.