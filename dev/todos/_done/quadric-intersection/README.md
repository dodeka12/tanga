# Quadric intersection (two-quadric curve) — Overview

**Created:** 2026-09-12 | **Status:** Done | **Branch:** `feat/quadric-space`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md` and `viz-architecture.md`) for the subsystem(s)
> this work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Implement the analysis of the **intersection of two 3D quadrics** (the deferred
IPNS grade-2 path in `quadric/_analysis.py`) and render it as a curve.  Two
displayable cases are handled via the pencil's degenerate members (Perwass's
conic method, one dimension up); the genuinely hard elliptic case raises for
now and is sketched separately.

## Architecture (short)

- **`pytanga.quadric/_intersection.py`** (new) — `intersect_quadrics(Q1, Q2)`:
  the pure **numpy** math (no scipy).  Finds the degenerate members of the pencil
  `Q1 − λQ2`, then either factors a plane-pair member into two plane-conics, or
  samples a cone member into a polyline.  Returns entities (imported lazily).
- **`pytanga.geometry.entities`** — three new entities (see contract below).
- **`pytanga.quadric/_analysis.py`** — `_analyze_q3` IPNS grade 2 now factors the
  bivector into two quadrics and calls `intersect_quadrics` (replaces the
  "deferred" `NotImplementedError`).
- **`pytanga.viz`** — serializers that sample the conics/curve into polylines in
  Python, plus one `curve.js` frontend renderer (draws a 3D polyline) and two
  styles.  Sampling is done **in Python**; the frontend only draws polylines.

## Fixed contract (decided up front)

### Entities

```python
@dataclass(frozen=True)
class PlaneConic:          # a conic lying in a 3D plane
    plane: Plane           # the plane (point + normal)
    conic: Conic           # 2D conic in the plane's canonical local 2D frame

@dataclass(frozen=True)
class PlaneConicPair:      # plane-pair degenerate member → two plane-conics
    conic1: PlaneConic
    conic2: PlaneConic

@dataclass(frozen=True)
class Curve:               # cone degenerate member → sampled polyline
    points: tuple[Point, ...]   # ordered
```

- **Canonical local 2D frame** (single helper `_plane_frame(n)` in
  `quadric/_intersection.py`, used by both the intersection code and the
  serializer, so they never drift): unit normal `n` → `u = normalize(n × e_z)`
  (fallback `e_x` if `n ∥ e_z`), `v = n × u`; local coords `(s, t)` map to 3D as
  `x = plane.point + s·u + t·v`.  `PlaneConic.conic` is expressed in this
  `(s, t)` frame.
- `Curve.points` is a single ordered polyline (the primary component).  Splitting
  a multi-component quartic into several polylines is a known simplification, not
  part of this plan.

### `intersect_quadrics(Q1, Q2) → PlaneConicPair | Curve`

- Input: two symmetric 4×4 matrices (also accept two `Quadric3D`).
- 1. Find degenerate members of `span{Q1, Q2}` — **numpy-only**:
  - If `det(Q2) ≠ 0`: `M = solve(Q2, Q1)`, real eigenvalues `λ` → member
    `Q1 − λQ2` with `rank ≤ 3`.  If instead `det(Q1) ≠ 0`, swap `Q1 ↔ Q2`
    (mirrors the 2D `two_conic_intersection`).
  - **Always append** the endpoint members `Q1` (`λ = 0`) and `Q2` (`λ = ∞`)
    themselves when they have `rank ≤ 3` — this surfaces the degenerate members
    for the both-singular case (the cube: both inputs are plane pairs, so `det`
    is identically zero and `solve` is unavailable).
  - Both-singular **through the origin** (a common null vector, e.g. the cube's
    pencil of cones): recover the rank-2 plane-pair members via the homogeneous
    cubic `det(α q₁ + β q₂) = 0` on the 3×3 quadratic parts.
  - Still deferred (see Non-goals): a common null vector that is *not* the
    origin (e.g. two cones sharing a finite apex) needs a translation first.
- 2. For each member, classify by rank/signature:
  - rank 2 indefinite → **plane pair** (factor into 2 planes).
  - rank 1 → **plane** (single plane).
  - rank 3 indefinite → **cone**.
  - rank 2/3 definite, rank 0 → imaginary / degenerate → skip.
- 3. Return: if a plane-pair (or plane) member exists → `PlaneConicPair` (each
  plane ∩ `Q1` = a 2D conic); else if a cone member exists → `Curve` (sampled);
  else raise `NotImplementedError` (the hard case — see the separate sketch).
  Prefer the plane-pair member over the cone (exact conics beat sampling).

## Decisions (confirmed)

- **Two specific result entities** — `PlaneConicPair` (plane-pair case) and a
  sampled `Curve` (cone case), rather than one unified entity (confirmed by the
  user).
- **Hard case raises `NotImplementedError` for now**; the elliptic/marching
  approach is sketched in `dev/todos/quadric-intersection-hard-case.md` (outside
  this plan).
- **Sampling in Python, polylines on the wire** — no conic-parameter math in the
  frontend; one `curve.js` renderer serves both `PlaneConicPair` and `Curve`.
- **`intersect_quadrics` is the primary entry point**; `analyze()` on the IPNS
  grade-2 blade is a thin wrapper (factor → intersect).
- **numpy-only, no scipy** — the degenerate-member detection uses
  `np.linalg.solve` + `np.linalg.eigvals` (the existing 2D pattern) and appends
  the input quadrics themselves when they are degenerate, covering the generic,
  one-singular, and both-singular (cube) cases.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-entities-plane-pair.md](./01-entities-plane-pair.md) | Entities + `intersect_quadrics` plane-pair/plane cases |
| 2 | [02-cone-case.md](./02-cone-case.md) | Cone (rank-3) member → sampled `Curve` |
| 3 | [03-analyze-integration.md](./03-analyze-integration.md) | `analyze()` on IPNS grade-2 → `intersect_quadrics` |
| 4 | [04-viz-renderers.md](./04-viz-renderers.md) | Serializers + `curve.js` renderer + styles + factory |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Changelog, example, docs regen, full regression |

## Testing as you go

- `uv run pytest py/tests/geometry/test_conic_analysis.py -q` (phases 1–3)
- `uv run pytest py/tests/viz/test_serializer.py -q` (phase 4)
- `uv run python tools/generate-example-docs.py --check` (phase 5)
- `uv run pytest -q` + `uv run mkdocs build --strict` (phase 5)

## Non-goals

- No `create()` (entity → MV) for the new entities — they are analysis results,
  not constructible inputs.
- No frontend conic-sampling math (sampling is in Python).
- No handling of the **hard case** (no real degenerate member → smooth elliptic
  quartic) — raises `NotImplementedError`; sketched separately.
- No handling of the **common-null-vector-not-at-origin corner** (both inputs
  singular with a shared finite apex/point and neither a plane pair) — needs a
  translation before the cubic fallback; deferred.  The through-the-origin case
  is handled (the cube).
- No multi-component curve splitting (single polyline per `Curve`).
- No PR / changelog hash rename (deferred to the combined quadric PR).
