# OPNS/IPNS on the Algebra — Overview

**Goal:** Move the OPNS/IPNS interpretation flag from per-call keyword arguments
(`opns=...` on most create/analyze functions and classes) onto the **algebra
itself**. Only the algebra carries the flag; every multivector can access it via
its algebra reference. Entity constructors (`Point(A)`, `Direction(A)`, `Line(A)`, …)
then use **specific, typed analyzers** to convert any multivector — raising a clear
exception when `A` has the wrong structure.

Three associated conveniences are part of the same rework:

- `Geometry.__call__` executes the facade's `create`, so
  ``geo = Geometry(BasisN3()); A = geo(Point(1, 2, 3))``.
- **Every entity constructor auto-converts multivector arguments** — not just the
  top-level entity, but each `Point`, `Direction`, or scalar field. For example
  ``Circle(A, B, C)`` works with `A` a point-MV, `B` a scalar-MV (radius), and
  `C` a direction-MV (normal). `Line.from_points(start, end)` and
  `PointPath.add(mv)` are special cases of the same rule.

**Non-goals / stated preferences:**

- **No backward compatibility.** All dependent code in `pytanga` (library,
  tests, examples, docs) is changed in the same series of phases.
- `algebra.opns` is **mutable** (settable at runtime).
- Per-entity conversion uses **explicit public analyzers** (`analyze_point`,
  `analyze_direction`, `analyze_line`, …), not a generic `analyze_entity` + `isinstance`.
- The old **E3 vector convenience** remains: `Point(mv)` / `Direction(mv)` on a
  plain grade-1 Euclidean vector still extracts x/y/z directly.
- `create_*` functions use the **algebra's setting** (`basis.opns`); they no
  longer accept an override flag.

---

## Current State (why this is painful)

- `Algebra` has no `opns`; the flag is threaded per call through:
  - `geometry/create.py` → 8 `create_*` modules (`e2/e3/p2/p3/pga2/pga3/n2/n3`).
  - `geometry/analysis.py` → 8 `analysis_*` modules.
  - `geometry/_geometry.py` → `Geometry` stores its own `opns` + per-call override.
  - `viz/visualizer.py`, `viz/_scene_handle.py`, `viz/_app.py` → `_opns` state +
    per-call `opns` params.
- `geometry/entities.py` `Point.__init__`/`Direction.__init__` special-case an MV
  via `hasattr(x, "_alg")` and read **raw E3 blade ids** `mv[1]/mv[2]/mv[4]`. This
  only works for an E3 grade-1 vector and is wrong for P3/N3/PGA3 points/directions.

---

## Target Architecture

```
Algebra.opns  (mutable bool, default True)
      ▲ delegated by
MV.opns ──────┘
      │
      ├─ analysis_*.analyze_point(mv)   ← reads mv.algebra.opns, dualizes if IPNS,
      │                                    calls internal decomposer, asserts type
      ├─ analysis_*.analyze_direction(mv)
      ├─ analysis_*.analyze_line(mv)
      ├─ … (plane / circle / sphere / point_pair / hpoint / hdirection / space)
      │
      ├─ entities.Point(mv)            ← calls the typed analyzer (+ E3 vector shortcut)
      ├─ entities.Direction(mv)
      └─ entities.Line(mv) / Plane(mv) / Circle(mv) / Sphere(mv) / …

create_*.create_point(basis, x, y, z)   ← reads basis.opns (no override)
create_entity(basis, entity)            ← dispatches to create_* (no override)

Geometry.__call__(obj)                  ← == Geometry.create(obj)
```

Every object that consumes base geometry instances (`Point`, `Direction`) or scalar
components auto-converts multivector arguments through the typed entity constructors
and a scalar-MV extractor (`float(mv.scalar)`), raising on mismatch.

The generic `analyze_entity(mv)` / `analyze(mv)` remain but **stop taking an
`opns` argument** — they read `mv.algebra.opns`. They remain the "what is this?"
entry points used by the visualizer.

---

## Phases

| Phase | File | Summary |
|-------|------|---------|
| **1** | `phase1-algebra-flag.md` | Mutable `opns` on `Algebra` + `MV.opns`; basis classes forward it |
| **2** | `phase2-typed-analyzers.md` | Explicit per-entity analyzers in all `analysis_*` modules |
| **3** | `phase3-entity-constructors.md` | `Point(A)/Direction(A)/Line(A)/…` accept MVs via typed analyzers; field-level auto-conversion; `Line.from_points` |
| **4** | `phase4-remove-basis-geometry.md` | Remove `point/direction/line/plane/vector/rotor` methods from `Basis*` (geometry only via the `geometry` submodule) |
| **5** | `phase5-analysis-reads-flag.md` | `analyze_entity`/`analyze` drop `opns`; `Geometry.which_entity/analyze` and `viz`/`PointPath.add` follow |
| **6** | `phase6-creation-reads-flag.md` | `create_*`/`create_entity` drop `opns`; `Geometry.create` follows; add `Geometry.__call__` |
| **7** | `phase7-examples.md` | Update all example scripts to the new API |
| **8** | `phase8-docs.md` | Update documentation (final step) |

Tests are **adapted within each phase** (not all at the end): each phase lists
the test files it adds or updates so the suite stays green at every step.

---

## Ordering Rationale (no later phase refactors earlier work)

