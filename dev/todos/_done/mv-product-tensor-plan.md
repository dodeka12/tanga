# MV Product Tensor — Implementation Plan

Expose the **product tensor** — the 3D encoding of a GA product's Cayley table — as both a C++ function and a pytanga Python class. This differs from the existing `Matrix_Product.h` which produces a **2D product matrix** (already contracted with a specific multivector's coefficients). The product tensor is the raw `O^k_{ij}`: it depends only on blade masks (and the algebra signature) and is independent of any specific MV.

## Mathematical Background

For any binary GA operation ∘ ∈ {GP, IP, OP}, the coefficients satisfy:

```
c^k = Σ_{i,j}  a^i · b^j · O^k_{ij}
```

where `O^k_{ij}` is the **product tensor**: ±1 when blA[i] ∘ blB[j] → blC[k], and 0 otherwise. This tensor encodes the entire Cayley table of the algebra for the restricted blade subspaces defined by the masks.

In Python, contraction of this tensor with MV data is done via `numpy.einsum`:

```python
# Contract along A-axis and B-axis:
C_vec = np.einsum('kij,i,j->k', O_tensor, A_coeffs, B_coeffs)
```

## Relationship to Existing Code

| Concept | Existing (Matrix_Product.h) | New (Product Tensor) |
|---------|----------------------------|---------------------|
| Output | 2D matrix `M^k_j` (contracted with A) | 3D tensor `O^k_{ij}` (no contraction) |
| Input | Requires a specific multivector A | Requires only blade masks |
| Use case | Build linear system for solving A∘X=Y | General-purpose GA multiplication via einsum |
| Involution | Supported on operands | Supported on operand axes |

The existing 2D product matrix is a partial contraction: `M^k_j = Σ_i a^i · O^k_{ij}`. The new 3D tensor is the uncontracted `O^k_{ij}`.

---

## Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `cpp/Tan.Math/Tensor.h` | **New** | General-purpose rank-agnostic `CTensor<T>` class (like `CMatrix` but for N-D) |
| `cpp/Tan.GA/Tensor_Product.h` | **New** | C++ templates for building the 3D product tensor from blade masks, returns `CTensor<T>` |
| `py/pytanga/codegen/_tensor.py` | **New** | Codegen fragment for GP/IP/OP product tensor bindings |
| `py/pytanga/mv_product_tensor.py` | **New** | Python dataclass wrapping the 3D tensor as numpy array |
| `py/pytanga/_template.cpp` | Modify | Add `#include "Tan.Math/Tensor.h"` and placeholder `{PRODUCT_TENSOR_DEF}` |
| `py/pytanga/codegen/_generator.py` | Modify | Wire `{PRODUCT_TENSOR_DEF}` placeholder replacement in `generate()` |
| `py/pytanga/__init__.py` | Modify | Export new class |
| `py/pytanga/solver/tensor_product.py` | **New** | Free function `product_tensor(alg, ...)` for building product tensors |
| `py/tests/test_product_tensor.py` | **New** | Tests for tensor correctness and einsum contraction |
| `docs/cpp/tensor-product.md` | **New** | C++ developer documentation for `CTensor<T>` and `Tensor_Product.h` |
| `docs/py/product-tensor.md` | **New** | Python user documentation for `MVProductTensor` and `product_tensor()` |

### Docstring Requirements

Every public API element in this plan **must** carry an inline docstring / doxygen comment.  This applies to:

| Element | Location | Documentation Style |
|---------|----------|---------------------|
| `CTensor<T>` class and all its public methods | `cpp/Tan.Math/Tensor.h` | Doxygen `\\\ ` comments |
| `_EvalProductTensor`, `EvalProductTensor_GP/IP/OP` | `cpp/Tan.GA/Tensor_Product.h` | Doxygen `\\\ ` comments |
| `product_tensor_def()` Python fragment generator | `py/pytanga/codegen/_tensor.py` | Python docstring |
| `MVProductTensor` class and all its public methods | `py/pytanga/mv_product_tensor.py` | Python docstrings (dataclass fields + methods) |
| `product_tensor()` free function | `py/pytanga/solver/tensor_product.py` | Python docstring |
| User-facing docs | `docs/cpp/tensor-product.md`, `docs/py/product-tensor.md` | Markdown |

Public API interfaces without documentation will be considered incomplete.

---

## Phase 0: C++ Rank-Agnostic Tensor — `CTensor<T>`

### Overview

