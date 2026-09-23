# Phase 5 — docs + changelog

## Goal

Update the developer docs and the branch changelog for the GA-only public API,
the sequence products, and the matrix constructor.

## Files

- Edit: `docs/dev/architecture/quadric-module.md`
- Edit: `docs/dev/architecture/geometry-module-layering.md`
- Edit: `docs/dev/ga/conic-quadric-space.md`
- Edit: `docs/changelog/2026/09/22_feat-quadric-solve.md`

## Steps

- [x] **5.1 — `quadric-module.md`**
  - Update the module map (drop `_build.py`; mark `_mapping`/`_embedding`/
    `_intersection`/`_pointset` backends as private), the pipeline diagram
    (points → `geo(Point)` → `op`/`join` → `analyze`), and the
    "where to look" table.

- [x] **5.2 — `geometry-module-layering.md`**
  - Update the DAG and the shims list: remove the `two_conic_intersection` shim;
    note `_from_coeffs` / `_to_coeffs` are now private.

- [x] **5.3 — `conic-quadric-space.md`**
  - Rewrite the construction/fit/intersection narrative to be GA-only
    (`geo(Conic/Quadric3D(m))`, `op`/`join`, `analyze`, `geo(Translator(...))`).

- [x] **5.4 — changelog** (`docs/changelog/2026/09/22_feat-quadric-solve.md`)
  - Add entries: GA sequence products; matrix-accepting `Conic`/`Quadric3D` +
    `to_matrix()`; pruned public `pytanga.quadric` API (see
    `dev/workflows/changelog.md`).

- [x] **5.5 — regenerate docs + validate**
  - `uv run mkdocs build --strict`.

## Validation

`uv run mkdocs build --strict`

## Notes

- `dev/theory/*.md` references to deleted functions are historical and may be left
  as-is (or lightly annotated).
- After this phase the plan `Status:` moves to `Done`; the PR then follows
  `dev/workflows/pull-request.md` (changelog hash rename + PR).

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
> touches, so the new code aligns with the documented architecture. If this work
> introduces or changes architecture, update the developer docs.
