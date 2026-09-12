# Phase 6 — Docs + changelog

## Goal

Update the public expression docs and the branch changelog.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `docs/py/ga/expression/usage.md`
- Edit: `docs/changelog/2026/09/11_fix-jupyter.md`

## Steps

- [x] **6.1 — Update `docs/py/ga/expression/usage.md`**
  - Adjust the "addition/subtraction" section's note (`inv` requires a single
    linear term) to state that `AffineExpression` now supports `lstsq`/`svd`/
    `inv` when the sum reduces to a single linear map in one remaining variable.
  - Optionally extend the Inverse/`lstsq`/`svd` sections to mention the same
    methods apply to such an `AffineExpression`.

- [x] **6.2 — Append a Bug Fixes bullet to the branch changelog**
  - In `docs/changelog/2026/09/11_fix-jupyter.md`, add a `- **Headline** —`
    bullet for the `AffineExpression` counting-axis reduction + linear-solve
    support, wrapping at ~80 columns (per `dev/workflows/changelog.md`).  Do not
    touch `docs/changelog/index.md` (that entry is added at PR time).

## Validation

`uv run mkdocs build --strict`

## Notes

- Keep the changelog's existing `# Changes since version 2.2.0` title.
- The public API change is additive (new methods on an existing class); no new
  top-level exports, so `docs/py/ga/expression/index.md` needs no structural
  change.
