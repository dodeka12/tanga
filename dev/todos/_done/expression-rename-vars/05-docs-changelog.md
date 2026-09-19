# Phase 5 — Documentation, example, and changelog

## Goal

Document the new API, add a runnable example, and record the feature in the
branch changelog.

## Files

- Edit: `docs/py/ga/expression/usage.md`
- Edit: `docs/py/ga/expression/index.md`
- New: `py/examples/ga/expression/rename_unify_variables.py`
- Edit: `docs/changelog/2026/09/15_feat-viz-detached-subtree.md`

## Steps

- [x] **5.1 — User docs**
  - Add a "Renaming and unifying variables" section to
    `docs/py/ga/expression/usage.md` covering `bind(X=X)`, `rename_var`, and
    `unify`, including the "target mask must equal the source mask" caveat and
    the list-returning `unify` semantics.

- [x] **5.2 — Index mention**
  - Add a one-line pointer in `docs/py/ga/expression/index.md` to the new usage
    section.

- [x] **5.3 — Example + regenerate**
  - Add `py/examples/ga/expression/rename_unify_variables.py` (license header +
    module docstring with a one-line description, `Run with:`, and `Keywords:`
    per `dev/workflows/example-docs.md`); then run
    `uv run python tools/generate-example-docs.py` and its `--check`.

- [x] **5.4 — Changelog**
  - Append a "New Features" bullet to
    `docs/changelog/2026/09/15_feat-viz-detached-subtree.md` (per
    `dev/workflows/changelog.md`); do not touch `docs/changelog/index.md`.

- [x] **5.5 — Full validation**
  - Run the full gate: pytest, ruff, ty, and the example-docs drift check.

## Validation

`uv run pytest py/tests -q && uv run ruff check py/pytanga/expression py/tests/expression/test_rename.py && uv run ty check py/pytanga/expression && uv run python tools/generate-example-docs.py --check`

## Notes

- No developer-doc update is required: the change is additive and does not alter
  the documented architecture.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
