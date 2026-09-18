# Phase 9 — Docs, changelog, and full validation

## Goal

Document the type-specific named-basis sweep, update the developer architecture
note for `basis_for`, add a branch changelog, and run the full gate.

## Files

- Edit: `docs/py/ga/geometry/operators.md` (named-basis notes per type, as needed)
- Edit: `docs/py/ga/blade-mask/usage.md` (mention `mask_for` named bases)
- Edit: `docs/dev/architecture/geometry-module-layering.md` (extend the
  `basis_for` note to the full per-type dispatcher)
- New: `docs/changelog/2026/09/18_feat-expression-matrix.md` (append bullets)
- Edit: `docs/changelog/index.md` (PR time only)

## Steps

- [x] **9.1 — user + developer docs**
  - Note the per-algebra `basis_for_<type>` convention and the auto display basis
    in `docs/dev/architecture/geometry-module-layering.md`.
  - Add a short `mask_for` named-basis note in `docs/py/ga/blade-mask/usage.md`.

- [x] **9.2 — changelog**
  - Append a New Features bullet to the branch changelog describing the
    per-algebra named-basis sweep.

- [x] **9.3 — full validation**
  - `uv run pytest -q && uv run ruff check . && uv run ty check && uv run mkdocs build --strict`

## Validation

`uv run pytest -q && uv run ruff check . && uv run ty check && uv run mkdocs build --strict`

## Notes

- Changelog file is the existing branch changelog
  `docs/changelog/2026/09/18_feat-expression-matrix.md`; append, don't create a
  second file.  `docs/changelog/index.md` is only edited at PR time.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
