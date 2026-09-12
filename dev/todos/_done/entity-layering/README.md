# Entity module layering + Vec3 — Overview

**Created:** 2026-09-12 | **Status:** Done | **Branch:** `refactor/entity-layering`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Re-layer the `geometry` / `quadric` package graph into a strict DAG by:

1. introducing a leaf `pytanga.entity` module that owns the fundamental vector
   types — a new `Vec3` plus `Point` and `Direction` — together with the
   `Refinable` protocol and the MV-conversion registry;
2. moving `Conic` / `Quadric3D` (and their kind enums + classification) out of
   `geometry.entities` into `pytanga.quadric`;
3. turning refinement from a module-level `isinstance` dispatch into a
   `Refinable` `refine()` method on `Conic`/`Quadric3D` plus a duck-typed
   `pytanga.geometry.refine` dispatcher.

The result is `pytanga.entity` → `pytanga.quadric` → `pytanga.geometry` →
`pytanga.viz`, with no import-time cycle and a single lazy import (of the
specific entities) inside the refine path.

## Architecture (short)

```
pytanga.entity          ← leaf: Vec3, Point(Vec3), Direction(Vec3), Refinable,
                          MV-conversion registry (register_analyzer/_convert_mv)
pytanga.quadric         ← from_coeffs/to_coeffs, Conic, Quadric3D (+ enums),
                          refine_conic/refine_quadric (lazy-imports geometry.entities)
pytanga.geometry.entities ← specific entities (Ellipse, Circle, …), re-exports
                          Point/Direction/Conic/Quadric3D, Entity Union alias
pytanga.geometry        ← analysis (registers analyzers), create, duck-typed refine
pytanga.viz             ← unchanged
```

The cycle that exists today — `quadric ↔ geometry.entities` via `Conic`'s
`Point`/`Direction` imports and `geometry.entities`' `Conic` re-export — is
broken by moving `Point`/`Direction` into the leaf `pytanga.entity`, which
`quadric` imports without touching `geometry.entities`.

## Decisions (confirmed)

- **`Vec3` is the fundamental math type.** `Point` and `Direction` subclass it
  and override only the typed operations (see phase 1), so their public
  behavior is byte-for-byte unchanged.
- **`Refinable` is a `@runtime_checkable` Protocol**, not a base-class `refine()`
  stub and not a `capabilities()` dict.  Only `Conic`/`Quadric3D` implement
  `refine()`; the dispatcher probes with `getattr(entity, "refine", None)`.
- **`Entity` stays a `Union` type alias** in `geometry.entities` (no base-class
  sweep over ~30 entity files).  A formal `Entity` base class is a non-goal.
- **Backward compat via re-export shims.** `pytanga.geometry.entities.{point,
  direction, conic}` and `pytanga.geometry.{Point, Direction, Conic, Quadric3D,
  EConicKind, EQuadricKind}` keep working unchanged.
- **`refine` / `refine_entity` move to `geometry.refine`** as duck-typed
  dispatchers; `quadric` keeps only `refine_conic` / `refine_quadric` (the
  math).  The lazy `_E()` import of `geometry.entities` stays inside
  `quadric.refine`.

### Vec3 contract (fixed up front)

```python
@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: Vec3) -> Vec3        # component-wise
    def __sub__(self, other: Vec3) -> Vec3        # component-wise
    def __neg__(self) -> Vec3
    def __mul__(self, other) -> Vec3              # scalar scaling OR element-wise
    def __rmul__(self, scalar) -> Vec3            # scalar scaling
    def __truediv__(self, scalar) -> Vec3
    def elem_mul(self, other: Vec3) -> Vec3       # element-wise (Hadamard) product
    def dot(self, other: Vec3) -> float           # Euclidean dot product
    def cross(self, other: Vec3) -> Vec3          # cross product
    def mag(self) -> float                        # sqrt(x² + y² + z²)
    def normalized(self) -> Vec3                  # raises ValueError on zero length
    def to_point(self) -> Point
    def to_direction(self) -> Direction
    @classmethod
    def from_point(cls, p: Point) -> Vec3
    @classmethod
    def from_direction(cls, d: Direction) -> Vec3
```

`__mul__` scales by a number; given a `Vec3` it returns the element-wise
(Hadamard) product — this is the "element-wise `*`" requirement.  `elem_mul`
is the explicit named spelling of the same operation.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-entity-leaf-vec3.md](./01-entity-leaf-vec3.md) | Create `pytanga.entity` (Vec3/Point/Direction/Refinable/registry) and re-home Point/Direction |
| 2 | [02-conic-quadric-to-quadric.md](./02-conic-quadric-to-quadric.md) | Move Conic/Quadric3D (+enums/classification) into `quadric` |
| 3 | [03-refine-method-dispatcher.md](./03-refine-method-dispatcher.md) | Make refine a `Refinable` method + duck-typed dispatcher |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Developer docs, changelog, full regression |

## Testing as you go

- Python geometry: `uv run pytest py/tests/geometry -q`
- Viz (depends on entities): `uv run pytest py/tests/viz -q`
- Quadric: `uv run pytest py/tests/quadric -q`
- Full suite: `uv run pytest -q`
- Import smoke:
  `uv run python -c "from pytanga.entity import Vec3, Point, Direction, Refinable; from pytanga.geometry import Point as P, Direction as D, Conic, Quadric3D, refine; from pytanga.quadric import Conic as C2, Quadric3D as Q2; assert P is Point and D is Direction and C2 is Conic and Q2 is Quadric3D; print('ok')"`

## Non-goals

- No formal `Entity` base class (the `Entity` Union alias stays).
- No change to `Point`/`Direction` public behavior (only their module home and
  shared math move into `Vec3`).
- No change to viz serialization/rendering beyond what the import moves require.
- No MV/algebra changes.