The existing `CMatrix<T>` inherits from `CArray<T>` and enforces 2D (row/col) semantics. For tensor-valued returns, we need a type that supports arbitrary rank while still inheriting the flat storage, strides, and element access provided by `CArray<T>`.

Create `cpp/Tan.Math/Tensor.h` with a `CTensor<T>` class that mirrors `CMatrix<T>` but for N dimensions.

### Background: CArray

`CArray<T>` (from `Tan.Core/Array.h`) already supports N-dimensional arrays:
- **Storage**: Flat `std::vector<T>` with a size vector and stride vector
- **Access**: `operator()(const TIdxVec&)` takes a vector of indices
- **Shape**: `GetSize()` returns the size vector, `GetDimension()` returns the rank
- **Iteration**: Stride-based iterators over the flat storage

`CMatrix<T>` inherits from `CArray<T>` and adds:
- Fixed 2D semantics (`m_nRowDimIdx=0`, `m_nColDimIdx=1`)
- Convenient `operator()(size_t row, size_t col)` access
- `GetRowCount()`, `GetColCount()`, `Resize(nr, nc)`, `SetSize(nr, nc)`
- `Zero()`, `Transpose()`, `AppendCols()`, `GetSubMatrix()`, etc.

### Step 0.1 — Create `cpp/Tan.Math/Tensor.h`

```cpp
// (Apache 2.0 license header matching Tan.Math/Matrix.h)

#pragma once

#include "Tan.Core/Defines.h"
#include "Tan.Core/Array.h"
#include "ValuePrecision.h"

namespace Tan
{
    /// Rank-agnostic tensor.
    ///
    /// Provides an N-dimensional container with the same storage and precision
    /// semantics as CMatrix<T> but without a fixed 2‑D shape.  Use when a
    /// function must return a 3‑D product tensor, a vector of matrices, etc.
    ///
    /// CTensor<T> inherits from CArray<T> and CValuePrecision<T> (same as CMatrix<T>).
    /// Unlike CMatrix<T>, CTensor<T> does NOT pin the first two axes as "row" / "col".
    template<class _TValue>
    class CTensor : public CArray<_TValue>, public CValuePrecision<_TValue>
    {
    public:
        typedef _TValue TValue;
        typedef CTensor<TValue> TThis;
        typedef CArray<TValue> TArray;
        typedef typename TArray::TIterator TIterator;
        typedef typename TArray::TConstIterator TConstIterator;
        typedef typename TArray::TIdx TIdx;
        typedef typename TArray::TIdxVec TIdxVec;
        typedef typename TArray::TSizeVec TSizeVec;
        typedef CValuePrecision<_TValue> TValPrec;

    public:
        CTensor() = default;
        
        CTensor(TValue fPrec) : CValuePrecision<TValue>(fPrec)
        {
            TValPrec::SetValuePrecision(fPrec);
        }

        CTensor(TThis&& xT) = default;
        TThis& operator=(TThis&& xT) = default;

        CTensor(const TThis& xT) = default;
        TThis& operator=(const TThis& xT) = default;

        // --- Dimension --------------------------------------------------

        /// Number of axes (rank).
        size_t GetDimension() const { return TArray::GetDimension(); }

        /// Size along axis `uDim` (zero-based).
        size_t GetDimSize(size_t uDim) const
        {
            return TArray::GetSize()[uDim];
        }

        /// Full size vector.
        const TSizeVec& GetSizes() const { return TArray::GetSize(); }

        /// Total number of elements (product of all dimension sizes).
        size_t GetTotalSize() const { return TArray::GetTotalSize(); }

        // --- Resize -----------------------------------------------------

        /// Resize to N dimensions, preserving existing elements where possible.
        void SetSize(const TSizeVec& vecSize)
        {
            TArray::SetSize(vecSize);
        }

        /// Resize to a given shape (convenience: wraps size vector).
        template<typename... TDimSizes>
        void SetSize(TDimSizes... sizes)
        {
            TArray::SetSize(TSizeVec{ static_cast<size_t>(sizes)... });
        }

        /// Resize without preserving data (all elements zeroed after resize).
        void Resize(const TSizeVec& vecSize)
        {
            if (TArray::GetTotalSize() == 0)
                TArray::SetSize(vecSize);
            else
                TArray::Resize(vecSize);
        }

        template<typename... TDimSizes>
        void Resize(TDimSizes... sizes)
        {
            Resize(TSizeVec{ static_cast<size_t>(sizes)... });
        }

        // --- Element access ---------------------------------------------

        /// Access element by index vector (from CArray).
        using CArray<TValue>::operator();

        /// Zero all elements.
        void Zero()
        {
            std::fill(TArray::GetData(), TArray::GetData() + TArray::GetTotalSize(), TValue(0));
        }
    };
} // namespace Tan
```

