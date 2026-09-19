# Phase 6 — User docs + changelog + full validation

## Goal

Document the new public API (`BladeMask.ids_outside`, `Expression.compile`,
`AffineExpression.compile`, multilinear `AffineExpression.get_tensor`) in the
authoritative docs, add the branch changelog, and run the full validation gate.

## Files

- Edit: `docs/py/ga/expression/usage.md`
- Edit: `docs/py/ga/expression/index.md` (mention `compile`)
- Edit: `docs/py/ga/tensors/mvtensor.md` (note multilinear `get_tensor` shape)
- New: `docs/changelog/2026/09/DD_feat-expression-speed.md` (see
  `dev/workflows/changelog.md` for exact naming/title rules)

## Steps

- [x] **6.1 — Document `compile()` and the automatic fast path**
  - Add a `## Compiling an expression for fast repeated evaluation` section to
    `usage.md`: `compiled = expr.compile()`; semantics == `__call__` for
    fully-bound `MV`/scalar bindings; `AffineExpression.compile()`; the note
    that `__call__`/`evaluate` already use the same plan automatically, so
    `compile()` is only needed when you want to hold the callable explicitly.

- [x] **6.2 — Document multilinear `get_tensor()`**
  - Update the `## Named bases and get_tensor()/get_array()` section: state that
    `AffineExpression.get_tensor()` supports one variable appearing `k >= 1`
    times per term (rank `1 + k`), and show the quadratic
    `np.einsum("ijk,j,k->i")` contraction. Keep the single-linear-map wording
    for `lstsq`/`svd`/`inv` unchanged.

- [x] **6.3 — Note `ids_outside`**
  - Add a one-line mention of `BladeMask.ids_outside` in the blade-mask docs
    (`docs/py/ga/blade-mask/index.md`) as the cheap membership-diff helper, and
    reference it from the expression validation note.

- [x] **6.4 — Changelog**
  - Create `docs/changelog/2026/09/DD_expression-compile-multilinear.md` per
    `dev/workflows/changelog.md` (determine the title with
    `uv run python tools/last-release.py`; use `# Changes since version …`).
  - Sections: `## New Features` (`Expression.compile` /
    `AffineExpression.compile` fast path; multilinear `AffineExpression.get_tensor`)
    and `## Bug Fixes`/`## Refactor` for the per-call overhead elimination.

- [x] **6.5 — Full validation**
  - `uv run pytest py/tests -q`
  - `uv run ruff check py/pytanga py/tests/expression py/tests/blade_mask`
  - `uv run ty check py/pytanga`
  - `uv run python tools/generate-example-docs.py --check`
  - `uv run mkdocs build --strict`

## Validation

`uv run pytest py/tests -q && uv run ruff check py/pytanga py/tests/expression py/tests/blade_mask && uv run ty check py/pytanga && uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Notes

- Update `docs/dev/` only if the work changed documented architecture (it
  should not — it is additive). If any `docs/dev/architecture/` contract is
  touched, add a step here to update it.
- Changelog naming: on a feature branch use `DD_<branch-name>.md`; rename to the
  squashed-commit hash when opening the PR (see `dev/workflows/pull-request.md`).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
