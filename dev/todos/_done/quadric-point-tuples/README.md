# Quadric point tuples (Q2/Q3 joins) — Overview

**Created:** 2026-09-13 | **Status:** Done | **Branch:** `feat/quadric-space`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md` and `quadric-module.md`) for the subsystem(s)
> this work touches, so the new code aligns with the documented architecture.
> If this work introduces or changes architecture, update the developer docs.

## Goal

Analyze a `k`-point **join** (OPNS blade, grades 2–7 in Q3; grades 2–4 in Q2)
as a `PointSet`, and make the IPNS dual of every such grade work through the
same path.  This completes the quadric-space entity analysis so every grade maps
to a displayable entity.

## Theory

`dev/theory/quadric-point-tuples.md` — the dual/net correspondence, the
complement → intersect → filter method, the net method vs. the pencil (cone)
reduction, and the `k = 7 → 8` Cayley–Bacharach phenomenon.

## Architecture (short)

- **`pytanga.quadric/_pointset.py`** — uniform point recovery.  `k = 2` uses the
  binary-quadratic rank-1 pencil; Q2 `k = 3, 4` uses the conic complement +
  `two_conic_intersection`; Q3 `k = 3..7` uses the quadric complement +
  `intersect_three_quadrics` (several random triplets are unioned and filtered to
  the points on *all* complement quadrics).
- **`pytanga.quadric/_intersection.py`** — `intersect_three_quadrics(Q1, Q2, Q3)`:
  reduce to `intersect_quadrics(Q1, Q2)` and locate `Q3 = 0` along the quartic
  (exact via a plane-pair member's plane-conics, numeric via Newton-refining the
  cone-sample polyline).  `intersect_quadrics` gained `n`/`extent` sampling
  parameters.
- **`pytanga.quadric/_analysis.py`** — `_analyze_q3` now dualizes IPNS → OPNS and
  reuses `_analyze_q3_opns` (one line), so every IPNS grade works.

## Phases

- [x] **Phase 0 — Theory document** (`dev/theory/quadric-point-tuples.md`).
- [x] **Phase 1 — IPNS dualize** (`_analysis.py`): `_analyze_q3` dualizes IPNS →
  OPNS and dispatches through `_analyze_q3_opns`.
- [x] **Phase 2 — Three-quadric intersection** (`_intersection.py`):
  `intersect_three_quadrics` (plane-pair exact path + cone Newton path).
- [x] **Phase 3 — Uniform point recovery** (`_pointset.py`):
  `_points_from_join_via_quadrics` via the orthogonal complement; `k = 7`
  returns the eight base points (Cayley–Bacharach).
- [x] **Phase 4 — Tests + docs** (`py/tests/geometry/test_conic_intersections.py`
  per-grade tests incl. the `k = 7 → 8` case and IPNS dualize).

## Notes / known limitations

- A `k = 7` join returns **eight** points (the seven originals + the
  Cayley–Bacharach partner), which is mathematically correct.
- The cone path samples the quartic out to a `[-extent, extent]³` box
  (`extent = 5`, `n = 200`); a join point far outside that box on an unbounded
  quartic can be missed.  This is a sampling density limitation of the numeric
  path, not a correctness gap for typical (unit-scale) point tuples.