Key design points:
- Inherits from `CArray<T>` and `CValuePrecision<T>` — same base classes as `CMatrix<T>`
- Does **not** pin first two axes as "row"/"col" — rank is variable
- Provides `GetDimension()`, `GetDimSize(i)`, `GetSizes()` for introspection
- `SetSize(...)` and `Resize(...)` accept variadic sizes for convenience or a `TSizeVec` for programmatic use
- `Zero()` is a convenience method (mirrors `CMatrix::Zero()`)
- Does **not** include matrix-specific methods (`Transpose`, `AppendCols`, `GetSubMatrix`, etc.) — those belong on `CMatrix`
- Stored in `cpp/Tan.Math/Tensor.h` alongside `Matrix.h`
- Follows the same license header and code style as `Matrix.h`

### Step 0.2 — Add to `Tan.Math/CMakeLists.txt`

No changes needed if `Tan.Math/CMakeLists.txt` uses a glob or includes all `.h` files. Verify during implementation; if explicit file lists are used, add `Tensor.h`.

---

## Phase 1: C++ Template — `Tensor_Product.h`

### Overview

Create `cpp/Tan.GA/Tensor_Product.h` with template functions that build a 3D product tensor from blade masks. The tensor layout is `(k, i, j)` where:
- `k` (axis 0) = output blade index in `xMaskC`
- `i` (axis 1) = left operand blade index in `xMaskA`  
- `j` (axis 2) = right operand blade index in `xMaskB`

The functions return `CTensor<TValue>` (from Phase 0), providing a properly-typed 3‑D container. The file is **independent** of `Matrix_Product.h` — it does not depend on any multivector instance, only on blade masks and the `GPSign`/`IPSign`/`OPSign` functions from `Blade_Operators.h`.

### Step 1.1 — Core tensor builder: `_EvalProductTensor`

```cpp
#pragma once

#include "Tan.Math/Tensor.h"    // for CTensor<T> (Phase 0)
#include "Enum.h"
#include "BladeMask.h"
#include "Blade_Operators.h"    // for GPSign, IPSign, OPSign

namespace Tan {
namespace GA {

/**
 * Build the 3D product tensor O^k_{ij} from three blade masks.
 *
 * The result is a CTensor<TValue> of shape (|xMaskC|, |xMaskA|, |xMaskB|).
 * Elements are ±1 when a valid product exists, 0 otherwise.
 *
 * Template parameters:
 *   TValue  - numeric type (float, double, int32_t, int64_t)
 *   TBlade  - blade type (must match the masks)
 *   FuncOp  - product sign function (GPSign, IPSign, OPSign)
 */
template <typename TValue, typename TBlade, typename FuncOp>
void _EvalProductTensor(
    CTensor<TValue>& tenO,
    const CBladeMask<TBlade>& xMaskA,
    const CBladeMask<TBlade>& xMaskB,
    const CBladeMask<TBlade>& xMaskC,
    bool bLeftToRight,
    FuncOp xFuncOp)
{
    const unsigned uDimA = xMaskA.Count();
    const unsigned uDimB = xMaskB.Count();
    const unsigned uDimC = xMaskC.Count();

    // Shape: (|c_mask|, |a_mask|, |b_mask|)
    tenO.SetSize(uDimC, uDimA, uDimB);
    tenO.Zero();

    // Write directly as 3‑D indexed via CArray::operator()(TSizeVec)
    unsigned uSign;
    TBlade blC;

    xMaskA.ForEachBlade([&](unsigned uIndexA, const TBlade& blA) {
        xMaskB.ForEachBlade([&](unsigned uIndexB, const TBlade& blB) {
            bool bValid;
            if (bLeftToRight)
                bValid = xFuncOp(uSign, blC, blA, blB);
            else
                bValid = xFuncOp(uSign, blC, blB, blA);

            unsigned uIndexC;
            if (bValid && xMaskC.GetIndex(uIndexC, blC)) {
                TIdxVec pos = { uIndexC, uIndexA, uIndexB };
                tenO(pos) = (uSign & 1) ? TValue(-1) : TValue(1);
            }
        });
    });
}
```

