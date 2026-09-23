# Phase 1 — Move `Transform` + transform math into `pytanga.geometry`

## Goal

Relocate `Transform` (from `viz/_nodes.py`), the pure transform math (from
`viz/_transforms.py`), and the transform coercion helpers/types (from
`viz/_types.py`) into `pytanga.geometry` — a **behavior-identical** move so later
phases change the representation in one place. `viz` keeps thin re-export shims.

## Files

- New: `py/pytanga/geometry/transforms.py` (pure math, moved from
  `viz/_transforms.py` — imports only `numpy` + geometry)
- New: `py/pytanga/geometry/transform.py` (`Transform` + coercers + type aliases)
- Edit: `py/pytanga/geometry/__init__.py` (export `Transform`)
- Edit: `py/pytanga/viz/_transforms.py` (re-export shim)
- Edit: `py/pytanga/viz/_nodes.py` (import + re-export `Transform`)
- Edit: `py/pytanga/viz/_types.py` (import + re-export moved coercers/aliases)
- Edit: `py/pytanga/viz/__init__.py` (import `Transform` from geometry)

## Steps

- [x] **1.1 — move the pure math to `geometry/transforms.py`**
  - Move `viz/_transforms.py` verbatim to `py/pytanga/geometry/transforms.py`
    (it imports only `numpy`, `geometry.entities.Direction/Point`,
    `geometry.operators.*`), updating its docstring. Keep `_EPS = 1e-12`.
  - `viz/_transforms.py` becomes a re-export shim
    (`from pytanga.geometry.transforms import *` plus its `__all__`) so
    `from pytanga.viz._transforms import operator_to_matrix` and
    `from . import _transforms as _T` keep working.

- [x] **1.2 — move `Transform` + coercers/types to `geometry/transform.py`**
  - Move `Transform` (`_nodes.py:116-237`) into `py/pytanga/geometry/transform.py`.
  - Move the transform coercers/types from `viz/_types.py`: `_as_vec3`,
    `_as_euler`, `Triple`, `TransformRotation`, `TransformOperator`,
    `TransformInput` (plus a local `Vec3`-like alias for annotations).
    `Transform` imports the math from `geometry.transforms`; `_as_euler` uses
    `geometry.transforms.to_trs`/`rotation_matrix`.
  - `_coerce_transform_matrix` **stays in viz** (it accepts an `MV`); it now
    imports `Transform` from geometry.

- [x] **1.3 — rewire viz imports (back-compat)**
  - `viz/_nodes.py`: import `Transform` from `pytanga.geometry.transform`
    (re-export it); keep `_coerce_transform_matrix` local.
  - `viz/_types.py`: import/re-export `_as_vec3`/`_as_euler`/`Triple`/
    `TransformRotation`/`TransformOperator`/`TransformInput` from geometry; keep
    the viz-specific aliases (`VizInputType`, `SceneEntity`, `Rotation`, `Vec3`).
  - `viz/__init__.py`: import `Transform` from geometry (public
    `from pytanga.viz import Transform` unchanged).

- [x] **1.4 — export from geometry**
  - `py/pytanga/geometry/__init__.py`: add `from .transform import Transform`
    and append `"Transform"` to `__all__` (public
    `from pytanga.geometry import Transform`).

- [x] **1.5 — validate the move**
  - Run the transform/node/object-ref tests; no behavior change expected.

## Validation

`uv run pytest py/tests/viz/test_transforms.py py/tests/viz/test_nodes.py py/tests/viz/test_object_ref.py py/tests/viz/test_node_serialization.py py/tests/viz/test_scene_graph_e2e.py -q`

## Notes

- This phase changes only file location + imports; `Transform` still stores an
  Euler triple here. Phase 2 swaps the representation.
- Layering: this makes `geometry` self-contained (it must not import `viz`) and
  `viz` consumes `Transform`/the math from geometry — matching the DAG in
  `docs/dev/architecture/geometry-module-layering.md`.
- The `Vec3` name is overloaded (`pytanga.entity.vec3.Vec3` class vs the
  `viz/_types.py` union alias); `geometry/transform.py` should use its own local
  alias (or inline `Point | Direction | tuple`) to avoid a clash.
- `_coerce_transform_matrix` (MV-aware input normalization) is a viz concern and
  stays put; only the pure geometry part moves.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
