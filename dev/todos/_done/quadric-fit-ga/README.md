# Quadric GA-native fitting, cone lift & tolerant analysis — Overview

**Created:** 2026-09-22 | **Status:** Done | **Branch:** `feat/quadric-solve`

## Goal

Make `pytanga.quadric`'s from-points fitting a thin wrapper over the GA expression
system (embed → scalar-product incidence → `DataArray` → `Expression.lstsq`), fix the
expression solver's underdetermined-homogeneous null-space bug, add a general
algebra-embedding primitive so a Q2 conic can be lifted into a Q3 cone
(`BasisQ3(c)`), and add tolerance-aware conic/quadric classification through the
`Geometry` subsystem. Ships example scripts for each new capability.

## Architecture (short)

- **Solver** (`py/pytanga/expression/_expression.py`) — `Expression`/`AffineExpression`
  `lstsq(rhs=None)` and `svd()` switch to `full_matrices=True` so the null space of a
  wide (underdetermined) linear system is returned instead of silently dropped.
- **Fit** (`py/pytanga/quadric/_build.py`) — `conic_from_points_svd`/
  `quadric_from_points_svd` are reimplemented on a new `_incidence_expression`
  (embed → `c.sp(p)` → `DataArray`) plus the fixed solver; new MV-returning helpers and
  a singular-spectrum / nullity diagnostic.
- **Embed + cone lift** (`py/pytanga/algebra/_algebra.py`, `_mv.py`,
  `py/pytanga/quadric/_basis.py`, `_create.py`) — a general `Algebra.embed`/
  `MV.to_algebra` blade-relabeling primitive, the canonical Q2→Q3 cone blade map,
  `BasisQ3.__call__`, and `cone_from_conic`.
- **Tolerant analysis** (`py/pytanga/geometry/_geometry.py`, `refine.py`,
  `py/pytanga/quadric/conic.py`, `refine.py`) — a `tol` on `Geometry` threaded through
  `refine`/classification so a noisy quadric can be classified "within a tolerance"
  (e.g. `cone`).

## Canonical contract (fixed up front)

- **Incidence operator:** scalar product `sp` (`c.sp(p) == ½·xᵀ A x`); the conic/quadric
  and the point embedding are both grade-1 blades of the Euclidean-rescaled quadric space.
- **Solver fix:** `np.linalg.svd(..., full_matrices=True)`; `svd()` returns
  `(values, mvs)` with `len == len(var_mask)`, `values` padded with zeros for the null
  space (trailing zero singular values = null vectors).
- **Cone blade map** (Q2→Q3, apex at origin, base conic in `z=1`):
  `{1:256, 2:512, 4:64, 8:16, 16:32, 32:128}` (`b1→b9, b2→b10, b3→b7, b4→b5, b5→b6, b6→b8`).
- **Tolerant analysis:** `Geometry(algebra, *, tol=None)` + settable `Geometry.tol`
  (default `None` → `algebra.precision`); `Geometry.refine(entity, *, tol=None)`
  threads it into `refine_conic`/`refine_quadric` → `_classify_*`.

## Decisions (confirmed)

- All four capabilities ship (solver fix, GA-native fit, embedding/cone-lift, tolerant
  classification) plus example scripts.
- `which_entity`/`analyze` keep returning the raw `Conic`/`Quadric3D`; the tolerant
  classification happens at the `refine` step (`geo(raw)` / `geo.refine(raw)`).
- The cone lift is the apex-at-origin / `z=0`-base blade relabel plus the existing
  translate-to-vertex step; no `Cone`-entity generalization (only right-circular cones
  round-trip through `refine`).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-solver-nullspace-fix.md](./01-solver-nullspace-fix.md) | `full_matrices=True` null-space fix + padded `svd()` spectrum |
| 2 | [02-ga-native-fit.md](./02-ga-native-fit.md) | Expression-system conic/quadric fit + MV helpers + diagnostics |
| 3 | [03-algebra-embed-cone-lift.md](./03-algebra-embed-cone-lift.md) | `Algebra.embed`/`MV.to_algebra`, cone blade map, `BasisQ3(c)`, `cone_from_conic` |
| 4 | [04-tolerant-analysis.md](./04-tolerant-analysis.md) | `Geometry.tol` + tolerance-aware classification/refinement |
| 5 | [05-examples.md](./05-examples.md) | Example scripts for fit, cone lift, tolerant classification |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Architecture + theory docs + changelog |
| 7 | [07-operator-translation.md](./07-operator-translation.md) | `geo(Translator(t))` as a linear-map expression |

## Testing as you go

- **Python:** `uv run pytest py/tests/expression -q py/tests/quadric -q py/tests/geometry -q` (targeted files per phase).
- **Lint/type:** `uv run ruff check .` / `uv run ty check` (final phase).
- **Docs:** `uv run mkdocs build --strict` and `uv run python tools/generate-example-docs.py --check` (final phases).

## Non-goals

- Generalizing the `Cone` entity / `_cone_from_quadric` to oblique cones.
- A dedicated `cone_from_points_svd(basis, points, apex=...)` sugar (a two-line
  composition of phases 2–3).
- Changing `which_entity`/`analyze` to return refined entities directly.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