Key design decisions:
- Returns `CTensor<TValue>` with proper 3‑D shape `(|c_mask|, |a_mask|, |b_mask|)` — no flat 2‑D intermediate anymore
- Direct 3‑D indexing via `CArray::operator()(TIdxVec)` using `{k, i, j}` index tuples
- Only stores ±1 values — the tensor is structurally sparse but we store dense blocks for the mask-specified subspaces
- Uses the same `GPSign`/`IPSign`/`OPSign` callables from `Blade_Operators.h`

### Step 1.2 — Public wrappers: GP, IP, OP

```cpp
template <typename TValue, typename TBlade>
void EvalProductTensor_GP(
    CTensor<TValue>& tenO,
    const CBladeMask<TBlade>& xMaskA,
    const CBladeMask<TBlade>& xMaskB,
    const CBladeMask<TBlade>& xMaskC,
    bool bLeftToRight = true)
{
    _EvalProductTensor(tenO, xMaskA, xMaskB, xMaskC, bLeftToRight,
        [](unsigned& uSign, TBlade& blC, const TBlade& blA, const TBlade& blB) -> bool {
            return GPSign(uSign, blC, blA, blB);
        });
}

template <typename TValue, typename TBlade>
void EvalProductTensor_IP(
    CTensor<TValue>& tenO,
    const CBladeMask<TBlade>& xMaskA,
    const CBladeMask<TBlade>& xMaskB,
    const CBladeMask<TBlade>& xMaskC,
    bool bLeftToRight = true)
{
    _EvalProductTensor(tenO, xMaskA, xMaskB, xMaskC, bLeftToRight,
        [](unsigned& uSign, TBlade& blC, const TBlade& blA, const TBlade& blB) -> bool {
            return IPSign(uSign, blC, blA, blB);
        });
}

template <typename TValue, typename TBlade>
void EvalProductTensor_OP(
    CTensor<TValue>& tenO,
    const CBladeMask<TBlade>& xMaskA,
    const CBladeMask<TBlade>& xMaskB,
    const CBladeMask<TBlade>& xMaskC,
    bool bLeftToRight = true)
{
    _EvalProductTensor(tenO, xMaskA, xMaskB, xMaskC, bLeftToRight,
        [](unsigned& uSign, TBlade& blC, const TBlade& blA, const TBlade& blB) -> bool {
            return OPSign(uSign, blC, blA, blB);
        });
}
```

### Step 1.3 — Add `#include` to template

Add `#include "Tan.Math/Tensor.h"` and `#include "Tan.GA/Tensor_Product.h"` in `py/pytanga/_template.cpp` alongside the existing includes.

### Step 1.4 — Include guard and license header

The file follows the same Apache 2.0 license header pattern as all other Tan.GA files.

---

## Phase 2: Python Bindings (pytanga codegen)

### Step 2.1 — Add placeholder to template

Add `{PRODUCT_TENSOR_DEF}` to `py/pytanga/_template.cpp` (in the matrix/blade-mask section, near `{MATRIX_DEF}`).

### Step 2.2 — Create codegen fragment in `py/pytanga/codegen/_tensor.py`

The binding converts the C++ `CTensor<TValue>` to a 3‑D `py::array_t<{ctype}>`.  A generic `_tensor_to_arr` lambda copies the CTensor's flat storage to numpy (both use row-major ordering).

