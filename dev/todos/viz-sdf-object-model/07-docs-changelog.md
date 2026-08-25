# Phase 7 — Docs + changelog

## Goal

Document the new SDF object model and record the change in the changelog.

## Files

- Modify: `docs/py/viz/sdf-objects.md` — rewrite the "Groups with `SdfGroup`"
  section into the new object-model API (styles, `SdfObject`, operators,
  per-object materials); keep the legacy `SdfStyle` marker documented as
  deprecated-but-supported.
- Modify: `docs/py/viz/sdf-viewer.md` — note that the standard-viewer object
  model now has per-entity SDF styles and operators (fullscreen viewer
  unchanged).
- Modify: `docs/changelog/2026-08-22_feat-sdf-viewer.md` — add bullets for
  per-entity `Sdf*Style`, `SdfObject`/`Combine` + `ECompose` operators, and
  per-object materials.
- Modify: `mkdocs.yml` if any new doc page is added (none expected).

## Steps

- [ ] **7.1 — `docs/py/viz/sdf-objects.md`**
  - New "SDF object model" section: per-entity styles table, `SdfObject`,
    operator table (`+`/`|`/`-`/`&`/`^`/`-x`/`~x`), `ECompose`, `Composed`/
    `SdfGroup`, per-object materials.
  - "Backward compatibility" note: `viz.add(Sphere(...), style=SdfStyle(...))`
    still works.

- [ ] **7.2 — `docs/py/viz/sdf-viewer.md`**
  - One-line cross-reference (the fullscreen viewer is unchanged; the standard
    viewer gained the object model).

- [ ] **7.3 — Changelog** (`2026-08-22_feat-sdf-viewer.md`)
  - Add concise bullets (mirror the README goal), with test-file references.

- [ ] **7.4 — Validate**
  - `uv run mkdocs build` (green; existing unrelated warnings acceptable).

## Validation

`uv run mkdocs build` (builds cleanly).

## Notes

- Follow `dev/workflows/changelog.md` for changelog structure/naming.
