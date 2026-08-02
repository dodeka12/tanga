# Phase 2 — C++ Binding Additions

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing any step in this plan.  
> In particular: the [C++ Coding Style Guide](../../../docs/dev/guides/cpp-coding-style-guide.md).  
> Also review any relevant architecture docs, use-case examples, and best practice documentation found there.

## Goal

Extend `py/pytanga/_template.cpp` and `py/pytanga/_codegen.py` with the
free functions that `MVSolver` will call.  All new C++ code is added to the
existing per-algebra binding module; no new shared library is introduced.

By the end of this phase every compiled binding exposes the new functions, and
rebuilding an existing algebra (by deleting its cache entry) produces a module
that includes them.

---

## Steps

### 2.1 — Add headers to `_template.cpp` ✓

Add to the `#include` block in `_template.cpp`:

```cpp
#include <pybind11/numpy.h>
#include "Tan.GA/Matrix_MapToBladeMask.h"
#include "Tan.Math/Matrix.Algo.GE.h"
```

`pybind11/numpy.h` enables `py::array_t<CTYPE>` for numpy interop.
`Matrix_MapToBladeMask.h` is header-only (template library); no new `.cpp`
source needs to be added to the CMake target.
`Matrix.Algo.GE.h` is likewise header-only.

Add a `{MATRIX_DEF}` placeholder token in the module body, after the existing
product definitions.

**Tests:** Verify that a freshly compiled float64 and int64 binding both load
without error (i.e., compilation succeeds).

### 2.2 — Blade-mask functions (float and integer, identical) ✓

Add to `_codegen.py` a `_matrix_common_def()` fragment included for all
dtypes. Bind the following free functions:

```
blade_mask(mv, only_nonzero=True) → list[int]
```
Calls `GA::EvalBladeMask`. Iterates `mv`'s blades; inserts ids into a
`std::vector<uint32_t>` in the same order as `CBladeMask` (ascending blade id).

```
product_blade_mask_gp(mv, col_ids, left_to_right=True, complete=False) → list[int]
product_blade_mask_ip(mv, col_ids, left_to_right=True, complete=False) → list[int]
product_blade_mask_op(mv, col_ids, left_to_right=True, complete=False) → list[int]
```
Each constructs a `CBladeMask` from `col_ids`, calls the corresponding
`GA::EvalProductBladeMask_GP/IP/OP`, then converts the result mask to
`std::vector<uint32_t>`.

**Tests:** For a known vector-grade multivector in G(3,0), verify that
`blade_mask` returns the expected ids. Verify that `product_blade_mask_gp`
with `complete=True` returns the closure of those ids under repeated
left-multiplication.

### 2.3 — Matrix conversion functions (all dtypes) ✓

Add to the common fragment:

```
to_matrix(mv, blade_ids) → np.ndarray   shape (n, 1), dtype=CTYPE
```
Constructs a `CBladeMask` from `blade_ids`, calls `GA::ToMatrix`, copies the
`CMatrix<CTYPE>` column into a `py::array_t<CTYPE>` of shape `(n, 1)`.

```
from_matrix(arr, blade_ids) → DynMV
```
Accepts a `py::array_t<CTYPE>` of shape `(n, 1)`, constructs a
`CMatrix<CTYPE>`, calls `GA::ToMultivector`. Raises if `arr.shape[0] !=
len(blade_ids)`.

**Tests:** Round-trip: construct an MV, call `to_matrix`, call `from_matrix`,
verify the resulting MV matches the original via `to_dict()`.

### 2.4 — Product-matrix functions (all dtypes) ✓

Add to the common fragment:

```
product_matrix_gp(mv, col_ids, row_ids, left_to_right=True) → np.ndarray
product_matrix_ip(mv, col_ids, row_ids, left_to_right=True) → np.ndarray
product_matrix_op(mv, col_ids, row_ids, left_to_right=True) → np.ndarray
```
Each constructs two `CBladeMask` objects from `col_ids` and `row_ids`, calls
`GA::EvalProductMatrix_GP/IP/OP` (2-mask overload), copies the resulting
`CMatrix<CTYPE>` into a `py::array_t<CTYPE>` of shape `(|row_ids|, |col_ids|)`.

```
product_matrix_gp_masked(mv, a_ids, col_ids, row_ids, left_to_right=True) → np.ndarray
product_matrix_ip_masked(mv, a_ids, col_ids, row_ids, left_to_right=True) → np.ndarray
product_matrix_op_masked(mv, a_ids, col_ids, row_ids, left_to_right=True) → np.ndarray
```
Same but uses the 3-mask overload with `xMaskA` built from `a_ids`.

```
product_matrix_array_gp(mvs, col_ids, row_ids, left_to_right=True) → np.ndarray
product_matrix_array_ip(mvs, col_ids, row_ids, left_to_right=True) → np.ndarray
product_matrix_array_op(mvs, col_ids, row_ids, left_to_right=True) → np.ndarray
```
Accepts a `std::vector<TDynMV>` (auto-converted from a Python list of `DynMV`
objects by pybind11 STL support). Calls `GA::EvalProductMatrixArray_GP/IP/OP`.
All elements of the list must have the same internal blade structure as
`mvs[0]`; this precondition is documented but not checked in C++.

**Tests:** For A = `1·e1 - 2·e2` in G(3,0), verify that `product_matrix_gp`
returns the expected 2×2 matrix for known `col_ids` and `row_ids`.

### 2.5 — Modular-integer solve binding (integer dtypes only) ✓

Add to `_codegen.py` a separate `_matrix_int_def(ctype)` fragment. Bind:

```
solve_mod(wA, wY, col_ids, row_ids, modulus) → DynMV
```

Implementation:
1. Build `xMaskB` from `col_ids`, `xMaskC` from `row_ids`.
2. Call `GA::EvalProductMatrix_GP` (2-mask) → `CMatrix<CTYPE> matA`.
3. Call `GA::ToMatrix(matY, wY, xMaskC)` → `CMatrix<CTYPE> matY`.
4. Build augmented matrix, call `GaussElim(matAug, TCong(modulus))`.
5. On failure raise `std::runtime_error("System has no unique solution")`.
6. Extract solution column, call `GA::ToMultivector` → `TDynMV`.

Float dtypes do **not** get this binding; float solving is done in Python with
numpy.

**Tests:** In G(3,0) with int64 and modulus 97, verify that
`solve_mod(A, scalar_1, col_ids, row_ids, 97)` returns the modular inverse
of A (cross-check against the existing `inv(A, 97)` binding).
