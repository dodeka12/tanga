# Quadric module

`pytanga.quadric` is the projective quadric-space layer of the Python library.
It represents **2D conics** (symmetric 3×3 matrices) and **3D quadrics**
(symmetric 4×4 matrices) as grade-1 blades of a Euclidean-rescaled geometric
algebra, and owns all the quadric math: construction from points, MV ↔ entity
analysis, classification / refinement, entity → MV creation, point recovery, the
quadric-space rotation rotor, and two-quadric intersection.

It is deliberately a **leaf-ish, numpy-only** package. It imports
`pytanga.entity` (`Vec3` / `Point` / `Direction`) directly, and it imports
`pytanga.geometry.entities` *lazily* so the `quadric ↔ geometry.entities` cycle
never fires at import time. The cross-package layering is described in
[Geometry & quadric layering](geometry-module-layering.md); this page describes
the module's *internal* structure.

## Module map

| File | Responsibility |
| --- | --- |
| `_basis.py` | `BasisQ2` / `BasisQ3` — Euclidean-rescaled `G(6,0)` / `G(10,0)` algebras |
| `_embedding.py` | `embed_point` — the `x·xᵀ` point embedding |
| `_mapping.py` | `to_coeffs` / `from_coeffs` — symmetric-matrix ↔ coefficient-vector |
| `_build.py` | `conic_from_points` / `quadric_from_points` (+ `_svd`), `line_from_points` |
| `conic.py` | `Conic` / `Quadric3D` dataclasses, `EConicKind` / `EQuadricKind`, classification |
| `refine.py` | `refine_conic` / `refine_quadric` — matrix → specific geometry entity |
| `_create.py` | `create_*` — entity → MV, plus `create_rotor` |
| `_analysis.py` | `analyze_entity` / `analyze_operator` / `analyze_rotor` — MV → entity |
| `_pointset.py` | `point_from_embedding`, `pointset_from_blade`, `two_conic_intersection` |
| `_intersection.py` | `intersect_quadrics` — two quadrics → `PlaneConicPair` / `Curve` |

## Representation and data flow

A conic/quadric is stored as a **coefficient vector** (6 entries for a conic, 10
for a quadric) that is the exact inverse of the symmetric-matrix form — see
`_mapping.py` for the fixed ordering. The Euclidean rescaling puts the `√2/2`
factors *only* in `_embedding.py` and `_mapping.py`, so the plain `Algebra(6,0)`
/ `Algebra(10,0)` metric is used everywhere else.

The main pipeline is:

```
points ──embed_point──▶ MVs ──join/∧──▶ blade ──analyze_entity──▶ Conic/Quadric3D
                                                                    │
                                            ┌───────────────────────┘
                                            ▼
                                 refine() ──▶ specific entity (Ellipse, Cone, …)
                                            │
                                            ▼
                       viz serializer ──▶ renderer (curve.js, plane_pair.js, …)
```

- **Construction** (`_build.py`): `conic_from_points` / `quadric_from_points`
  wedge the point embeddings and take the dual; the `_svd` variants take the null
  vector of the stacked point embeddings instead (more robust to noise).
- **Analysis** (`_analysis.py`): `analyze_entity` prunes numerical noise, then
  dispatches on algebra dimension (Q2 vs Q3) and blade grade. IPNS input is
  dualized to OPNS first, so a single OPNS dispatch path handles both.
- **Refine** (`refine.py`, reached via `Conic.refine()` / `Quadric3D.refine()`):
  classifies the matrix and builds the concrete entity via eigen-decomposition.
- **Creation** (`_create.py`): inverts the round-trip — `create_circle`,
  `create_ellipse`, `create_cone`, `create_rotor`, … build the coefficient vector
  / MV from an entity. Every entity type here has a matching `refine_*` branch.

## Classification and refine

`Conic` / `Quadric3D` (in `conic.py`) expose cached properties computed from the
matrix's affine block form `[[Q, b], [bᵀ, c]]`:

- `rank` (full matrix) and `signature` (inertia `(n⁺, n⁻, n⁰)`),
- `kind` — the coarse projective classification, from the rank of the full matrix
  against the rank of the quadratic part `Q` (`parabola`, `ellipse`, `hyperbola`,
  `line_pair`, `cone`, `hyperboloid_2s`, `plane_pair`, …),
- `center`, `eigenvalues`, `principal_directions`, and `rho` (circle/sphere
  radius).

`refine.py` turns those into `pytanga.geometry.entities` objects. The degenerate
cases mirror Perwass's conic-space analysis: a rank-2 quadric is a plane pair
whose two homogeneous plane vectors are `√λ₊·v₊ ± √(−λ₋)·v₋` built from the
eigen-decomposition of the full matrix; a rank-1 quadratic part is a parallel
plane pair; a rank-3 quadric with a null vector is a cone whose apex is that null
vector (dehomogenised). `_line_pair_from_conic` is the 2D counterpart, and the two
share the same "factor a degenerate matrix" idea.

## Two-quadric intersection

`intersect_quadrics(Q1, Q2)` (`_intersection.py`) is numpy-only (no scipy). It
finds the **real degenerate members** of the pencil `span{Q1, Q2}` and returns
either:

- a **`PlaneConicPair`** — a rank-2 member factors into two planes; each plane is
  intersected with the *other* quadric to give a conic; or
- a sampled **`Curve`** — a rank-3 **cone** member is ruled: each generator
  (a line through the apex) meets the companion quadric in a quadratic, and the
  roots trace the quartic. That quartic is generally unbounded, so its asymptotic
  directions are solved analytically (a quartic in `tan(θ/2)` on the base conic)
  and sampled out to the `±extent` box, while the bounded body is sampled at a low
  resolution.

Degenerate-member detection combines the generalised-eigenvalue `solve` path with
a homogeneous-cubic fallback for pencils whose generators are both singular and
through the origin (e.g. a rotated exact cube). The elliptic hard case — no real
degenerate member — raises `NotImplementedError`.

## Point tuples and three-quadric intersection

A `k`-point **join** (OPNS blade, grades 2–7 in Q3, 2–4 in Q2) is analyzed as a
`PointSet` by dualizing to the space of quadrics through the points and
intersecting a generic triple of them (`_pointset.py`):

- `k = 2` uses the rank-1 pencil (a binary quadratic); Q2 `k = 3, 4` uses the
  conic complement + `two_conic_intersection`; Q3 `k = 3..7` uses the quadric
  complement + `intersect_three_quadrics`.
- `intersect_three_quadrics(Q1, Q2, Q3)` reduces to `intersect_quadrics(Q1, Q2)`
  and finds `Q3 = 0` along the quartic: exact through a plane-pair member's
  plane-conics, numeric by Newton-refining the cone-sample polyline.  Several
  random triplets are unioned and filtered to the points on *all* complement
  quadrics.
- `_analyze_q3` dualizes IPNS → OPNS first, so every IPNS grade routes through
  the same OPNS path.

A `k = 7` join returns **eight** points — the seven originals plus the
Cayley–Bacharach partner of the 3-dim net (see
`dev/theory/quadric-point-tuples.md`).

## Where to look for a change

| I want to… | File(s) |
| --- | --- |
| add a new conic/quadric kind | `conic.py` (enum + classifier), `refine.py`, `_create.py` |
| change how a point is embedded or a matrix maps to coeffs | `_embedding.py`, `_mapping.py` |
| change how an MV is analyzed (grade dispatch) | `_analysis.py` |
| change two-quadric intersection | `_intersection.py` |
| change the rotation rotor | `_create.py` (`create_rotor`), `_analysis.py` (`analyze_rotor`) |
| recover points from a blade / intersect two conics | `_pointset.py` |