Create the file `py/pytanga/codegen/_tensor.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Binding fragment for product tensor construction (GP/IP/OP, all dtypes)."""


def product_tensor_def(ctype: str) -> str:
    """Build GP/IP/OP tensor bindings using the CTensor<T> return type from Phase 0.

    Returns a single string containing all three python-def bindings
    (product_tensor_gp, product_tensor_ip, product_tensor_op).
    """
    return f"""
    // -----------------------------------------------------------------------
    // Product-tensor construction (3D Cayley table for GP/IP/OP)
    // -----------------------------------------------------------------------
    
    // Helper: copy N‑D CTensor to numpy array (both row-major)
    auto _tensor_to_arr = [](const Tan::CTensor<{ctype}>& ten) -> py::array_t<{ctype}> {{
        size_t ndim = ten.GetDimension();
        const auto& sizes = ten.GetSizes();
        std::vector<py::ssize_t> py_sizes(ndim);
        for (size_t d = 0; d < ndim; ++d)
            py_sizes[d] = static_cast<py::ssize_t>(sizes[d]);
        py::array_t<{ctype}> arr(py_sizes);
        auto buf = arr.mutable_data();
        const {ctype}* src = ten.GetData();     // row-major flat storage from CArray
        std::copy(src, src + ten.GetTotalSize(), buf);
        return arr;
    }};

    auto _build_tensor = [&, _tensor_to_arr](const std::vector<uint32_t>& a_ids,
                              const std::vector<uint32_t>& b_ids,
                              const std::vector<uint32_t>& c_ids,
                              bool left_to_right,
                              const std::string& product_name) -> py::array_t<{ctype}> {{
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids) xMaskA.Insert(TBlade(id));
        for (auto id : b_ids) xMaskB.Insert(TBlade(id));
        for (auto id : c_ids) xMaskC.Insert(TBlade(id));
        Tan::CTensor<{ctype}> ten;
        if (product_name == "gp")
            Tan::GA::EvalProductTensor_GP<{ctype}, TBlade>(ten, xMaskA, xMaskB, xMaskC, left_to_right);
        else if (product_name == "ip")
            Tan::GA::EvalProductTensor_IP<{ctype}, TBlade>(ten, xMaskA, xMaskB, xMaskC, left_to_right);
        else if (product_name == "op")
            Tan::GA::EvalProductTensor_OP<{ctype}, TBlade>(ten, xMaskA, xMaskB, xMaskC, left_to_right);
        else
            throw std::runtime_error("Unknown product: " + product_name);
        return _tensor_to_arr(ten);
    }};

    m.def("product_tensor_gp", _build_tensor,
        py::arg("a_ids"), py::arg("b_ids"), py::arg("c_ids"),
        py::arg("left_to_right") = true, py::arg("_product") = "gp",
        "Build the 3D geometric-product tensor O[k,i,j] from blade masks.");

    m.def("product_tensor_ip", _build_tensor,
        py::arg("a_ids"), py::arg("b_ids"), py::arg("c_ids"),
        py::arg("left_to_right") = true, py::arg("_product") = "ip",
        "Build the 3D inner-product tensor O[k,i,j] from blade masks.");

    m.def("product_tensor_op", _build_tensor,
        py::arg("a_ids"), py::arg("b_ids"), py::arg("c_ids"),
        py::arg("left_to_right") = true, py::arg("_product") = "op",
        "Build the 3D outer-product tensor O[k,i,j] from blade masks.");
"""
```

Note: The `_product` parameter is a pybind11-internal routing parameter. In the Python API it is not exposed; instead separate `product_tensor_gp/ip/op` functions are called. If needed, a single `product_tensor(product, ...)` dispatch can be added.

### Step 2.3 — Wire into `py/pytanga/codegen/_generator.py`

In `_generator.py`, import the new fragment and add the placeholder replacement in the `generate()` function, in the same dtype-dependent block as `MATRIX_DEF`:

1. Add the import at top:
   ```python
   from ._tensor import product_tensor_def
   ```

2. Add the placeholder replacement after the `MATRIX_DEF` lines (for both float and int branches):
   ```python
   template = sub_bare(template, "PRODUCT_TENSOR_DEF", product_tensor_def(ctype))
   ```

---

## Phase 3: Python Class — `mv_product_tensor.py`

### Step 3.1 — Create `py/pytanga/mv_product_tensor.py`

This is a new file (NOT `mv_product_matrix.py` — that already exists with a different purpose). The class wraps the 3D numpy array with blade mask labels.

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga._mv_product_tensor — MVProductTensor: a 3‑D product tensor labelled by blade masks."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from .blade_mask import BladeMask
from .product import EProduct

if TYPE_CHECKING:
    from .algebra import Algebra


