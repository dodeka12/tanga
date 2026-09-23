# quadric-ga-consolidation — Overview

**Created:** 2026-09-23 | **Status:** Done | **Branch:** `feat/quadric-solve`

## Goal

Make `pytanga.quadric`'s public surface **GA-only**. Every conic/quadric
construction, fit, and intersection that can be expressed through
`BasisQ2`/`BasisQ3` + `Geometry` (`geo(...)`) + GA operations (`op`/`join`/`meet`/`gp`,
`dual`, `sp`, `vp`) + `analyze`/`refine` is moved onto that route, and the
raw-coefficient / matrix / fit / intersection helpers are made private or deleted.

## Architecture (short)

- `pytanga.algebra` gains module-level sequence reducers `op`, `join`, `meet`, `gp`
  (`mvs: Sequence[MV] -> MV`), left-folding `MV.op/.join/.meet/.gp`.
- `Conic` / `Quadric3D` accept a symmetric matrix (3×3 / 4×4 — `np.ndarray` or
  `pytanga.geometry.Matrix`) in `__init__` and expose `to_matrix() -> np.ndarray`
  (satisfying the runtime-checkable `MatrixProvider` protocol).
- `pytanga.quadric.__all__` shrinks to the GA-centric names below; everything else
  is private (`_`-prefixed), deleted, or dropped from the package re-export.

## Fixed contract (decided up front; do not change after phase 1)

**Sequence functions** (new, in `pytanga.algebra`):

```python
def op(mvs: Sequence[MV]) -> MV: ...    # outer (wedge) product
def join(mvs: Sequence[MV]) -> MV: ...  # join
def meet(mvs: Sequence[MV]) -> MV: ...  # meet
def gp(mvs: Sequence[MV]) -> MV: ...    # geometric product
```

Empty sequence → `ValueError`; length-1 → returned unchanged; else a left fold.

**Public `pytanga.quadric` surface after this plan:**

```python
__all__ = [
    "analyze_entity", "analyze_operator", "analyze_rotor",
    "BasisQ2", "BasisQ3",
    "Conic", "EConicKind", "EQuadricKind", "Quadric2D", "Quadric3D",
]
```

**Deleted (removed outright):** `conic_from_points`, `conic_from_points_mv`,
`conic_from_points_svd`, `quadric_from_points`, `quadric_from_points_mv`,
`quadric_from_points_svd`, `line_from_points`, `cone_from_conic`,
`fit_singular_values`, `fit_nullity` (and the now-dead `_build.py` module).

**Made private (`_`-prefix, kept as internal backends):** `embed_point`,
`from_coeffs`, `to_coeffs`, `intersect_quadrics`, `intersect_three_quadrics`,
`two_conic_intersection` (also removed from the `pytanga.geometry` re-export shim).

**Dropped from `__all__` (kept in submodules, still used internally):** the 17
`create_*` functions, `refine_conic`, `refine_quadric`, `CONE_BLADE_MAP`.

## Decisions (confirmed)

- **Delete** (not private-alias) the GA-superseded fit/intersection helpers.
- The 2D conic-conic intersection demo gets its **own file**
  (`conic_intersection_demo.py`); the quadric-intersection demo stays 3D-only.
- Sequence functions are named `op`, `join`, `meet`, `gp`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-ga-sequence-products.md](./01-ga-sequence-products.md) | `op`/`join`/`meet`/`gp` sequence reducers |
| 2 | [02-quadric-matrix-constructor.md](./02-quadric-matrix-constructor.md) | matrix-accepting `Conic`/`Quadric3D` + `to_matrix()` |
| 3 | [03-prune-public-api.md](./03-prune-public-api.md) | private / delete / drop the non-GA quadric API |
| 4 | [04-examples.md](./04-examples.md) | rewrite examples + new conic-intersection demo |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | architecture docs + changelog |

## Testing as you go

- Python: `uv run pytest -rs`
- Lint + type: `uv run ruff check .` and `uv run ty check`
- Docs: `uv run mkdocs build --strict` and
  `uv run python tools/generate-example-docs.py --check`

## Non-goals

- No new conic/quadric kinds and no classification changes.
- No changes to the `viz` renderer or serializers.
- No changes to the `pytanga.geometry` `create`/`analyze`/`refine` facades (only the
  `two_conic_intersection` re-export shim is removed).

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
> touches, so the new code aligns with the documented architecture. If this work
> introduces or changes architecture, update the developer docs.
