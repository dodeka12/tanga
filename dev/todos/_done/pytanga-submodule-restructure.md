# pytanga Submodule Restructuring Plan

**Goal:** Restructure `py/pytanga/` into focused submodules — `blade_mask`, `matrix`,
`tensor`, and `solver` — with well-named files that don't redundantly repeat the
submodule name.

**Import convention:** Single-dot relative imports (e.g. `from ._dispatch import ...`) are
fine. Double-dot relative imports are **replaced with absolute imports** (e.g.
`from pytanga.blade_mask import BladeMask` instead of `from pytanga.blade_mask import BladeMask`).

---

## 1. Target Structure

```
py/pytanga/
├── enums.py                     # EProduct, EInv (renamed from product.py)
│
├── blade_mask/                  # Everything blade-mask-related
│   ├── __init__.py              # Re-exports BladeMask
│   ├── _mask.py                 # BladeMask class (moved from pytanga/blade_mask.py)
│   ├── _dispatch.py             # _dispatch_product_blade_mask (split from solver/_dispatch.py)
│   └── predict.py               # inverse_blade_mask, product_blade_mask
│
├── matrix/                      # MVMatrix, MVProductMatrix, and all matrix operations
│   ├── __init__.py              # Re-exports MVMatrix, MVProductMatrix
│   ├── _data.py                 # MVMatrix class (moved from pytanga/mv_matrix.py)
│   ├── _product_data.py         # MVProductMatrix class (moved from pytanga/mv_product_matrix.py)
│   ├── _dispatch.py             # _dispatch_product_matrix, _dispatch_product_matrix_masked,
│   │                            #   _dispatch_product_matrix_array (split from solver/_dispatch.py)
│   ├── convert.py               # to_matrix, from_matrix
│   └── product.py               # product_matrix, product_matrix_rev, product_matrix_conj
│
├── tensor/                      # MVTensor and all tensor operations
│   ├── __init__.py              # Re-exports MVTensor
│   ├── _data.py                 # MVTensor class (moved from pytanga/mv_tensor.py)
│   ├── convert.py               # to_tensor, from_tensor
│   ├── product.py               # product_tensor
│   └── ops.py                   # contract (and future tensor operations)
│
├── solver/                      # High-level solve functions only
│   ├── __init__.py              # Empty
│   └── solve.py                 # solve, solve_lsq, solve_mod
│
├── mv_utils.py                  # random_mask, random_mv, _as_mv, MVLike (merged from _coerce.py)
│
├── product.py                   # ✕ DELETED (renamed to enums.py)
├── mv_matrix.py                 # ✕ DELETED (class moved to matrix/_data.py)
├── mv_product_matrix.py         # ✕ DELETED (class moved to matrix/_product_data.py)
├── mv_tensor.py                 # ✕ DELETED (class moved to tensor/_data.py)
├── blade_mask.py                # ✕ DELETED (class moved to blade_mask/_mask.py)
├── solver/_coerce.py            # ✕ DELETED (merged into mv_utils.py)
├── solver/_dispatch.py          # ✕ DELETED (split into blade_mask/_dispatch.py + matrix/_dispatch.py)
├── (other existing files unchanged)
```

### File Renaming & Movement Rationale

