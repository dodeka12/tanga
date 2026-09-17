# Phase 6 — Docs + changelog

## Goal

Document `project_onto` on expressions, the `BladeMask` empty construction, and
the new `TwistBivector` operator, and record the work in the branch changelog.

## Files

- Edit: `docs/py/ga/blade-mask/construction.md`
- Edit: `docs/py/ga/expression/usage.md`
- Edit: `docs/py/ga/geometry/operators.md`
- Edit: `docs/changelog/2026/09/17_fix-expression-unify.md`

## Steps

- [x] **6.1 — `BladeMask` docs**
  - In `docs/py/ga/blade-mask/construction.md`, document `BladeMask(alg)` (full)
    vs `BladeMask(alg, [])` (empty).

- [x] **6.2 — expression docs**
  - In `docs/py/ga/expression/usage.md`, add a short `project_onto` note:
    restrict an expression (or affine sum) to a blade set (`MV` → non-zero
    blades, `BladeMask` → exact id membership); note the disjoint result is zero.

- [x] **6.3 — geometry docs**
  - In `docs/py/ga/geometry/operators.md`, add a `TwistBivector` entry (N3-only,
    rotor + translator → motor → projected to the twist bivector mask; not
    visualizable).

- [x] **6.4 — Changelog**
  - Append to `docs/changelog/2026/09/17_fix-expression-unify.md`:
    - `## New Features` — `Expression` / `AffineExpression.project_onto`, module
      `project_onto`, the N3 Euclidean projection example, and the `TwistBivector`
      geometry operator.
    - `## Bug Fixes` — `BladeMask(alg, [])` now returns an empty mask (and
      `intersection` / `union` / `from_mv` handle the empty case).
  - Leave `docs/changelog/index.md` for PR time (per
    `dev/workflows/pull-request.md`).

- [x] **6.5 — Full validation**
  - Run the full targeted suite, lint, `ty`, example, example-docs, and mkdocs.

## Validation

`uv run pytest py/tests/blade_mask py/tests/expression py/tests/geometry -q && uv run ruff check py/pytanga py/tests/blade_mask py/tests/expression py/tests/geometry && uv run ty check && uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Notes

- The `rename_var` bugfix from earlier on this branch already has a bullet in the
  changelog; append the new bullets rather than recreating the file.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
