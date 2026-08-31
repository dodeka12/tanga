# Phase 06c — Entity/operator → SDF-object mapping per draw style

**Status:** Done

## Goal

Give **every** geometry entity and operator an associated SDF object (basic or
composed), mirroring the standard viewer's per-kind dispatch. Previously only
six entities were supported and every operator raised `TypeError`.

## Mapping

| Kind | SDF object |
|------|------------|
| `Point` (PointStyle) | sphere (`size`) |
| `Point` (CrossHairPointStyle) | **composed**: 3-axis crosshair (3 thin boxes) |
| `HPoint` | sphere (`size`) |
| `Direction` / `HDirection` | **composed**: arrow (cylinder shaft + cone tip) |
| `PointPair` / `ImagPointPair` | **composed**: 2 spheres + connecting segment |
| `Line` (finite) | capped cylinder (`thickness`) |
| `Line` (infinite) | `intersect(cappedCylinder, bound)` |
| `Plane` | bounded slab (box) |
| `Circle` / `ImagCircle` | torus (`tubeRadius`) |
| `Sphere` / `ImagSphere` | sphere (`radius`) |
| `Space` | box (bounded volume, `extent`) |
| `ReflectionLine` | capped cylinder |
| `ReflectionPlane` | bounded slab |
| `ReflectionPoint` | sphere |
| `Inversion` | sphere (`radius`) |
| `Rotor` | **composed**: sector disc (filled to angle) + full rim ring + axis arrow |
| `Translator` | **composed**: arrow |
| `Dilator` | **composed**: concentric torus rings |
| `Motor` | **composed**: rotor disc + translator arrow |
| `GeneralRotor` | **composed**: sector disc + full rim ring + axis arrow at `origin` |

`TripleReflection` and `VersorFactors` remain deferred (`TypeError`).

## Style resolution

The serializer now resolves the effective draw style and reads parameters from
the **merged style** (user override > canonical > builtin) via `_param`, so
e.g. `style=CrossHairPointStyle(size=…)` is honoured. `SdfVisualizer.add` gained
a `style=` parameter.

`wireframe` is **not** honoured by the SDF path: a true wireframe cage is a 1D
structure the ray-marcher cannot express as a solid, so `SphereStyle`'s
`wireframe=True` default is ignored and spheres stay filled (the confirmed
vertical-slice behaviour). A thin-shell approximation is a future option.

## Files

- Modify: `py/pytanga/viz/sdf/serializer.py` (dispatch + per-kind/operator
  builders + `_param`/`_style_type` + `_tube`/`_disc_node`/`_arrow_node`)
- Modify: `py/pytanga/viz/sdf/visualizer.py` (`style=` parameter)

## Unit tests

- `py/tests/viz/sdf/test_sdf_serializer.py`: `test_serialize_space_box`,
  `test_serialize_direction_arrow`, `test_serialize_crosshair_point`,
  `test_operator_mapping`, and updated `test_unsupported_kind_raises`.

## Verification

- [x] `uv run pytest py/tests/viz/sdf` passes (51 tests).
- [x] `uv run pytest py/tests/viz` passes (511 tests).
- [x] `uv run ruff check` clean on the changed files.
