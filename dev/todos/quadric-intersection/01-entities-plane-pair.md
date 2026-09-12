# Phase 1 — Entities + `intersect_quadrics` (plane-pair / plane cases)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Add the `PlaneConic`, `PlaneConicPair`, `Curve` entities and implement
`intersect_quadrics(Q1, Q2)` for the **plane-pair** (rank-2) and **plane**
(rank-1) degenerate members.  The cone member and the hard (no-real-member) case
raise `NotImplementedError` in this phase.

## Files

- New: `py/pytanga/geometry/entities/plane_conic.py`
- New: `py/pytanga/quadric/_intersection.py`
- Edit: `py/pytanga/geometry/entities/__init__.py`
- Edit: `py/pytanga/geometry/__init__.py`
- Edit: `py/pytanga/quadric/__init__.py`
- Edit: `py/tests/geometry/test_conic_analysis.py`

## Steps

- [x] **1.1 — Add the three entities** (`geometry/entities/plane_conic.py`)
  - `PlaneConic(plane, conic)` — frozen dataclass; coerce `plane` via
    `_to_plane` (mirror `plane_pair.py`) and `conic` via `Conic` (import from
    `pytanga.quadric`, already re-exported by `geometry.entities`).
  - `PlaneConicPair(conic1, conic2)` — two `PlaneConic`.
  - `Curve(points)` — frozen dataclass; `points` coerced to a tuple of `Point`.
  - Add `__repr__` for each.
- [x] **1.2 — Export the entities**
  - `geometry/entities/__init__.py`: import the three, add to the `Entity` union
    and `__all__`.
  - `geometry/__init__.py`: import + `__all__`.
- [x] **1.3 — `quadric/_intersection.py`: degenerate-member detection (numpy-only)**
  - `_degenerate_members(A, B) -> list[np.ndarray]`:
    - If `abs(det(B)) ≥ 1e-12`: `M = np.linalg.solve(B, A)`; for each real
      eigenvalue `λ` of `M` (`|imag| < 1e-9`): member `A − λ B`, keep if
      `rank ≤ 3` (tolerance `1e-9`).  Else if `abs(det(A)) ≥ 1e-12`, swap `A ↔ B`
      and repeat (mirrors the 2D `two_conic_intersection`).
    - **Always append** `A` and `B` themselves when their rank is `≤ 3`
      (captures the `λ = 0` / `λ = ∞` members; covers the both-singular cube
      pencil where `det` is identically zero and `solve` is unavailable).
    - Deduplicate members (normalize scale, drop near-duplicates).
  - No scipy — only `numpy` (verified: `solve`+`eigvals` yields the rank-3 cone
    members for a generic pencil; appending the inputs yields the plane pairs for
    the cube).
- [x] **1.4 — `_plane_frame(n)` + `_conic_from_plane_quadric`**
  - `_plane_frame(n) -> (u, v)`: canonical orthonormal 2D basis (README contract:
    `u = normalize(n × e_z)`, fallback `e_x`; `v = n × u`).
  - `_plane_conic_from_quadric(Q, plane) -> PlaneConic`: build the local frame
    `(u, v)` with origin `plane.point`; substitute `x = p + s·u + t·v` (homogeneous
    `x_H = [x, 1]`) into `x_Hᵀ Q x_H = 0`; collect the `(s², t², st, s, t, 1)`
    coefficients into a `Conic` (matching `from_coeffs` ordering).
- [x] **1.5 — `intersect_quadrics(Q1, Q2)` dispatch (plane-pair / plane / raise)**
  - Coerce inputs to 4×4 `np.ndarray` (accept `Quadric3D` by using `.matrix`).
  - `members = _degenerate_members(Q1, Q2)`.
  - For each member, classify:
    - rank 2 indefinite → `_plane_pair_from_matrix` (eigen-decomposition →
      two plane vectors, mirror `refine.py::_plane_pair_from_quadric`) → two
      `Plane`s → two `PlaneConic` via step 1.4 → return `PlaneConicPair`.
    - rank 1 → one plane (mirror `refine.py::_plane_from_quadric`) → one
      `PlaneConic` → return `PlaneConicPair(conic, conic)` (degenerate double).
    - rank 3 indefinite (cone) → `raise NotImplementedError("cone member — phase 2")`.
    - else (definite / rank 0) → skip.
  - If no plane-pair/plane member and no cone member → `raise NotImplementedError`
    (hard case — see `dev/todos/quadric-intersection-hard-case.md`).
  - Import `Plane`/`PlaneConic`/`PlaneConicPair`/`Curve` **lazily** (mirror
    `refine.py::_entities()`), preserving the `quadric → geometry.entities`
    layering.
- [x] **1.6 — Export `intersect_quadrics`** from `quadric/__init__.py` (`__all__`).
- [x] **1.7 — Tests** (`test_conic_analysis.py`, new `TestQuadricIntersection`)
  - Cube pencil: `Q1 = x²−y²`, `Q2 = y²−z²` → `intersect_quadrics` returns a
    `PlaneConicPair`; each `PlaneConic.conic` refines (`refine`) to a `LinePair`
    (two lines), and the four lines are the cube body diagonals
    `(1,1,1), (1,1,−1), (−1,1,1), (1,−1,1)` (up to sign).
  - Two intersecting planes (`x=0`, `y=0`) → `PlaneConicPair` with two line
    conics (the coordinate axes in each plane).
  - `intersect_quadrics(sphere_matrix, ellipsoid_matrix)` with a known circle
    case → plane-pair member gives two conics (or a single circle-conic).
  - No-real-member case raises `NotImplementedError` (assert with `pytest.raises`).

## Validation

`uv run pytest py/tests/geometry/test_conic_analysis.py -q`

## Notes

- The plane-pair factorization already exists (private) in `refine.py`; re-use
  its eigen-decomposition logic here or extract a shared helper — do **not**
  duplicate the math with different sign conventions.
- The cube's two input quadrics are both rank 2 (singular), so the
  `solve`+`eigvals` step is unavailable (`det` identically zero); the "append
  `A`/`B` when rank ≤ 3" step is what surfaces the plane-pair members (`Q1` and
  `Q2` themselves), which is sufficient to recover all four body diagonals.
- `PlaneConic.conic` may itself be degenerate (a line pair) — that is expected
  and correct for the cube case.