| Current Path | New Path | Reasoning |
|---|---|---|
| `product.py` | `enums.py` | Contains only `EProduct` and `EInv` enums. Name `enums.py` clearly communicates purpose. |
| `blade_mask.py` | `blade_mask/_mask.py` | Class moves into the submodule so the directory can be named `blade_mask/`. Underscore prefix = implementation detail. Re-exported via `__init__.py`. |
| `mv_matrix.py` | `matrix/_data.py` | Class belongs in `matrix/` submodule. `_data` = the data class. Re-exported via `__init__.py`. |
| `mv_product_matrix.py` | `matrix/_product_data.py` | Class belongs in `matrix/` submodule. `_product_data` = the product matrix data class. Re-exported via `__init__.py`. |
| `mv_tensor.py` | `tensor/_data.py` | Class belongs in `tensor/` submodule. `_data` = the data class. Re-exported via `__init__.py`. |
| `solver/blade_masks.py` | `blade_mask/predict.py` | These functions *predict* what blades result from / go into GA products. Submodule already says "blade_mask", no need to repeat in filename. |
| `solver/matrix_convert.py` | `matrix/convert.py` | Converting between MV and MVMatrix. Submodule says "matrix", file says "convert". |
| `solver/matrix_product.py` | `matrix/product.py` | Building product matrices. Submodule says "matrix", file says "product". |
| `solver/tensor_contract.py` | `tensor/ops.py` | Contract is a tensor→tensor *operation*. Future operations go here too. |
| `solver/tensor_convert.py` | `tensor/convert.py` | Same pattern as `matrix/convert.py`. |
| `solver/tensor_product.py` | `tensor/product.py` | Same pattern as `matrix/product.py`. Symmetry. |
| `solver/solve.py` | `solver/solve.py` | Already well-named. Submodule is `solver`, file is `solve`. |
| `solver/_coerce.py` | (merged into `mv_utils.py`) | Single function `_as_mv` + `MVLike` type alias. Merged into `mv_utils.py` which already contains utility functions like `random_mask`, `random_mv`. |
| `solver/_dispatch.py` | `blade_mask/_dispatch.py`<br>`matrix/_dispatch.py` | Split by domain: blade mask dispatch goes with `blade_mask/`, product matrix dispatch goes with `matrix/`. |

---

## 2. `solver/_dispatch.py` Split

The current `solver/_dispatch.py` contains four dispatch functions. They are split by domain:

### → `blade_mask/_dispatch.py`

- `_dispatch_product_blade_mask` — calls blade-mask prediction C++ bindings

### → `matrix/_dispatch.py`

- `_dispatch_product_matrix` — calls 2-mask product matrix C++ bindings
- `_dispatch_product_matrix_masked` — calls 3-mask product matrix C++ bindings
- `_dispatch_product_matrix_array` — calls array product matrix C++ bindings

---

## 3. `solver/_coerce.py` → Merge into `mv_utils.py`

`_coerce.py` contains:
- `MVLike` — type alias (`Union[MV, float, int, str]`)
- `_as_mv` — coerce scalar/string to MV

Both are merged into `py/pytanga/mv_utils.py` (which already provides `random_mask`, `random_mv`). After the merge, `mv_utils.py` contains:

```python
# mv_utils.py
MVLike = Union["MV", float, int, str]

def _as_mv(alg, x): ...        # coerce scalar/string to MV
def random_mask(alg, n, ...): ...  # random blade mask
def random_mv(alg, ...): ...       # random multivector
```

---

## 4. Internal Import Changes

### 4.1 `product.py` → `enums.py`

All references to `from pytanga.product import EProduct, EInv` become `from pytanga.enums import EProduct, EInv`.
Similarly, all `from .product import ...` become `from .enums import ...`.

**Files affected within pytanga:**
- `blade_mask/predict.py` — `from pytanga.enums import EProduct`
- `blade_mask/_dispatch.py` — `from pytanga.enums import EProduct`
- `matrix/_dispatch.py` — `from pytanga.enums import EProduct, EInv`
- `matrix/product.py` — `from pytanga.enums import EInv, EProduct`
- `matrix/_product_data.py` — `from pytanga.enums import EInv, EProduct`
- `tensor/product.py` — `from pytanga.enums import EProduct`
- `solver/solve.py` — `from pytanga.enums import EProduct`
- `py/pytanga/__init__.py` — `from .enums import EProduct`

### 4.2 BladeMask class move

**`blade_mask/_mask.py`** — file content identical to old `blade_mask.py`, with imports adjusted from single-dot (`from .xxx`) to absolute (`from pytanga.xxx`) since it now lives one level deeper:

