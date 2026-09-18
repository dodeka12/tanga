# Phase 6 — Docs, changelog, and full validation

## Goal

Update user docs and developer architecture docs, add a branch changelog, and run
the full validation gate.

## Files

- Edit: `docs/py/ga/blade-mask/construction.md`
- Edit: `docs/py/ga/blade-mask/properties-and-ops.md`
- Edit: `docs/py/ga/blade-mask/usage.md`
- Edit: `docs/py/ga/expression/usage.md`
- Edit: `docs/py/ga/geometry/operators.md` (TwistBivector named basis note)
- Edit: `docs/dev/architecture/geometry-module-layering.md` (`basis_for` hook note)
- New: `docs/changelog/2026/09/18_feat-expression-matrix.md` (branch changelog)
- Edit: `docs/changelog/index.md` (on PR finalization only — see Notes)

## Steps

- [x] **6.1 — user docs**
  - Document `BladeMask.basis_vectors`/`basis_names`/`with_basis`/`basis_matrix`,
    auto display basis, composed-name parsing, and basis-aware
    `union`/`intersection(discard_basis=…)` in `docs/py/ga/blade-mask/*`.
  - Document `Expression.get_tensor()` / `AffineExpression.get_tensor()` (raw
    `MVTensor`) and `MVTensor.get_array()` (`out_basis`/`axis_bases`, returns
    `np.ndarray`) in `docs/py/ga/expression/usage.md`.
  - Add a `TwistBivector` note (6 physical DOF named basis) to
    `docs/py/ga/geometry/operators.md`.

- [x] **6.2 — developer docs**
  - Update `docs/dev/architecture/geometry-module-layering.md`: per-algebra
    `basis_for` hook feeds `mask_for`'s named basis.

- [x] **6.3 — changelog**
  - Create `docs/changelog/2026/09/18_feat-expression-matrix.md` per
    `dev/workflows/changelog.md` (title from `uv run python tools/last-release.py`;
    New Features bullets for named `BladeMask` bases, `get_tensor()`, and the
    `TwistBivector` named basis).
  - Do **not** edit `docs/changelog/index.md` yet — that happens at PR time after
    the hash rename.

- [x] **6.4 — full validation**
  - Run the complete gate and confirm green.

## Validation

`uv run pytest -q && uv run ruff check . && uv run ty check && uv run mkdocs build --strict`

## Notes

- Changelog filename uses the branch start date (2026-09-18) and branch name
  `feat-expression-matrix`; it is renamed to the squashed-commit hash at PR time
  (see `dev/workflows/changelog.md` / `dev/workflows/pull-request.md`).
- This phase records that the work adds named-basis metadata to `BladeMask` with
  **no `MVTensor` change**; the developer-docs edits in 6.2 document the
  `basis_for` hook only.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
