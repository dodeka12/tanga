# Phase 6 — docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` and re-verify the architecture docs reflect the `Act*` basis and
> the `from_entity`/`axis_directions` helpers.

## Goal

Finalize the user-facing docs and the branch changelog; run the full validation.

## Files

- Edit: `docs/py/viz/entities/labelme.md`
- Edit: `docs/py/viz/entities/active-elements/act-rectangle2d.md`
- Edit: `docs/py/viz/entities/active-elements/act-ellipse.md`
- Edit: `docs/py/viz/entities/active-elements/act-circle.md`
- Edit: `docs/changelog/YYYY/MM/DD_<hash-or-branch>.md` (append)

## Steps

- [x] **6.1 — `labelme.md`.**
  - State the ellipse `angle` frame ("radians from image horizontal") and the
    load/save identity guarantee.

- [x] **6.2 — Act docs.**
  - Document the new `dir_u`/`dir_v` params, `from_entity`, and (for the
    entities) `axis_directions()`.

- [x] **6.3 — Changelog.**
  - Append a bullet for `from_entity`, `axis_directions()`, and the export-frame
    fix (per `dev/workflows/changelog.md`).

- [x] **6.4 — Final validation.**
  - Run the full suite, lint, type, and docs build.

## Validation

`uv run pytest -rs && uv run ruff check . && uv run ty check && uv run mkdocs build --strict`

## Notes

- This is a follow-up to the already-open `fix/rectangle2d` PR; append to the
  existing branch changelog rather than starting a new one.
