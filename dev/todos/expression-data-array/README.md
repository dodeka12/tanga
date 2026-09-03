# Expression `DataArray` + unified binding API — Overview

**Created:** 2026-09-02 | **Status:** Done | **Branch:** `fix/expression`

## Goal

Introduce a public `DataArray` data container and collapse the non-scalar
`Expression.__call__` / `AffineExpression.__call__` binding surface to a single
form: bind a variable (or reduce a counting axis) with either a single `MV` or a
`DataArray`. The ad-hoc `(array, specs)`, plain `MVTensor`, `list`/`tuple`-of-MVs,
and `(label, [mvs])` binding shapes are removed. A raw 1-D array/list remains as
a sum-only shorthand for counting-axis reduction.

## Background

- The branch already added array binding via `(array, specs)` and `MVTensor`, but
  that produces several overlapping ways to express the same thing. `DataArray`
  makes the labeled-data concept explicit and becomes the single recommended
  container.
- `DataArray` is a thin, user-facing wrapper over the existing spec concept:
  each axis is either a `BladeMask` (a blade axis) or a `str` (a counting-axis
  name, mask `None`, mode `"_"`).
- `AffineExpression` is a list of unmergeable `Expression` terms. Even after the
  input surface collapses to `MV`/`DataArray`, its `__call__` must still combine
  per-term results where one term returns a single `MV` and another returns a
  `list` (because a term that keeps a counting axis is materialised by
  `from_tensor` as a list). That broadcast logic is preserved.

## Decisions (confirmed)

- **Breaking change now**: the expression system has essentially no external
  users, so `list`/`tuple`-of-MVs, `(label, [mvs])`, plain `MVTensor`, and the
  `(array, specs)` tuple forms are removed from `__call__` (not deprecated).
- **Accepted value forms**:
  - variable binding: `MV` / `int` / `float`, or `DataArray` (one blade axis
    matching the variable mask, any number of counting axes).
  - counting-axis reduction: raw 1-D `np.ndarray`/`list` (sum sugar), or
    `DataArray` (all counting axes).
- **`DataArray` construction**:
  - `DataArray(array, masks=...)` where `array` is `np.ndarray`, a
    `list`/`tuple` of `MV`, or a `list`/`tuple` of scalars, and `masks` is a
    sequence of `BladeMask | str`.
  - A list of MVs is converted via `to_tensor` and reordered so the blade axis
    sits where its `BladeMask` appears in `masks`; it must have exactly one
    `BladeMask` and one `str` (ndim 2).
- **Renaming**: `rename_axis(old, new)` returns a new `DataArray`;
  `data(old=new, ...)` renames in place and returns `self`. Renames apply to
  counting-axis (`str`) specs only.
- **Markers**: in a counting-axis reduction, a spec `"_"` resolves to the binding
  key in element-wise (multiply/keep) mode and `"*"` in contract (sum) mode; a
  trailing `_` (`"name_"`) is element-wise. These are reduction-only shorthands
  so the user does not repeat the binding-key name.
- **1-D implicit key**: a 1-D `DataArray` in a reduction is always the binding
  key; its name is ignored except for the `_`/`*`/trailing-`_` marker.
- **Uniqueness**: `DataArray` rejects duplicate counting-axis names and more than
  one `_`/`*` marker at construction time.

### Fixed contract

```python
# py/pytanga/expression/_data_array.py  (exported as pytanga.expression.DataArray,
#                                         and as pytanga.DataArray)

class DataArray:
    def __init__(self, array, masks) -> None: ...
    @property
    def array(self) -> np.ndarray: ...
    @property
    def masks(self) -> tuple[BladeMask | str, ...]: ...
    @property
    def ndim(self) -> int: ...
    @property
    def shape(self) -> tuple[int, ...]: ...
    def rename_axis(self, old: str, new: str) -> DataArray: ...
    def __call__(self, **renames: str) -> DataArray: ...   # in-place, returns self

# accepted by Expression.__call__ / AffineExpression.__call__:
#   variable binding:   expr(v=mv)             # MV / int / float
#                       expr(x=data)           # DataArray (blade axis matched by mask)
#   counting reduction: expr(pnt_idx=scalars)  # 1-D np.ndarray / list  -> sum
#                       expr(pnt_idx=data)     # DataArray (all counting axes)

data = DataArray(points, masks=("pnt_idx", point_mask))
data = DataArray([mv1, mv2], masks=("pnt_idx", point_mask))
scalar = DataArray(scalars, masks=("n",))
scalar2d = DataArray(scalars2d, masks=("n", "m"))

contract = expr(x_pnt=data)
contract(pnt_idx=scalar)                                  # sum (1-D implicit key)
contract(pnt_idx=scalar(n="_"))                           # multiply, keep
contract(pnt_idx=scalar2d(n="*", m="m_idx"))              # sum key, keep m_idx
contract(pnt_idx=scalar2d(n="_", m="m_idx"))              # multiply key, keep m_idx
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-data-array.md](./01-data-array.md) | Add the `DataArray` class, exports, and unit tests. |
| 2 | [02-expression-input-refactor.md](./02-expression-input-refactor.md) | Refactor `Expression`/`AffineExpression` to the unified binding API and migrate tests. |
| 3 | [03-example-script.md](./03-example-script.md) | Add a runnable `py/examples/` demo of expressions, variables, and DataArrays. |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Update docs/benchmark and write the branch changelog (Breaking Changes). |

## Testing as you go

- DataArray tests: `uv run pytest py/tests/tensor/ -q`
- Expression tests: `uv run pytest py/tests/expression/ -q`
- Full suite (final phase): `uv run pytest`
- Lint: `uv run ruff check py/pytanga/tensor py/pytanga/expression`
- Docs build (final phase): `uv run mkdocs build --strict`

## Non-goals

- No `MVTensor(masks=(...str...))` string-mask syntax (unchanged from before).
- No `DataArray` slicing/arithmetic — it is a data + axis-spec container plus
  rename helpers.
- No static type-checker gate (type hints are validated by import/pytest/ruff).
