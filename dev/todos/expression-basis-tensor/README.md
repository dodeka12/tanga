# Expression basis-aware `get_tensor()` and named `BladeMask` bases — Overview

**Created:** 2026-09-18 | **Status:** Done | **Branch:** `feat/expression-matrix`

## Goal

Let `BladeMask` carry a *named basis* (ordered composed directions such as
`einf = ep + em` or `e1∧e∞ = e14 + e15`) alongside its raw blade ids, and expose
`Expression.get_tensor()` / `AffineExpression.get_tensor()` returning the raw
`MVTensor` plus `MVTensor.get_array()` to recombine it into named bases.  This
replaces the "evaluate once per canonical basis blade" pattern in
`AffineExpression._variable_matrix()` with a tensor-native combination, and lets
`mask_for(TwistBivector)` report its 6 *physical* DOF directions
(`e12, e13, e23, e1∧e∞, e2∧e∞, e3∧e∞`) over its 9 raw twist blades so callers get
a 6-column operator matrix without hand-written recombination.

## Architecture (short)

- **`BladeMask`** keeps raw identity (`_ids`, `_index`, `len`, `__eq__`) unchanged
  and gains an optional named basis `_basis: tuple[tuple[str, MV], ...] | None`
  (an ordered list of ``(name, MV)`` directions).  `basis_vectors` / `basis_names`
  return the directions, falling back to the raw blades in `ids` order when
  `_basis is None`.  `with_basis(...)` attaches directions (reduced sets allowed);
  `basis_matrix(...)` returns the raw→named change-of-basis matrix.
- **Auto named basis on construction** — `BladeMask.__init__` attaches the
  algebra's display basis (`Algebra._get_display_basis()`, e.g. `einf`/`eo` for
  N3) *iff* the display directions whose support ⊆ the raw ids exactly cover the
  raw ids; otherwise the mask is raw-only.  String parsing passes the algebra's
  composite `named_basis`, so `BladeMask(N3, "e1 + einf")` expands `einf` to raw
  `{8, 16}`.
- **No `MVTensor` change** — the named directions are consumed only by `get_tensor()`
  and display; `get_tensor()` returns a plain `np.ndarray`, so `MVTensor` axis labels
  stay `BladeMask | None`.
- **Geometry** — a per-algebra `basis_for(basis, typ)` hook (mirroring
  `create_operator`) supplies a type-specific named basis; `mask.py::mask_for`
  attaches it via `with_basis`.  `basis_for_twist_bivector` (N3) returns the 6
  physical DOF directions.
- **`get_tensor()` / `get_array()`** — `Expression` / `AffineExpression`
  `get_tensor()` returns the raw `MVTensor`; `MVTensor.get_array()` recombines
  each axis into its named basis and returns a plain `np.ndarray`.  Math:

  ```
  T_named = C_out @ T_raw @ B_var1 @ B_var2 @ …
  B_var   = to_matrix(var_directions, mask=var_mask).data        # |var| × n_var
  C_out   = np.linalg.pinv(to_matrix(out_directions, mask=out_mask).data)  # n_out × |out|
  ```

## Decisions (confirmed)

- **No separate `Basis` type.**  The named basis lives directly on `BladeMask` as
  an ordered tuple of ``(name, MV)`` directions — no `BladeMask ↔ Basis` recursion.
- **Raw identity unchanged.** `BladeMask` `ids` / `len` / `__eq__` / tensor-axis
  alignment stay keyed to raw ids; the named directions are metadata, and
  `get_tensor()` returns a plain `np.ndarray` (so `MVTensor` is untouched).
- **Two sources of named basis** — (1) the algebra display basis auto-attached on
  construction; (2) a geometry-type-specific basis attached by `mask_for` via the
  per-algebra hook, overriding (1).
- **`TwistBivector` basis = the 6 physical DOF**, not the 9-element display basis:
  `e12, e13, e23, e1∧e∞, e2∧e∞, e3∧e∞`.
- **`get_tensor()` returns the raw `MVTensor`** (`get_array()` recombines), not a
  separate `matrix()`.  `lstsq` / `svd` / `inv` keep using the private raw
  `_variable_matrix()`.
- **`union`** is forgiving (merge named directions when both have a basis, else
  raw union).  **`intersection`** is strict by default (raises when names cannot
  be aligned), with `discard_basis=True` to fall back to the raw-id intersection.
- **No C++ changes.** `GA::CBladeMask` and the `Tan.GA` core are untouched.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-basis-blademask-core.md](./01-basis-blademask-core.md) | `BladeMask` named basis (`basis_vectors`/`basis_names`/`with_basis`/`basis_matrix`, auto display basis, string parse) |
| 2 | [02-blademask-union-intersection.md](./02-blademask-union-intersection.md) | Basis-aware `union` / `intersection(discard_basis=…)` |
| 3 | [03-geometry-mask-basis.md](./03-geometry-mask-basis.md) | Per-algebra `basis_for` + `mask_for` attaches `TwistBivector` 6-D basis |
| 4 | [04-expression-tensor.md](./04-expression-tensor.md) | Public `Expression.get_tensor()` / `AffineExpression.get_tensor()` (returns `np.ndarray`) |
| 5 | [05-example-scripts.md](./05-example-scripts.md) | Example scripts for the named basis + `get_tensor()` |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Docs + changelog + dev-docs update + full validation |

## Testing as you go

- `uv run pytest py/tests/blade_mask/ -q`
- `uv run pytest py/tests/tensor/ -q`
- `uv run pytest py/tests/geometry/test_operators.py py/tests/geometry/test_geometry_n3.py py/tests/geometry/test_geometry_mask.py -q`
- `uv run pytest py/tests/expression/ -q`
- `uv run python py/examples/ga/blade_mask/named_basis.py`
- `uv run python py/examples/ga/expression/tensor_named_basis.py`
- `uv run python tools/generate-example-docs.py --check`
- `uv run ruff check py/pytanga/blade_mask py/pytanga/tensor py/pytanga/expression py/pytanga/geometry py/tests/blade_mask py/tests/tensor py/tests/expression py/tests/geometry`
- `uv run ty check`
- `uv run mkdocs build --strict`

## Non-goals

- No C++ `GA` / `CBladeMask` / storage-core changes.
- No separate `Basis` type or `MVTensor` axis-label change.
- No general multi-variable `AffineExpression.get_tensor()` beyond the
  single-variable / appears-once-per-term linear case in this plan (the wrench
  case); multi-variable affine recombination is a follow-up.
- `lstsq` / `svd` / `inv` remain raw-blade based (unchanged); solving/inverting in
  a reduced named basis is out of scope.
- No visualization or analysis support for the composed basis.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
