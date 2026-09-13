# Phase 5 — `pytanga/geometry`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Annotate `py/pytanga/geometry` (101 untyped functions) — the entity data classes,
operators, and the analysis/create/refine/random dispatchers.  This includes the
`Plane.__init__` type-hint fix that seeded this plan.

## Files

- Edit: `py/pytanga/geometry/entities/*.py` (all entity data classes)
- Edit: `py/pytanga/geometry/operators.py`
- Edit: `py/pytanga/geometry/analysis*.py`
- Edit: `py/pytanga/geometry/create*.py`
- Edit: `py/pytanga/geometry/refine.py`
- Edit: `py/pytanga/geometry/mask.py`
- Edit: `py/pytanga/geometry/random.py`
- Edit: `py/pytanga/geometry/_geometry.py`, `_pointset.py`, and helper modules

## Steps

- [x] **5.1 — `entities/plane.py` `Plane.__init__` (canonical example)**
  - Add `from typing import TYPE_CHECKING` and, after the local imports,
    `if TYPE_CHECKING: from pytanga.algebra._mv import MV`.
  - Annotate the constructor (behavior unchanged):
    ```python
    def __init__(
        self,
        point: Point | MV | None = None,
        normal: Direction | MV | None = None,
        span_u: Direction | MV | None = None,
        span_v: Direction | MV | None = None,
        extent: float | MV | None = None,
    ) -> None:
    ```
- [x] **5.2 — remaining `entities/*.py`** — annotate the `__init__` coercion
  constructors and helpers of `Line`, `Circle`, `Sphere`, `Cone`, `Cylinder`,
  `Disk`, `Ellipsoid`, `Hyperbola`, `Parabola`, `HDirection`, `HPoint`,
  `LinePair`, `PlanePair`, `PointPair`, `PointSet`, `Space`, `Arc`, `Box`,
  `Polygon`, `plane_conic`, using `Point | MV`, `Direction | MV`,
  `float | MV | None` (mirror 5.1) and the `_coerce.to_*` helpers.
- [x] **5.3 — `operators.py`** — `Rotor`, `Translator`, `Reflection*`, `Motor`,
  `Dilator`, `Inversion`, `GeneralRotor`, `TripleReflection` constructors and
  methods.
- [x] **5.4 — `analysis*.py`** — `analyze`, `analyze_entity`, `analyze_operator`,
  `analyze_plane`, `analyze_line`, `analyze_point`, `_detect`, `_typed`,
  `_expect` — `MV` / `Algebra` under `TYPE_CHECKING`.
- [x] **5.5 — `create*.py`** — `create`, `create_entity`, `create_operator`, the
  per-algebra `create_*` builders (`-> MV`).
- [x] **5.6 — `refine.py` / `mask.py` / `random.py` / `_geometry.py` /**
  `_pointset.py`** — `refine`, `mask_for`, `create_var`, `two_conic_intersection`,
  and the random generators (`-> MV`, `-> Point`, `-> Direction`).

- [x] **5.7 — Resolve `pytanga/geometry` ty diagnostics**
  - `uv run ty check py/pytanga/geometry` → 0 (baseline: 183 diagnostics).
  - Fix each (real bug / annotation inaccuracy) or add
    `# ty: ignore[<rule>]  # <reason>` for verified false positives.

## Validation

`uv run ruff check --select ANN --ignore ANN401 py/pytanga/geometry` → 0
`uv run ty check py/pytanga/geometry` → 0
`uv run pytest py/tests/geometry -q`

## Notes

- 5.1 is the reference pattern for every entity coercion constructor — the other
  entities copy it verbatim (adjusting the accepted `Point`/`Direction`/`float`
  types).
- Entities must stay runtime-independent of `pytanga.algebra`; `MV` is annotated
  via `TYPE_CHECKING` only (per `geometry-module-layering.md`).
- `analysis` / `create` modules already use `if TYPE_CHECKING:` for `MV` /
  `Algebra` — follow that existing style.