1. **Phase 1** is purely additive (algebra/MV/basis gain `opns`; nothing existing is removed).
2. **Phase 2** is purely additive (new typed analyzers read `mv.algebra.opns`).
3. **Phase 3** consumes Phase 2 analyzers from entity constructors (still additive —
   the old `analyze_entity(mv, opns=…)`/`create(..., opns=…)` APIs remain).
4. **Phase 4** removes geometry-creating methods from the basis classes. It depends on
   Phase 3 so geometry can still be created via the `geometry` submodule after removal.
5. **Phase 5** removes `opns` from the **analysis** path and, in the same step, updates
   its direct callers (`Geometry.which_entity/analyze`, `viz`, `_point_path`) so those
   callers never pass a stale `opns=` that no longer exists.
6. **Phase 6** removes `opns` from the **creation** path and, in the same step, updates
   `Geometry.create` (adding `__call__`) and converts any internal `opns=True` sub-builds
   to private OPNS-only helpers.
7. **Phases 7–8** are documentation/examples only and touch no library code.

Phases 5 and 6 are deliberately split along the analysis/creation boundary; they are
the only two API-removal phases for the flag, and each bundles its callers + tests.
Phase 4 is set before them so the basis methods it removes are not later refactored.

---

## High-Risk Areas

1. **Internal `opns=True` sub-builds inside `create_*`** (e.g. `create_n3.create_line`
   builds OPNS points then wedges `einf`; `create_point_pair`/`create_circle`/
   `create_imag_point_pair`; `create_pga3.create_line` recurses with `opns=True`;
   `create_p3/p2.create_line` builds two OPNS points). A naive switch to `basis.opns`
   corrupts IPNS geometry. Phase 6 requires private OPNS-only builders for these steps.
2. **PGA grade conventions differ** (PGA3 point = grade‑3, P/N point = grade‑1).
   Typed analyzers must not hard-code a grade; they reuse the existing per-algebra
   decomposers.
3. **E3 has no finite point.** `Point(e3_vector)` works via the plain-vector shortcut,
   but `analyze_point(e3_vector)` must raise; the constructor's fallback ordering must
   keep the shortcut without hiding a genuine mismatch.
4. **Mutability semantics** — flipping `algebra.opns` mid-script reinterprets
   pre-existing MVs from that algebra; documented in the `opns` docstring.
5. **Frozen-dataclass recursion** — the numeric branch of `Point(A)`/`Direction(A)`
   must copy fields without re-entering the MV branch.

---

## Files to Create / Modify (roll-up)

### New files

| File | Content |
|------|---------|
| `py/tests/geometry/test_opns_algebra_flag.py` | Algebra/MV `opns` property tests (Phase 1) |
| `py/tests/geometry/test_typed_analyzers.py` | Typed analyzer round-trip + mismatch tests (Phase 2) |
| `py/tests/geometry/test_entity_constructors.py` | `Point(mv)/Direction(mv)/…` tests (Phase 3) |

### Modified files (library)

| File(s) | Change | Phase |
|---------|--------|-------|
| `py/pytanga/algebra/_algebra.py` | `opns` ctor kwarg + mutable property | 1 |
| `py/pytanga/algebra/_mv.py` | `opns` property | 1 |
| `py/pytanga/basis/*.py` (8) | forward `opns` to `super().__init__` | 1 |
| `py/pytanga/geometry/analysis_*.py` (8) | add typed analyzers | 2 |
| `py/pytanga/geometry/entities.py` | MV-accepting constructors; field-level auto-conversion; `Line.from_points` | 3 |
| `py/pytanga/basis/*.py` (6) | remove `point/direction/line/plane/vector/rotor` methods | 4 |
| `py/pytanga/geometry/create_*.py`, `analysis_*.py` | drop `hasattr(basis, ...)` fallbacks | 4 |
| `py/pytanga/geometry/analysis.py` | drop `opns`; re-export typed analyzers | 5 |
| `py/pytanga/geometry/analysis_*.py` (8) | `analyze_entity` reads `mv.algebra.opns` | 5 |
| `py/pytanga/geometry/_geometry.py` | drop stored `opns` on `which_entity/analyze` | 5 |
| `py/pytanga/viz/visualizer.py`, `_scene_handle.py`, `_app.py` | drop `opns` params/state | 5 |
| `py/pytanga/viz/_point_path.py` | `PointPath.add` auto-converts MVs via typed conversion; drop `opns` | 5 |
| `py/pytanga/geometry/create.py` | drop `opns`; dispatch to create_* | 6 |
| `py/pytanga/geometry/create_*.py` (8) | read `basis.opns`; private OPNS helpers | 6 |
| `py/pytanga/geometry/_geometry.py` | `Geometry.create` drops `opns`; add `__call__` | 6 |

### Modified files (tests / examples / docs)

| File(s) | Change | Phase |
|---------|--------|-------|
| `py/tests/geometry/*.py`, `py/tests/viz/*.py` | drop `opns=` args; set `alg.opns` | 1–6 |
| `py/examples/geometry/*.py`, `py/examples/viz/*.py`, `py/examples/basis/*.py`, `py/examples/numerics/*.py`, `py/examples/tensor/*.py` | new API; replace basis geometry methods | 7 |
| `docs/py/geometry/*.md`, `docs/py/viz/*.md` | new API | 8 |