```python
# OLD (in blade_mask.py — single-dot relative imports)
from ._blade_names import blade_name
from ._blade_names import grade as _grade
from ._parse import _parse_mv_string
from .algebra import Algebra
from .mv import MV

# NEW (in blade_mask/_mask.py — absolute imports)
from pytanga._blade_names import blade_name
from pytanga._blade_names import grade as _grade
from pytanga._parse import _parse_mv_string
from pytanga.algebra import Algebra
from pytanga.mv import MV
```

**`blade_mask/__init__.py`:**
```python
from ._mask import BladeMask

__all__ = ["BladeMask"]
```

### 4.3 MVMatrix / MVProductMatrix move

**`matrix/_data.py`** — file content identical to old `mv_matrix.py`, with imports adjusted:

```python
# OLD
from .blade_mask import BladeMask

# NEW (absolute import)
from pytanga.blade_mask import BladeMask  # via blade_mask/__init__.py re-export
```

**`matrix/_product_data.py`** — file content identical to old `mv_product_matrix.py`, with imports adjusted:

```python
# OLD
from .blade_mask import BladeMask
from .product import EInv, EProduct

# NEW (absolute imports)
from pytanga.blade_mask import BladeMask
from pytanga.enums import EInv, EProduct
```

**`matrix/__init__.py`:**
```python
from ._data import MVMatrix
from ._product_data import MVProductMatrix

__all__ = ["MVMatrix", "MVProductMatrix"]
```

### 4.4 MVTensor move

**`tensor/_data.py`** — file content identical to old `mv_tensor.py`, with imports adjusted:

```python
# OLD
from .blade_mask import BladeMask

# NEW (absolute import)
from pytanga.blade_mask import BladeMask
```

**`tensor/__init__.py`:**
```python
from ._data import MVTensor

__all__ = ["MVTensor"]
```

### 4.5 `_dispatch.py` split — imports

**`blade_mask/_dispatch.py`:**
```python
# Uses absolute import
from pytanga.enums import EProduct
```

**`matrix/_dispatch.py`:**
```python
# Uses absolute imports
import numpy as np
from pytanga.enums import EInv, EProduct
```

### 4.6 Submodule operation files — imports

**`blade_mask/predict.py`:**
```python
# OLD
from pytanga.blade_mask import BladeMask
from pytanga.product import EProduct
from ._dispatch import _dispatch_product_blade_mask

# NEW (absolute for cross-submodule, single-dot for sibling)
from pytanga.blade_mask import BladeMask  # via __init__ re-export
from pytanga.enums import EProduct
from ._dispatch import _dispatch_product_blade_mask  # single-dot: sibling stays
```

**`matrix/convert.py`:**
```python
# OLD
from pytanga.blade_mask import BladeMask
from pytanga.mv import MV
from pytanga.mv_matrix import MVMatrix
from ._coerce import MVLike, _as_mv

# NEW
from pytanga.blade_mask import BladeMask
from pytanga.mv import MV
from . import MVMatrix  # single-dot: via __init__.py re-export
from pytanga.mv_utils import MVLike, _as_mv  # merged into mv_utils.py
```

**`matrix/product.py`:**
```python
# OLD
from pytanga.blade_mask import BladeMask
from pytanga.mv_product_matrix import MVProductMatrix
from pytanga.product import EInv, EProduct
from ._coerce import MVLike, _as_mv
from ._dispatch import _dispatch_product_matrix_masked
from .blade_masks import product_blade_mask

# NEW
from pytanga.blade_mask import BladeMask
from . import MVProductMatrix  # single-dot: via __init__.py re-export
from pytanga.enums import EInv, EProduct
from pytanga.mv_utils import MVLike, _as_mv
from ._dispatch import _dispatch_product_matrix_masked  # single-dot: sibling
from pytanga.blade_mask.predict import product_blade_mask
```