@dataclass
class MVProductTensor:
    """A 3‑D tensor encoding the full product table O^k_{ij} for a GA operation.

    The tensor entry ``data[k, i, j]`` is ±1 when blade ``a_mask[i]`` ∘
    ``b_mask[j]`` produces ``c_mask[k]``, and 0 otherwise.  No multivector
    coefficients are involved — this is the pure Cayley-table restricted to
    the three given blade masks.

    To apply the product to multivectors A and B:

        C_vec = np.einsum('kij,i,j->k', tensor.data, A_coeffs, B_coeffs)

    Parameters
    ----------
    data : np.ndarray
        Shape ``(|c_mask|, |a_mask|, |b_mask|)``. 3‑D tensor of ±1/0 values.
    a_mask : BladeMask
        First  axis — blade ids of the left operand.
    b_mask : BladeMask
        Second axis — blade ids of the right operand.
    c_mask : BladeMask
        Zeroth axis — blade ids of the result.
    product : EProduct
        The GA product this tensor encodes (GP, IP, or OP).
    left : bool
        True = A ∘ B (A left, B right).  False = B ∘ A.
    """

    data: np.ndarray
    a_mask: BladeMask
    b_mask: BladeMask
    c_mask: BladeMask
    product: EProduct
    left: bool

    def __post_init__(self) -> None:
        if self.data.ndim != 3:
            raise ValueError(
                f"MVProductTensor.data must be 3-D, got ndim={self.data.ndim}"
            )
        nc, na, nb = self.data.shape
        if len(self.c_mask) != nc:
            raise ValueError(f"axis 0 size {nc} != len(c_mask)={len(self.c_mask)}")
        if len(self.a_mask) != na:
            raise ValueError(f"axis 1 size {na} != len(a_mask)={len(self.a_mask)}")
        if len(self.b_mask) != nb:
            raise ValueError(f"axis 2 size {nb} != len(b_mask)={len(self.b_mask)}")
        if self.b_mask.algebra is not self.c_mask.algebra:
            raise ValueError("b_mask and c_mask belong to different algebras")

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the underlying data array: (|c_mask|, |a_mask|, |b_mask|)."""
        return self.data.shape

    @property
    def algebra(self) -> "Algebra":
        """The algebra this tensor belongs to (from b_mask)."""
        return self.b_mask.algebra

    def __repr__(self) -> str:
        return (
            f"MVProductTensor(shape={self.data.shape}, "
            f"a_mask={self.a_mask}, b_mask={self.b_mask}, c_mask={self.c_mask}, "
            f"product={self.product.name}, left={self.left})"
        )

    def contract(self, a_coeffs: np.ndarray, b_coeffs: np.ndarray) -> np.ndarray:
        """Contract the tensor with two coefficient vectors via einsum.

        Parameters
        ----------
        a_coeffs : np.ndarray
            Shape ``(|a_mask|,)`` — coefficients of the left multivector.
        b_coeffs : np.ndarray
            Shape ``(|b_mask|,)`` — coefficients of the right multivector.

        Returns
        -------
        np.ndarray
            Shape ``(|c_mask|,)`` — coefficient vector of the result C.
        """
        return np.einsum('kij,i,j->k', self.data, a_coeffs, b_coeffs)
```

Note: The file name `mv_product_tensor.py` is distinct from the existing `mv_product_matrix.py` (which wraps the 2D per-multivector product matrix).

### Step 3.2 — Export in `__init__.py`

Add `from .mv_product_tensor import MVProductTensor` to `py/pytanga/__init__.py`.

---

## Phase 4: Solver Integration

### Step 4.1 — Create `py/pytanga/solver/tensor_product.py`

Following the solver restructure (see `dev/todos/solver-restructure-plan.md`), the `MVSolver` class has been removed.  All solver functionality is now exposed as free functions taking `alg: Algebra` as first argument, organised in the `py/pytanga/solver/` submodule.

Create `py/pytanga/solver/tensor_product.py` as a new public module:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.solver.product_tensor — build the 3‑D product tensor from blade masks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytanga.blade_mask import BladeMask
from pytanga.mv_product_tensor import MVProductTensor
from pytanga.product import EProduct

if TYPE_CHECKING:
    from pytanga.algebra import Algebra

from .blade_masks import product_blade_mask


def product_tensor(
    alg: "Algebra",
    a_mask: BladeMask,
    b_mask: BladeMask,
    c_mask: BladeMask | None = None,
    *,
    product: EProduct = EProduct.GP,
    left: bool = True,
) -> MVProductTensor:
    """Build the 3‑D product tensor O from blade masks.

    When *c_mask* is None (default), it is computed automatically via
    ``product_blade_mask`` for the given *a_mask*, *b_mask*, and *product*.

    Parameters
    ----------
    a_mask : BladeMask
        Blade ids of the left operand A.
    b_mask : BladeMask
        Blade ids of the right operand B.
    c_mask : BladeMask | None
        Blade ids of the result C.  Computed from a_mask and b_mask if None.
    product : EProduct
        Which GA operation to encode.
    left : bool
        True = A ∘ B; False = B ∘ A.

    Returns
    -------
    MVProductTensor
        Shape ``(|c_mask|, |a_mask|, |b_mask|)``.
    """
    assert a_mask.algebra is alg
    assert b_mask.algebra is alg

    if c_mask is None:
        c_mask = product_blade_mask(alg, a_mask, b_mask, product=product, left=left)

    assert c_mask.algebra is alg

    _fn_map = {
        EProduct.GP: "product_tensor_gp",
        EProduct.IP: "product_tensor_ip",
        EProduct.OP: "product_tensor_op",
    }
    fn = getattr(alg._mod, _fn_map[product])
    arr = fn(a_mask.ids, b_mask.ids, c_mask.ids, left)
    # arr is already 3-D from the binding (via _tensor_to_arr in C++)

    return MVProductTensor(
        data=arr,
        a_mask=a_mask,
        b_mask=b_mask,
        c_mask=c_mask,
        product=product,
        left=left,
    )
```

Usage:
```python
from pytanga.solver.product_tensor import product_tensor

alg = pytanga.Algebra(3, 0)
full = pytanga.BladeMask.full(alg)
T = product_tensor(alg, full, full)
```

---

## Phase 5: Tests

### Step 5.1 — Create `py/tests/test_product_tensor.py`

Tests should cover:

1. **Shape correctness**: Tensor built from three masks has the expected shape `(len(c_mask), len(a_mask), len(b_mask))`.

2. **GP tensor entries**: For E3 with full masks, verify specific known entries:
   - `O[k, e1_idx, e1_idx]` should be 1 for the scalar blade (k = scalar_idx)
   - `O[k, e1_idx, e2_idx]` should be 1 for the e1^e2 blade
   - No entries should be outside `{-1, 0, 1}`

3. **IP tensor**: Inner product is zero when blades are not in containment relationship. Verify known cases.

4. **OP tensor**: Wedge product is zero when blades share basis vectors. Verify known cases.

5. **Einsum contraction consistency**: Build tensor for E3, contract with random coefficient vectors via einsum, compare against the actual `A * B` (GP), `A | B` (IP), `A ^ B` (OP) computed by the algebra.

6. **Left vs right**: Verify `left=True` vs `left=False` produce transposed results where appropriate.

7. **Auto c_mask**: When c_mask is None, the solver computes it automatically.

8. **Subspace masks**: Tensor built with restricted masks (e.g., only even-grade blades) has correct shape and entries.

9. **Modular integer types**: Tensor built from int64 algebra has int64 dtype and correct entries (±1 mod p makes sense for GP but IP/OP sign is just ±1 anyway).

Test fixtures should use the existing `alg_float` and `slv_float` fixtures from `conftest.py`.

---

## Phase 6: Documentation

### Step 6.1 — Create `docs/cpp/tensor-product.md`

C++ developer documentation covering:

- **`CTensor<T>`**: Overview, inheritance from `CArray<T>`, API reference (`GetDimension()`, `GetDimSize()`, `GetSizes()`, `GetTotalSize()`, `SetSize()`, `Resize()`, `Zero()`, `operator()`), relationship to `CMatrix<T>`, example usage.
- **`Tensor_Product.h`**: Mathematical background (tensor contraction equation), API reference for `_EvalProductTensor`, `EvalProductTensor_GP`, `EvalProductTensor_IP`, `EvalProductTensor_OP`, description of the `(k, i, j)` axis layout, notes on `±1`/`0` entries and row-major flattening to numpy.
- Cross-reference to `docs/cpp/product-matrices.md` for the related 2‑D `Matrix_Product.h`.

Follow the style of existing docs such as `docs/cpp/product-matrices.md`.

### Step 6.2 — Create `docs/py/product-tensor.md`

Python user documentation covering:

- **`MVProductTensor`**: Overview, dataclass fields (`data`, `a_mask`, `b_mask`, `c_mask`, `product`, `left`), properties (`shape`, `algebra`), `contract()` method, einsum usage patterns.
- **`product_tensor()`** free function: Signature, parameter descriptions, return type, example usage showing import from `pytanga.solver.product_tensor`.
- Relationship to `MVProductMatrix` and when to use each.
- Integration with `BladeMask` and `MVSolver`-family functions.

Follow the style of existing docs such as `docs/py/solver.md`.

### Step 6.3 — Update `docs/cpp/index.md` and `docs/py/index.md`

Add entries for the new pages in the respective index files, if they exist.  If no index file is present, the new doc pages still stand alone; cross-links from related pages (e.g. `docs/cpp/product-matrices.md`, `docs/py/solver.md`) are sufficient.

---

## Dependency Ordering

```
Phase 0 (C++ CTensor<T> — rank-agnostic tensor container)
    │
    ▼
Phase 1 (C++ Tensor_Product.h — builds 3‑D product tensor, returns CTensor<T>)
    │
    ▼
Phase 2 (pytanga codegen bindings — CTensor<T> → numpy 3‑D array)
    │   New file: py/pytanga/codegen/_tensor.py
    │   Modify:  py/pytanga/codegen/_generator.py
    │   Modify:  py/pytanga/_template.cpp
    │
    ▼
Phase 3 (Python MVProductTensor class)
    │
    ├──► Phase 4 (py/pytanga/solver/tensor_product.py — free function)
    └──► Phase 5 (Tests)
```

Phase 0 provides the `CTensor<T>` type used as the return value of Phase 1.  
Phase 2 converts `CTensor<T>` → numpy array.  Phase 3 wraps it in Python.  
Phase 4 adds the solver-module free function.  Phases 4 and 5 can proceed in parallel once Phase 3 is done.
Phase 6 (Documentation) can be done in parallel with Phases 4–5, or immediately after Phase 3.

---

## Verification

After all phases:

1. Run `uv run python -m pytest py/tests/test_product_tensor.py -v` — all tests pass.
2. Run existing test suite to ensure no regressions: `uv run python -m pytest py/tests/ -v`
3. Smoke test:
   ```python
   import numpy as np
   import pytanga
   from pytanga.solver.product_tensor import product_tensor

   alg = pytanga.Algebra(3, 0)
   full = pytanga.BladeMask.full(alg)
   T = product_tensor(alg, full, full)
   print(T.shape)  # (8, 8, 8) for E3
   # Contract with basis vectors
   e1_coeffs = np.zeros(8); e1_coeffs[1] = 1.0
   e2_coeffs = np.zeros(8); e2_coeffs[2] = 1.0  # e2 blade
   result = T.contract(e1_coeffs, e2_coeffs)
   print(result)  # should have non-zero at e1^e2 blade index (idx 3)
   ```

---

## Estimated Effort

| Phase | Description | Effort |
|-------|-------------|--------|
| 0 | C++ `CTensor<T>` class (`cpp/Tan.Math/Tensor.h`) | ~45 min |
| 1 | C++ template `Tensor_Product.h` (returns `CTensor<T>`) | ~1 h |
| 2 | pytanga codegen bindings (`CTensor<T>` → numpy) | ~45 min |
| 3 | Python `MVProductTensor` class | ~30 min |
| 4 | `py/pytanga/solver/tensor_product.py` free function | ~20 min |
| 5 | Tests | ~1 h |
| 6 | Documentation (inline docstrings + `docs/` pages) | ~1 h |
| **Total** | | **~5.25 h** |

---

## Key Integration Points

- **New `CTensor<T>` class** (`cpp/Tan.Math/Tensor.h`) inherits from `CArray<T>` and `CValuePrecision<T>` (same base classes as `CMatrix<T>`), providing rank-agnostic N‑D storage with row-major layout matching numpy's default.
- **New file `Tensor_Product.h`** returns `CTensor<T>` with proper 3‑D shape `(|c_mask|, |a_mask|, |b_mask|)` — no flat 2‑D intermediate. Direct 3‑D indexing via `CArray::operator()(TIdxVec)`.
- **Uses existing `GPSign`/`IPSign`/`OPSign`** from `Blade_Operators.h` — no new blade algebra needed.
- **Codegen fragment** lives in `py/pytanga/codegen/_tensor.py`, following the established pattern (one file per feature); wired into `_generator.py` via import and placeholder replacement.
- **Binding helper `_tensor_to_arr`** copies `CTensor<T>` flat storage to numpy via `std::copy` — both use row-major ordering, so no reshape needed.
- **Solver function** `product_tensor(alg, ...)` lives in `py/pytanga/solver/tensor_product.py` as a free function, following the solver restructure — no `MVSolver` class.
- **Python class `MVProductTensor`** is intentionally separate from `MVProductMatrix` (which already stores the 3D per-multivector product matrix stack). The product tensor is a fundamentally different object (no MV coefficients, pure Cayley table).
- **`numpy.einsum`** is the intended contraction mechanism in Python. The `contract()` convenience method on `MVProductTensor` wraps this.
