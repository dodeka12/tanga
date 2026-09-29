# Calibrated Labeling — Overview

**Created:** 2026-09-29 | **Status:** Planned | **Branch:** `feat/calibrated-labeling`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make `pytanga.viz.labelme` coordinate-system-agnostic by introducing a small
pixel↔world `CoordinateMapper` protocol (a `PlanarMapper` default plus a
`CalibratedPlaneMapper` for pinhole-camera scenes), harden `LabelMeStore` against
real-world (sometimes malformed) labelme files, and ship a new example app that
labels a calibrated image — a calibrated `CameraView` on the left and a world
`SceneView` on the right, both rendering the **same** world scene.

## Architecture (short)

- `CoordinateMapper` (protocol: `to_world(u, v) -> Point`, `to_pixel(point) ->
  (u, v)`) lives in `py/pytanga/viz/camera.py` next to `CameraCalibration` —
  pure math, no labelme knowledge.
- `labelme.py` depends only on the protocol. `LabelMeStore(mapper=...)` threads it
  through every pixel↔world call site; the default `PlanarMapper` preserves
  today's `z=0` ("pixel == world XY") behavior, so it is non-breaking for existing
  callers that omit `mapper`.
- `LabelShape` becomes the single type for both the serialized labelme shape and
  the in-memory live shape (`act`/`style` back-references), so the example app's
  throwaway `LabeledShape` is removed.
- The new example app mirrors `py/examples/viz/camera/pinhole_calibrated.py`
  (bundled T-LESS calibration, calibrated view left + world view right) and adds
  an editable labelme overlay driven by `CalibratedPlaneMapper`.

## Decisions (confirmed)

- **`CoordinateMapper` + mappers live in `camera.py`** (not a new module),
  exported from `pytanga.viz`. `PlanarMapper` is the default; `CalibratedPlaneMapper`
  ports the cal-auto-labelling repo's `CameraPlane` math (pinhole ray ∩ plane ⟂
  optical axis at `depth`).
- **`LabelShape` unification** — fold the example's `LabeledShape`
  (`act`/`style`/`label`) into `LabelShape`; `points`/`shape_type` become optional
  (default empty) so the live in-memory form is representable. `style`/`act` are
  in-memory only (never serialized); `mask` **is** serialized/round-tripped.
- **Loader is breaking** — `load`/`loads` return `LabelMeLoadResult(document,
  errors)` and `add_shapes`/`iter_objects` return `(result, errors)`. Malformed
  shapes are skipped and reported, never crash and never silently drop. Documented
  as a "Breaking" change (labelme is new in 2.13, low blast radius).
- **Output fidelity** — `dumps`/`save` default to `indent=4`, a fixed key order,
  and no coordinate rounding; rounding becomes opt-in via
  `LabelMeStore(coordinate_precision=...)`.
- **Existing image labeler app stays on `ImageCanvas`** (only the `LabeledShape` →
  `LabelShape` refactor touches it). The calibrated-camera path is a *separate*
  example app, not a mode of `ImageLabeler`.
- **`ActPoint` drag mode** — `_act_from_shape` currently forces `DragMode.XY_PLANE`
  for points, which is wrong off the `z=0` plane; switch to `DragMode.VIEW_PLANE`
  (already the default for the other shapes).

## Contract (fixed)

```python
# py/pytanga/viz/camera.py — near CameraCalibration
class CoordinateMapper(Protocol):
    def to_world(self, u: float, v: float) -> Point: ...
    def to_pixel(self, point: Point) -> tuple[float, float]: ...

class PlanarMapper:                       # default — today's z=0 behavior
    def to_world(self, u, v) -> Point: return Point(u, v, 0.0)
    def to_pixel(self, point): return (point.x, point.y)

class CalibratedPlaneMapper:              # NEW — ports cal repo's CameraPlane
    def __init__(self, camera: CameraCalibration, depth: float) -> None: ...
    def to_world(self, u, v) -> Point: ...   # ray through (u,v) ∩ plane ⟂ optical axis at depth
    def to_pixel(self, point) -> tuple[float, float]: ...
```

```python
# py/pytanga/viz/labelme.py
@dataclass
class LabelShape:
    label: str
    points: list[tuple[float, float]] = field(default_factory=list)
    shape_type: str = ""
    group_id: int | None = None
    description: str | None = None            # preserve None vs "" (no coercion)
    flags: dict[str, Any] = field(default_factory=dict)
    mask: str | None = None                   # NEW — round-tripped verbatim
    style: ObjVizStyle | None = None          # NEW — in-memory, never serialized
    act: Any = field(default=None, repr=False, compare=False)  # NEW — in-memory, never serialized

@dataclass
class LabelMeLoadResult:
    document: LabelMeDocument
    errors: list[str]                         # e.g. "shape 3 ('rear_rim_low'): 'rectangle' needs at least 2 points, got 1"
```

- `LabelMeStore(*, allow_extensions=True, mapper: CoordinateMapper | None = None,
  coordinate_precision: int | None = None)`.
- `dumps`/`save`: `indent=4`, key order `version, flags, shapes, imagePath,
  imageData, imageHeight, imageWidth`, no coordinate rounding by default.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-coordinate-mapper.md](./01-coordinate-mapper.md) | `CoordinateMapper` protocol + `PlanarMapper`/`CalibratedPlaneMapper` |
| 2 | [02-label-shape-unify.md](./02-label-shape-unify.md) | `LabelShape` unification + `mask` fidelity; drop `LabeledShape` |
| 3 | [03-labelme-mapper.md](./03-labelme-mapper.md) | Thread `mapper` through `LabelMeStore` |
| 4 | [04-labelme-errors.md](./04-labelme-errors.md) | Error-collecting loader (`LabelMeLoadResult`) |
| 5 | [05-labelme-fidelity.md](./05-labelme-fidelity.md) | Output fidelity (no rounding, key order, `mask`) |
| 6 | [06-calibrated-labeling-example.md](./06-calibrated-labeling-example.md) | New calibrated labeling example app |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` (targeted per phase)
- `uv run ruff check .`
- `uv run ty check`
- `uv run python tools/generate-example-docs.py --check` (phases 6–7)
- `uv run mkdocs build --strict` (phase 7)

## Non-goals

- No change to `ImageLabeler`'s `ImageCanvas`-based behavior (beyond the
  `LabeledShape` → `LabelShape` refactor).
- No mesh/PLY importer; the example renders only shapes + frustum, like
  `pinhole_calibrated.py`.
- No runtime network/download; the example reuses bundled T-LESS data.
- No change to the frontend `pinhole-framing.js`/`CameraView` architecture —
  `CoordinateMapper` is a Python-side math seam only.