**`tensor/convert.py`:**
```python
# OLD
from pytanga.blade_mask import BladeMask
from pytanga.mv import MV
from pytanga.mv_tensor import MVTensor
from ._coerce import MVLike, _as_mv
from .matrix_convert import to_matrix

# NEW
from pytanga.blade_mask import BladeMask
from pytanga.mv import MV
from . import MVTensor  # single-dot: via __init__.py re-export
from pytanga.mv_utils import MVLike, _as_mv
from pytanga.matrix.convert import to_matrix
```

**`tensor/product.py`:**
```python
# OLD
from pytanga.blade_mask import BladeMask
from pytanga.mv_tensor import MVTensor
from pytanga.product import EProduct
from .blade_masks import product_blade_mask

# NEW
from pytanga.blade_mask import BladeMask
from . import MVTensor  # single-dot: via __init__.py re-export
from pytanga.enums import EProduct
from pytanga.blade_mask.predict import product_blade_mask
```

**`tensor/ops.py`:**
```python
# OLD (tensor_contract.py)
from pytanga.blade_mask import BladeMask
from pytanga.mv_tensor import MVTensor

# NEW
from pytanga.blade_mask import BladeMask
from . import MVTensor  # single-dot: via __init__.py re-export
```

**`solver/solve.py`:**
```python
# OLD
from pytanga.blade_mask import BladeMask
from pytanga.mv import MV
from pytanga.mv_matrix import MVMatrix
from pytanga.product import EProduct
from ._coerce import MVLike, _as_mv
from .blade_masks import inverse_blade_mask, product_blade_mask
from .matrix_convert import from_matrix, to_matrix
from .matrix_product import product_matrix as build_product_matrix

# NEW
from pytanga.blade_mask import BladeMask
from pytanga.mv import MV
from pytanga.matrix import MVMatrix  # via __init__.py re-export
from pytanga.enums import EProduct
from pytanga.mv_utils import MVLike, _as_mv
from pytanga.blade_mask.predict import inverse_blade_mask, product_blade_mask
from pytanga.matrix.convert import from_matrix, to_matrix
from pytanga.matrix.product import product_matrix as build_product_matrix
```

### 4.7 `pytanga/__init__.py` — updated

```python
# OLD
from .algebra import Algebra
from .blade_mask import BladeMask
from .codegen import precompile
from .mv import MV
from .mv_matrix import MVMatrix
from .mv_product_matrix import MVProductMatrix
from .mv_tensor import MVTensor
from .mv_utils import random_mask, random_mv
from .product import EProduct

# NEW
from .algebra import Algebra
from .blade_mask import BladeMask  # still works via blade_mask/__init__.py re-export
from .codegen import precompile
from .enums import EProduct
from .matrix import MVMatrix, MVProductMatrix  # via matrix/__init__.py re-exports
from .mv import MV
from .mv_utils import random_mask, random_mv
from .tensor import MVTensor  # via tensor/__init__.py re-export
```

### 4.8 Import Rules Summary

| Location | Pattern | Example |
|---|---|---|
| Same submodule (sibling) | Single-dot relative | `from ._dispatch import ...` |
| Same submodule via `__init__` | Single-dot relative | `from . import MVMatrix` |
| Cross-submodule or top-level | Absolute | `from pytanga.blade_mask import BladeMask` |
| Top-level `__init__.py` | Single-dot relative | `from .enums import EProduct` |

---

## 5. Import Pattern Summary

After restructuring, the public import paths become:

```python
# Enums
from pytanga.enums import EProduct, EInv

# Core classes (re-exported from submodule __init__.py)
from pytanga.blade_mask import BladeMask
from pytanga.matrix import MVMatrix, MVProductMatrix
from pytanga.tensor import MVTensor

# Blade mask operations
from pytanga.blade_mask.predict import (
    inverse_blade_mask,
    product_blade_mask,
)

# Matrix operations
from pytanga.matrix.convert import to_matrix, from_matrix
from pytanga.matrix.product import (
    product_matrix,
    product_matrix_rev,
    product_matrix_conj,
)

# Tensor operations
from pytanga.tensor.convert import to_tensor, from_tensor
from pytanga.tensor.product import product_tensor
from pytanga.tensor.ops import contract

# High-level solvers
from pytanga.solver.solve import solve, solve_lsq, solve_mod

# Utilities
from pytanga.mv_utils import random_mask, random_mv, MVLike, _as_mv
```

