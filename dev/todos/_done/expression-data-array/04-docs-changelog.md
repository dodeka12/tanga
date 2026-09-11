# Phase 4 — docs, benchmark, changelog

## Goal

Update the user-facing docs and benchmark to the `DataArray` API, and write the
branch changelog with a `## Breaking Changes` section.

## Files

- Edit: `docs/py/ga/expression/usage.md`
- Edit: `_input/test_expression_2.py`
- Edit: `dev/src/dev_expression_bench.py`
- Edit: `py/pytanga/expression/__init__.py` (docstring, if needed)
- Edit: `docs/changelog/2026-09-02_fix-expression.md` (append Breaking Changes)

## Steps

- [x] **4.1 — Update docs**
  - In `docs/py/ga/expression/usage.md`, replace `e(V1=[x0, x1])` and
    `e(V1=("n", [x0, x1]))` examples with `DataArray` equivalents and document
    the new accepted forms (single `MV`, `DataArray`, raw 1-D reduction sugar)
    plus `rename_axis`/`__call__` and the `_`/`*` reduction markers.

- [x] **4.2 — Update the local example**
  - In `_input/test_expression_2.py`, replace the manual
    `MVLabeledTensor`/`MVTensor`/tuple contractions with the `DataArray` DSL at
    the bottom, keeping the earlier manual section for reference.

- [x] **4.3 — Update the benchmark**
  - In `dev/src/dev_expression_bench.py`, switch the batched evaluation case to
    build a `DataArray` (from the list of MVs) instead of binding a list directly.

- [x] **4.4 — Write the changelog**
  - Append a `## Breaking Changes` section to
    `docs/changelog/2026-09-02_fix-expression.md` listing the removed binding
    forms (`list`/`tuple`, `(label, [mvs])`, `MVTensor`, `(array, specs)`) and
    point to `DataArray` as the replacement. Add a `## New Features` bullet for
    `DataArray` (construction, renaming, reduction markers).

- [x] **4.5 — Full validation**
  - Run the full suite, lint, and docs build.

## Validation

`uv run pytest; uv run ruff check py/pytanga/expression py/pytanga/tensor; uv run mkdocs build --strict`

## Notes

- The changelog title/index entry follow `dev/workflows/changelog.md` /
  `dev/workflows/pull-request.md`; the index update and hash rename happen at PR
  time.
