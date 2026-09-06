# Phase 4 — docs + changelog

## Goal

Update the multivector and expression docs, and record the `project_to` removal
as a breaking change in the branch changelog.

## Files

- Edit: `docs/py/ga/algebra/mv.md`
- Edit: `docs/py/ga/expression/usage.md`
- New: `docs/changelog/YYYY-MM-DD_fix-expressions.md` (append to the existing
  branch changelog, run date)

## Steps

- [x] **4.1 — Update `mv.md`**
  - Replace the `project_to` table row with `project_onto`, documenting
    `a.project_onto(b)` for `b: MV | BladeMask` (exact membership) and the new
    direction.

- [x] **4.2 — Update `expression/usage.md`**
  - Add a short "Constant expressions" note: `Expression(A)` and
    `Expression(A, BladeMask)` produce a zero-variable constant expression.

- [x] **4.3 — Changelog**
  - Per `dev/workflows/changelog.md`, append to the existing branch changelog
    `docs/changelog/2026-09-02_fix-expressions.md`:
    - `## New Features` — `project_onto` (MV + `BladeMask`), and constant
      `Expression(A)` / `Expression(A, BladeMask)`.
    - `## Breaking Changes` — `project_to` removed (use `project_onto`).
  - Do **not** rename to a hash or touch `docs/changelog/index.md`; that is the
    PR-time step in `dev/workflows/pull-request.md`.

## Validation

`uv run pytest && uv run mkdocs build --strict`

## Notes

- The changelog title/since-version stays as already authored
  (`# Changes since version 1.16.0`) — only append the new bullets.
- `Status:` in this plan's `README.md` moves to `Done` after this phase.