### Comparison: Old vs New Imports

| Old Import | New Import |
|---|---|
| `from pytanga import BladeMask` | `from pytanga.blade_mask import BladeMask` (also `pytanga.BladeMask` still works via `__init__`) |
| `from pytanga import MVMatrix` | `from pytanga.matrix import MVMatrix` (also `pytanga.MVMatrix` still works) |
| `from pytanga import MVProductMatrix` | `from pytanga.matrix import MVProductMatrix` |
| `from pytanga import MVTensor` | `from pytanga.tensor import MVTensor` |
| `from pytanga import EProduct` | `from pytanga.enums import EProduct` |
| `from pytanga.solver.blade_masks import inverse_blade_mask` | `from pytanga.blade_mask.predict import inverse_blade_mask` |
| `from pytanga.solver.matrix_convert import to_matrix` | `from pytanga.matrix.convert import to_matrix` |
| `from pytanga.solver.matrix_product import product_matrix` | `from pytanga.matrix.product import product_matrix` |
| `from pytanga.solver.tensor_contract import contract` | `from pytanga.tensor.ops import contract` |
| `from pytanga.solver.tensor_convert import to_tensor` | `from pytanga.tensor.convert import to_tensor` |
| `from pytanga.solver.tensor_product import product_tensor` | `from pytanga.tensor.product import product_tensor` |
| `from pytanga.solver.solve import solve` | `from pytanga.solver.solve import solve` (unchanged) |
| `from pytanga.mv_utils import random_mask` | `from pytanga.mv_utils import random_mask` (unchanged) |

---

## 6. Files to Update (Consumers)

All files that import from old paths need updating.

### 6.1 Example Files

| File | Changes |
|---|---|
| `py/examples/solver_basics_01.py` | `from pytanga.product import EProduct` → `from pytanga.enums import EProduct`<br>`solver.matrix_convert` → `matrix.convert`<br>`solver.matrix_product` → `matrix.product`<br>`solver.solve` → `solver.solve` |
| `py/examples/solver_basics_02.py` | `solver.solve` → `solver.solve` (unchanged path) |
| `py/examples/solver_basics_03.py` | `solver.solve` → `solver.solve` (unchanged path) |
| `py/examples/solver_line_fitting_p2.py` | `solver.matrix_convert` → `matrix.convert`<br>`solver.matrix_product` → `matrix.product` |
| `py/examples/solver_point_line_p3.py` | `solver.blade_masks` → `blade_mask.predict`<br>`solver.matrix_convert` → `matrix.convert`<br>`solver.matrix_product` → `matrix.product` |
| `py/examples/solver_rotor_estimation.py` | `solver.matrix_convert` → `matrix.convert`<br>`solver.matrix_product` → `matrix.product` |
| `py/examples/tensor_basics_01.py` | `from pytanga.solver.tensor_product` → `from pytanga.tensor.product`<br>`solver.matrix_convert` → `matrix.convert` |
| All examples | `from pytanga.product import EProduct` → `from pytanga.enums import EProduct` |

### 6.2 Test Files

