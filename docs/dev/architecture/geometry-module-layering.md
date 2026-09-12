# Geometry / Quadric module layering

The `pytanga.geometry` and `pytanga.quadric` packages are layered into a strict
import DAG so fundamental primitives sit at the bottom and nothing imports "up"
into a cyclic dependency.

## The DAG

```
pytanga.entity           ← leaf: Vec3, Point(Vec3), Direction(Vec3), Refinable,
                           MV-conversion registry (register_analyzer/_convert_mv)
pytanga.quadric          ← from_coeffs/to_coeffs, Conic, Quadric3D (+ enums),
                           refine_conic/refine_quadric, entity→MV creation
                           incl. the Q2/Q3 rotation rotor (_create.py),
                           MV→entity analysis incl. rotor analysis
                           (_analysis.py), point recovery (_pointset.py),
                           quadric intersection (_intersection.py) —
                           all lazy-import geometry.entities
pytanga.geometry.entities ← specific entities (Ellipse, Circle, …), re-exports
                           Point/Direction/Conic/Quadric3D, Entity Union alias
pytanga.geometry         ← analysis (registers analyzers), create, duck-typed refine
pytanga.viz              ← unchanged
```

Each layer imports only the layers below it.  `pytanga.entity` imports nothing
from `pytanga.geometry` or `pytanga.quadric`.

## `Vec3` / `Point` / `Direction`

- `Vec3` (`pytanga.entity.vec3`) is the fundamental 3D vector: component-wise
  `+`/`-`, scalar and element-wise `*` (`elem_mul`), `dot`, `cross`, `mag`,
  `normalized`, and the conversions `to_point()` / `to_direction()` /
  `from_point()` / `from_direction()`.
- `Point(Vec3)` and `Direction(Vec3)` subclass `Vec3` and override the typed
  operations to return the semantically correct type (`Point - Point →
  Direction`, `cross()` → `Direction`, `normalized()` → `Point`/`Direction`).
  Their public behavior is unchanged from when they lived in `geometry.entities`.

## The `Refinable` protocol

`pytanga.entity.base.Refinable` is a `@runtime_checkable` `Protocol` with a
single `refine()` method.  `Conic` and `Quadric3D` (in `pytanga.quadric`)
implement it; `pytanga.geometry.refine` is a duck-typed dispatcher:

```python
def refine(entity):
    fn = getattr(entity, "refine", None)
    if not callable(fn):
        raise TypeError(f"{type(entity).__name__} is not refinable")
    return fn()
```

The actual quadric math stays in `pytanga.quadric` and imports
`geometry.entities` lazily (only when `refine()` / `create_entity()` /
`analyze_entity()` are actually called), so the `quadric ↔ geometry.entities`
cycle never fires at import time.

## MV-conversion registry

`pytanga.entity._util` owns the analyzer registry (`register_analyzer`,
`_convert_mv`, `_is_mv`, `_scalar`).  `pytanga.geometry.analysis` registers the
algebra-specific `analyze_<name>` callables at import time, so `Point(mv)` /
`Direction(mv)` can route an MV through the full analyzer without importing
`analysis` (which imports the entities) — no import-time cycle.

## Backward-compatibility shims

The canonical definitions moved, but the old import paths keep working via thin
re-export shims:

- `pytanga.geometry.entities.point` / `direction` / `conic` re-export from
  `pytanga.entity` / `pytanga.quadric`.
- `pytanga.geometry.Point`, `Direction`, `Conic`, `Quadric3D`, `EConicKind`,
  `EQuadricKind` re-export unchanged.
- `pytanga.geometry.refine` / `refine_entity` keep their public signatures.
- `pytanga.geometry.create_q2` / `create_q3`, `analysis_q2` / `analysis_q3`,
  and `_pointset` re-export from `pytanga.quadric._create`, `._analysis`, and
  `._pointset` respectively, so the creation/analysis dispatchers keep working.
- `analyze_operator` also routes `q2`/`q3` MVs to `quadric._analysis.analyze_operator`,
  which returns a `pytanga.geometry.operators.Rotor` (imported lazily inside the
  function to keep the `quadric → geometry` edge lazy).
