# Phase 3 — Algebra core (algebra / blade_mask / basis / codegen / expression / matrix / solver / tensor)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `type-system-and-storage.md` and `geometry-module-layering.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture.  If this work introduces or changes architecture, update the
> developer docs.

## Goal

Annotate the GA compute layer (34 untyped functions).  These packages import
each other (`algebra ↔ blade_mask`) and are imported by `geometry`/`quadric`, so
cross-references use `TYPE_CHECKING` + string annotations.

## Files

- Edit: `py/pytanga/algebra/*.py`
- Edit: `py/pytanga/blade_mask/*.py`
- Edit: `py/pytanga/basis/*.py`
- Edit: `py/pytanga/codegen/*.py`
- Edit: `py/pytanga/expression/*.py`
- Edit: `py/pytanga/matrix/*.py`
- Edit: `py/pytanga/solver/solve.py`
- Edit: `py/pytanga/tensor/*.py`

## Steps

- [x] **3.0 — Typed Protocol for the C++ binding**
  - New `py/pytanga/codegen/_binding.py`: `DynMVBinding` + `AlgebraBinding`
    protocols transcribed from `py/pytanga/_template.cpp` and the
    `codegen/*_def()` snippets (the authoritative signatures).
  - `get_or_build(...) -> AlgebraBinding`; `Algebra._mod: AlgebraBinding`;
    `MV.__init__(impl: DynMVBinding, ...)`.
  - Removes the `_mod`-driven `unsound-return-statement` class with **no
    suppressions** (algebra + blade_mask: 29 → 17 diagnostics) and benefits
    every later phase.
- [x] **3.1 — `algebra` + `blade_mask` (4)**
  - Finish `py/pytanga/algebra/_mv.py` (`MV` dunder math, `grade`, `is_grade`,
    `scalar`, `normalized`, `show`) — reuse `MVLike` and `BladeMask` aliases.
  - `py/pytanga/blade_mask/_mask.py` / `_dispatch.py` / `predict.py`: annotate
    `product_blade_mask`, `inverse_blade_mask`, and the mask dispatch helpers
    (`-> BladeMask`).  Use `TYPE_CHECKING` for `Algebra` / `MV` (already the
    pattern here).
- [x] **3.2 — `basis` (10)**
  - The `BasisE2/E3/P2/P3/N2/N3/PGA2/PGA3` `__init__`s are already typed; annotate
    the remaining blade-member helpers / property methods (`E123: int`, etc. are
    class attributes and stay as-is).
- [x] **3.3 — `codegen` + `expression` (7)**
  - `codegen/*.py`: annotate the product-matrix/tensor builders and blade-mask
    generators (`-> np.ndarray`, `-> BladeMask`, `-> str`).
  - `expression/_expression.py`, `_variable.py`, `_labels.py`, `_data_array.py`:
    annotate `Expression`, `Variable`, and `DataArray` methods.
- [x] **3.4a — `matrix`**
  - `matrix/convert.py`, `product.py`, `_dispatch.py`, `_data.py`,
    `_product_data.py`: annotate `to_matrix`, `product_matrix`,
    `_resolve_alg`, and the `MVMatrix`/`MVProductMatrix` dataclass helpers;
    `cast`/`int(...)` the untyped numpy `.shape` results; disambiguate the
    `mvs`/`mv` locals in `product_matrix`.
- [x] **3.4b — `solver` + `tensor`** (ty: solver 9, tensor 26 remaining)
  - `solver/solve.py`: narrow the `MVLike | list[MVLike]` unions before
    `len()`/iteration/`_as_mv`; `cast` the `from_matrix` results (`MV | list`).
  - `tensor/*.py`: annotate `to_tensor`, `MVTensor`, `MVLabeledTensor` methods;
    fix the `str | int` (``AxisName``) vs `str` mismatches in `_labeled.py`;
    `cast` the untyped numpy `.shape`/`.strides` results; widen the
    `BladeMask | None` accesses in `convert.py`.

- [x] **3.5 — Resolve the algebra-core ty diagnostics**
  - `uv run ty check py/pytanga/algebra py/pytanga/blade_mask py/pytanga/basis py/pytanga/codegen py/pytanga/expression py/pytanga/matrix py/pytanga/solver py/pytanga/tensor` → 0 (baseline: 151 diagnostics).
  - Fix each (real bug / annotation inaccuracy) or add
    `# ty: ignore[<rule>]  # <reason>` for verified false positives.

## Validation

`uv run ruff check --select ANN --ignore ANN401 py/pytanga/algebra py/pytanga/blade_mask py/pytanga/basis py/pytanga/codegen py/pytanga/expression py/pytanga/matrix py/pytanga/solver py/pytanga/tensor` → 0
`uv run ty check` on the same paths → 0
`uv run pytest py/tests/algebra py/tests/basis py/tests/expression -q`

## Notes

- `algebra` and `blade_mask` import each other; keep any new imports under
  `TYPE_CHECKING` (or lazy inside functions) exactly as the existing code does.
- `MVLike = Union["MV", float, int, str]` already exists — use it for
  "MV-or-scalar-or-string" parameters; use bare `MV` for "must be a multivector".
- Do not annotate blade-id class attributes (`E123: int = 7`) — they are already
  annotated; the ruff ANN output will not flag them.