| File | Old Imports | New Imports |
|---|---|---|
| `test_blade_mask.py` | `pytanga.solver.blade_masks` | `pytanga.blade_mask.predict` |
| `test_matrix_conversion.py` | `pytanga.solver.matrix_convert` | `pytanga.matrix.convert` |
| `test_product_matrix.py` | `pytanga.solver.blade_masks`, `pytanga.solver.matrix_convert`, `pytanga.solver.matrix_product` | `pytanga.blade_mask.predict`, `pytanga.matrix.convert`, `pytanga.matrix.product` |
| `test_product_matrix_rev_conj.py` | `pytanga.solver.matrix_convert`, `pytanga.solver.matrix_product`<br>`pytanga.product import EProduct` | `pytanga.matrix.convert`, `pytanga.matrix.product`<br>`pytanga.enums import EProduct` |
| `test_product_matrix_einv.py` | `pytanga.solver.blade_masks`, `pytanga.solver.matrix_convert`, `pytanga.solver.matrix_product` | `pytanga.blade_mask.predict`, `pytanga.matrix.convert`, `pytanga.matrix.product` |
| `test_mv_tensor.py` | `pytanga.solver.tensor_contract`, `pytanga.solver.tensor_convert`, `pytanga.solver.tensor_product` | `pytanga.tensor.ops`, `pytanga.tensor.convert`, `pytanga.tensor.product` |
| `test_product_tensor.py` | `pytanga.solver.tensor_contract`, `pytanga.solver.tensor_convert`, `pytanga.solver.tensor_product`<br>`pytanga.product import EProduct` | `pytanga.tensor.ops`, `pytanga.tensor.convert`, `pytanga.tensor.product`<br>`pytanga.enums import EProduct` |
| `test_solve_float.py` | `pytanga.solver.solve`, `pytanga.product import EProduct` | `pytanga.solver.solve` (unchanged), `pytanga.enums import EProduct` |
| `test_solve_mod.py` | `pytanga.solver.solve` | `pytanga.solver.solve` (unchanged) |
| `test_least_squares.py` | `pytanga.solver.solve`, `pytanga.product import EProduct` | `pytanga.solver.solve` (unchanged), `pytanga.enums import EProduct` |
| `test_mvlike_coercion.py` | `pytanga.solver.matrix_convert`, `pytanga.solver.solve`<br>`pytanga.product import EInv` | `pytanga.matrix.convert`, `pytanga.solver.solve`<br>`pytanga.enums import EInv` |
| `test_blade_ops.py` | `pytanga.product import EProduct` | `pytanga.enums import EProduct` |
| `test_mvproductmatrix.py` | (uses `pytanga.product`?) | Check and update to `pytanga.enums` |
| `conftest.py` | Any `pytanga.product` imports | `pytanga.enums` |

### 6.3 pytanga Internal Files

| File | Change |
|---|---|
| `py/pytanga/__init__.py` | Update all imports: `product` → `enums`, class re-exports from submodules |
| `py/pytanga/blade_mask.py` | **DELETE** |
| `py/pytanga/mv_matrix.py` | **DELETE** |
| `py/pytanga/mv_product_matrix.py` | **DELETE** |
| `py/pytanga/mv_tensor.py` | **DELETE** |
| `py/pytanga/product.py` | **DELETE** (renamed to `enums.py`) |
| `py/pytanga/solver/_coerce.py` | **DELETE** (merged into `mv_utils.py`) |
| `py/pytanga/solver/_dispatch.py` | **DELETE** (split) |
| `py/pytanga/solver/__init__.py` | Unchanged (already empty) |
| `py/pytanga/mv_utils.py` | Add `MVLike` type alias and `_as_mv` function |
| `py/pytanga/algebra.py` | `from .product import EProduct` → `from .enums import EProduct` |
| `py/pytanga/mv.py` | `from .product import EProduct` → `from .enums import EProduct` (if present) |

### 6.4 Documentation

| File | Change |
|---|---|
| `docs/py/solver.md` | Update all import examples, class paths, and module structure documentation |
| `docs/py/index.md` | Update import examples if any reference old paths |

---

## 7. Implementation Steps

