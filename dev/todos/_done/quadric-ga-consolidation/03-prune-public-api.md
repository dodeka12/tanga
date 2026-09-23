# Phase 3 — prune the public `pytanga.quadric` API

## Goal

Shrink `pytanga.quadric`'s public surface to the GA-centric contract in the
README: delete GA-superseded helpers, rename internal backends to `_`-prefix, and
drop the raw `create_*` / `refine_*` / `CONE_BLADE_MAP` re-exports.

## Files

- Edit: `py/pytanga/quadric/__init__.py` (shrink `__all__` + imports)
- Edit: `py/pytanga/quadric/_mapping.py`, `_embedding.py`, `_intersection.py`,
  `_pointset.py`, `_create.py`, `_analysis.py`, `conic.py` (renames + call sites)
- Delete: `py/pytanga/quadric/_build.py`
- Edit: `py/pytanga/geometry/__init__.py`, `py/pytanga/geometry/_pointset.py`
  (drop the `two_conic_intersection` re-export shim)
- Edit: `py/tests/quadric/test_core.py`, `test_cone_lift.py`, `test_fit_ga.py`

## Steps

- [x] **3.1 — private renames**
  - `embed_point → _embed_point`, `from_coeffs → _from_coeffs`,
    `to_coeffs → _to_coeffs`, `intersect_quadrics → _intersect_quadrics`,
    `intersect_three_quadrics → _intersect_three_quadrics`,
    `two_conic_intersection → _two_conic_intersection`; update every internal
    call site (`conic.py`, `_analysis.py`, `_create.py`, `_pointset.py`).

- [x] **3.2 — delete GA-superseded functions**
  - Delete `conic_from_points`, `conic_from_points_mv`, `conic_from_points_svd`,
    `quadric_from_points`, `quadric_from_points_mv`, `quadric_from_points_svd`,
    `line_from_points`, `fit_singular_values`, `fit_nullity`; delete the now-empty
    `_build.py` module.
  - Delete `cone_from_conic` in `_create.py` (its helper `_centered_matrix` stays
    only if still used by `create_cone`/`create_quadric`).

- [x] **3.3 — shrink `__all__`**
  - `py/pytanga/quadric/__init__.py` exports exactly the 10-name list from the
    README; drop `create_*`, `refine_conic`, `refine_quadric`, `CONE_BLADE_MAP`,
    and all deleted names from the import block and `__all__`.

- [x] **3.4 — drop the `geometry` shim**
  - Remove `two_conic_intersection` from `py/pytanga/geometry/__init__.py` and
    `py/pytanga/geometry/_pointset.py` (keep `point_from_embedding` /
    `pointset_from_blade` as internal re-exports).

- [x] **3.5 — update tests**
  - Delete `TestBuildFromPoints` and the `TestMapping` cases tied to the removed
    public names (re-point any kept coverage at `_mapping` / `_to_coeffs`).
  - Delete `test_cone_from_conic_*` in `test_cone_lift.py` (keep the
    `BasisQ3.__call__` / `CONE_BLADE_MAP` coverage).
  - Rewrite `test_fit_ga.py` to drive `Expression.svd`/`lstsq` directly (no
    `fit_nullity` / `fit_singular_values`).

## Validation

`uv run pytest py/tests/quadric py/tests/geometry -q && uv run ty check`

## Notes

- `_intersect_quadrics` / `_intersect_three_quadrics` / `_two_conic_intersection`
  remain as the private backends that `analyze` (via `_analysis` / `_pointset`)
  calls — they are not deleted, only hidden.
- The `create_*` / `refine_*` functions stay importable from their submodules
  (`_create.py`, `refine.py`) for `pytanga.geometry`'s dispatchers.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
> touches, so the new code aligns with the documented architecture. If this work
> introduces or changes architecture, update the developer docs.