1. **Rename `product.py` → `enums.py`** (and update all internal references).
2. **Create `blade_mask/` directory:**
   - Move `blade_mask.py` → `blade_mask/_mask.py`, fix imports (single-dot → absolute).
   - Create `blade_mask/__init__.py` re-exporting `BladeMask`.
   - Move `_dispatch_product_blade_mask` from `solver/_dispatch.py` → `blade_mask/_dispatch.py`.
   - Move `solver/blade_masks.py` → `blade_mask/predict.py`, fix imports.
3. **Create `matrix/` directory:**
   - Move `mv_matrix.py` → `matrix/_data.py`, fix imports (single-dot → absolute).
   - Move `mv_product_matrix.py` → `matrix/_product_data.py`, fix imports (single-dot → absolute).
   - Create `matrix/__init__.py` re-exporting `MVMatrix`, `MVProductMatrix`.
   - Move `_dispatch_product_matrix*` functions from `solver/_dispatch.py` → `matrix/_dispatch.py`.
   - Move `solver/matrix_convert.py` → `matrix/convert.py`, fix imports.
   - Move `solver/matrix_product.py` → `matrix/product.py`, fix imports.
4. **Create `tensor/` directory:**
   - Move `mv_tensor.py` → `tensor/_data.py`, fix imports (single-dot → absolute).
   - Create `tensor/__init__.py` re-exporting `MVTensor`.
   - Move `solver/tensor_contract.py` → `tensor/ops.py`, fix imports.
   - Move `solver/tensor_convert.py` → `tensor/convert.py`, fix imports.
   - Move `solver/tensor_product.py` → `tensor/product.py`, fix imports.
5. **Merge `solver/_coerce.py` into `mv_utils.py`:** Copy `MVLike` and `_as_mv` into `mv_utils.py`.
6. **Delete orphan files:** `blade_mask.py`, `mv_matrix.py`, `mv_product_matrix.py`, `mv_tensor.py`, `product.py`, `solver/_coerce.py`, `solver/_dispatch.py`.
7. **Update `pytanga/__init__.py`** — update all imports.
8. **Update all consumer files** — examples, tests, `conftest.py`.
9. **Update `docs/py/solver.md`**.
10. **Run test suite** — `uv run python -m pytest py/tests/ -q`.

---

## 8. Design Decisions Summary

| Decision | Rationale |
|---|---|
| `product.py` → `enums.py` | Contains only enums; `enums.py` is self-documenting. |
| `BladeMask` → `blade_mask/_mask.py` | Resolves file/directory naming conflict; everything blade-mask-related in one place. |
| `MVMatrix` → `matrix/_data.py`, `MVProductMatrix` → `matrix/_product_data.py` | Classes belong with their operations. Underscore prefix = implementation detail, re-exported via `__init__.py`. |
| `MVTensor` → `tensor/_data.py` | Same rationale as matrix classes. |
| `_dispatch.py` split by domain | Blade mask dispatch (`_dispatch_product_blade_mask`) goes to `blade_mask/`; product matrix dispatch goes to `matrix/`. Each dispatch module lives with the code that calls it. |
| `_coerce.py` → merged into `mv_utils.py` | Only two items (a type alias and a single function). `mv_utils.py` is the natural home for utility functions. |
| `tensor_contract.py` → `tensor/ops.py` | General bucket for tensor→tensor operations (contract, future decompose, reshape, etc.). |
| `matrix/product.py` and `tensor/product.py` | Symmetric naming for building product matrices/tensors. |
| `solver/solve.py` unchanged | Already well-named: submodule is `solver`, file is `solve`. |
| Empty `__init__.py` in `solver/` | Users import from specific files; follows existing convention. |
| Re-export `__init__.py` in `blade_mask/`, `matrix/`, `tensor/` | Data classes are still importable from the submodule directly (e.g. `from pytanga.matrix import MVMatrix`). |
| Absolute imports for cross-module references | `from pytanga.blade_mask import BladeMask` instead of `from pytanga.blade_mask import BladeMask`. Single-dot relative imports kept for same-module references. |