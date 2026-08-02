# pytanga Submodule Restructuring — Implementation Plan

> References design document: [pytanga-submodule-restructure.md](pytanga-submodule-restructure.md)

This file is a step-by-step implementation checklist. Each step is ordered by dependency.
Complete each step fully before moving to the next.

---

## Step 1: Rename `product.py` → `enums.py` ✅

1. **Copy** `py/pytanga/product.py` → `py/pytanga/enums.py` (no content changes — the file
   contains only `EProduct` and `EInv` enum classes. Update the module docstring from
   `pytanga._product` to `pytanga.enums`).

2. **Find all files** under `py/` and `docs/` that import from `pytanga.product` or
   reference `product.py`:

   ```bash
   grep -rn "from pytanga.product import" py/ docs/
   grep -rn "from \.product import" py/pytanga/
   grep -rn "\.product\b" py/pytanga/algebra.py py/pytanga/mv.py
   ```

3. **Update all references** — replace `pytanga.product` → `pytanga.enums` and
   `.product` → `.enums` in every file found.

4. **DO NOT delete `product.py` yet** — keep it until all internal files are updated.

---

## Step 2: Create `blade_mask/` submodule

1. **Create directory:** `py/pytanga/blade_mask/`

2. **Create `py/pytanga/blade_mask/__init__.py`:**

   ```python
   from ._mask import BladeMask

   __all__ = ["BladeMask"]
   ```

3. **Move `blade_mask.py` → `blade_mask/_mask.py`:**
   - Copy file content from `py/pytanga/blade_mask.py` to `py/pytanga/blade_mask/_mask.py`.
   - Update all imports from single-dot relative to absolute:
     - `from ._blade_names import blade_name` → `from pytanga._blade_names import blade_name`
     - `from ._blade_names import grade as _grade` → `from pytanga._blade_names import grade as _grade`
     - `from ._parse import _parse_mv_string` → `from pytanga._parse import _parse_mv_string`
     - `from .algebra import Algebra` → `from pytanga.algebra import Algebra`
     - `from .mv import MV` → `from pytanga.mv import MV`
   - Update the module docstring from `pytanga._blade_mask` to `pytanga.blade_mask._mask`.

4. **Create `py/pytanga/blade_mask/_dispatch.py`:**
   - Extract the `_dispatch_product_blade_mask` function from `py/pytanga/solver/_dispatch.py`.
   - Update its imports to absolute:
     - `from pytanga.product import EProduct` → `from pytanga.enums import EProduct`
   - Also extract any `TYPE_CHECKING` imports it needs (check original file).

5. **Move `solver/blade_masks.py` → `blade_mask/predict.py`:**
   - Copy file content from `py/pytanga/solver/blade_masks.py` to `py/pytanga/blade_mask/predict.py`.
   - Update imports:
     - `from pytanga.blade_mask import BladeMask` → `from pytanga.blade_mask import BladeMask`
     - `from pytanga.product import EProduct` → `from pytanga.enums import EProduct`
     - `from ._dispatch import _dispatch_product_blade_mask` → `from ._dispatch import _dispatch_product_blade_mask` (single-dot, sibling — stays the same)
   - Update the module docstring from `pytanga.solver.blade_masks` to `pytanga.blade_mask.predict`.

---

## Step 3: Create `matrix/` submodule

1. **Create directory:** `py/pytanga/matrix/`

2. **Create `py/pytanga/matrix/__init__.py`:**

   ```python
   from ._data import MVMatrix
   from ._product_data import MVProductMatrix

   __all__ = ["MVMatrix", "MVProductMatrix"]
   ```

3. **Move `mv_matrix.py` → `matrix/_data.py`:**
   - Copy file content from `py/pytanga/mv_matrix.py` to `py/pytanga/matrix/_data.py`.
   - Update imports:
     - `from .blade_mask import BladeMask` → `from pytanga.blade_mask import BladeMask`
   - Update the module docstring.

4. **Move `mv_product_matrix.py` → `matrix/_product_data.py`:**
   - Copy file content from `py/pytanga/mv_product_matrix.py` to `py/pytanga/matrix/_product_data.py`.
   - Update imports:
     - `from .blade_mask import BladeMask` → `from pytanga.blade_mask import BladeMask`
     - `from .product import EInv, EProduct` → `from pytanga.enums import EInv, EProduct`
   - Update the module docstring.

5. **Create `py/pytanga/matrix/_dispatch.py`:**
   - Extract the three `_dispatch_product_matrix*` functions from `py/pytanga/solver/_dispatch.py`:
     - `_dispatch_product_matrix`
     - `_dispatch_product_matrix_masked`
     - `_dispatch_product_matrix_array`
   - Also copy `import numpy as np` and any `TYPE_CHECKING` imports.
   - Update imports:
     - `from pytanga.product import EInv, EProduct` → `from pytanga.enums import EInv, EProduct`

6. **Move `solver/matrix_convert.py` → `matrix/convert.py`:**
   - Copy file content.
   - Update imports:
     - `from pytanga.blade_mask import BladeMask` → `from pytanga.blade_mask import BladeMask`
     - `from pytanga.mv import MV` → `from pytanga.mv import MV`
     - `from pytanga.mv_matrix import MVMatrix` → `from . import MVMatrix` (single-dot via `__init__`)
     - `from ._coerce import MVLike, _as_mv` → `from pytanga.mv_utils import MVLike, _as_mv`
     - Remove `from pytanga.algebra import Algebra` if only used via `TYPE_CHECKING` —
       add `from pytanga.algebra import Algebra` under `if TYPE_CHECKING:`.
   - Update the module docstring.

7. **Move `solver/matrix_product.py` → `matrix/product.py`:**
   - Copy file content.
   - Update imports:
     - `from pytanga.blade_mask import BladeMask` → `from pytanga.blade_mask import BladeMask`
     - `from pytanga.mv_product_matrix import MVProductMatrix` → `from . import MVProductMatrix`
     - `from pytanga.product import EInv, EProduct` → `from pytanga.enums import EInv, EProduct`
     - `from ._coerce import MVLike, _as_mv` → `from pytanga.mv_utils import MVLike, _as_mv`
     - `from ._dispatch import _dispatch_product_matrix_masked` → `from ._dispatch import _dispatch_product_matrix_masked` (sibling — unchanged)
     - `from .blade_masks import product_blade_mask` → `from pytanga.blade_mask.predict import product_blade_mask`
     - Remove/update `from pytanga.algebra import Algebra` → `from pytanga.algebra import Algebra` under `TYPE_CHECKING`.
   - Update the module docstring.

---

## Step 4: Create `tensor/` submodule

1. **Create directory:** `py/pytanga/tensor/`

2. **Create `py/pytanga/tensor/__init__.py`:**

   ```python
   from ._data import MVTensor

   __all__ = ["MVTensor"]
   ```

3. **Move `mv_tensor.py` → `tensor/_data.py`:**
   - Copy file content from `py/pytanga/mv_tensor.py` to `py/pytanga/tensor/_data.py`.
   - Update imports:
     - `from .blade_mask import BladeMask` → `from pytanga.blade_mask import BladeMask`
   - Update the module docstring.

4. **Move `solver/tensor_contract.py` → `tensor/ops.py`:**
   - Copy file content.
   - Update imports:
     - `from pytanga.blade_mask import BladeMask` → `from pytanga.blade_mask import BladeMask`
     - `from pytanga.mv_tensor import MVTensor` → `from . import MVTensor`
   - Update the module docstring.

5. **Move `solver/tensor_convert.py` → `tensor/convert.py`:**
   - Copy file content.
   - Update imports:
     - `from pytanga.blade_mask import BladeMask` → `from pytanga.blade_mask import BladeMask`
     - `from pytanga.mv import MV` → `from pytanga.mv import MV`
     - `from pytanga.mv_tensor import MVTensor` → `from . import MVTensor`
     - `from ._coerce import MVLike, _as_mv` → `from pytanga.mv_utils import MVLike, _as_mv`
     - `from .matrix_convert import to_matrix` → `from pytanga.matrix.convert import to_matrix`
     - Update TYPE_CHECKING algebra imports.
   - Update the module docstring.

6. **Move `solver/tensor_product.py` → `tensor/product.py`:**
   - Copy file content.
   - Update imports:
     - `from pytanga.blade_mask import BladeMask` → `from pytanga.blade_mask import BladeMask`
     - `from pytanga.mv_tensor import MVTensor` → `from . import MVTensor`
     - `from pytanga.product import EProduct` → `from pytanga.enums import EProduct`
     - `from .blade_masks import product_blade_mask` → `from pytanga.blade_mask.predict import product_blade_mask`
   - Update the module docstring.

---

## Step 5: Merge `solver/_coerce.py` into `mv_utils.py`

1. **Open `py/pytanga/mv_utils.py`.**

2. **Add the contents of `solver/_coerce.py`:**
   - Add `from typing import TYPE_CHECKING, Union` at the top (if not already present).
   - Add `from pytanga.algebra import Algebra` under `if TYPE_CHECKING:`.
   - Add the `MVLike` type alias.
   - Add the `_as_mv` function.
   - Ensure `_as_mv` uses the lazy import pattern already in the file (the original
     `_coerce.py` does `from pytanga.mv import MV as _MV` inside the function — update this to
     `from pytanga.mv import MV as _MV`).

3. **Update `mv_utils.py`'s existing imports** — it currently uses absolute imports
   (`from pytanga.algebra import Algebra`, etc.). These are fine, keep them.

---

## Step 6: Fix imports in `solver/solve.py`

1. **Open `py/pytanga/solver/solve.py`.**

2. **Update all imports:**
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
   from pytanga.matrix import MVMatrix
   from pytanga.enums import EProduct
   from pytanga.mv_utils import MVLike, _as_mv
   from pytanga.blade_mask.predict import inverse_blade_mask, product_blade_mask
   from pytanga.matrix.convert import from_matrix, to_matrix
   from pytanga.matrix.product import product_matrix as build_product_matrix
   ```

3. **Also update TYPE_CHECKING imports** for `Algebra` — change `from pytanga.algebra import Algebra` to `from pytanga.algebra import Algebra`.

---

## Step 7: Update `py/pytanga/__init__.py`

1. **Open `py/pytanga/__init__.py`.**

2. **Replace the imports section:**
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
   from .blade_mask import BladeMask     # via blade_mask/__init__.py
   from .codegen import precompile
   from .enums import EProduct
   from .matrix import MVMatrix, MVProductMatrix  # via matrix/__init__.py
   from .mv import MV
   from .mv_utils import random_mask, random_mv
   from .tensor import MVTensor          # via tensor/__init__.py
   ```

3. **Update `__all__`** if it lists individual items — ensure `EProduct`, `MVMatrix`,
   `MVProductMatrix`, `MVTensor` are still listed (they are).

---

## Step 8: Update `algebra.py` and `mv.py`

1. **Check `py/pytanga/algebra.py`** for `from .product import EProduct` or
   `from pytanga.product import EProduct` — replace with `from pytanga.enums import EProduct`.

2. **Check `py/pytanga/mv.py`** for any `product` import references — same change.

3. **Search for any remaining `pytanga.product` references** in all `.py` files under
   `py/pytanga/`:

   ```bash
   grep -rn "pytanga\.product\b" py/pytanga/
   ```

   Replace any remaining occurrences with `pytanga.enums`.

---

## Step 9: Delete old files

Once all new files are in place and imports are updated, delete:

| Old File | Reason |
|---|---|
| `py/pytanga/product.py` | Renamed to `enums.py` |
| `py/pytanga/blade_mask.py` | Moved to `blade_mask/_mask.py` |
| `py/pytanga/mv_matrix.py` | Moved to `matrix/_data.py` |
| `py/pytanga/mv_product_matrix.py` | Moved to `matrix/_product_data.py` |
| `py/pytanga/mv_tensor.py` | Moved to `tensor/_data.py` |
| `py/pytanga/solver/_coerce.py` | Merged into `mv_utils.py` |
| `py/pytanga/solver/_dispatch.py` | Split into `blade_mask/_dispatch.py` and `matrix/_dispatch.py` |
| `py/pytanga/solver/blade_masks.py` | Moved to `blade_mask/predict.py` |
| `py/pytanga/solver/matrix_convert.py` | Moved to `matrix/convert.py` |
| `py/pytanga/solver/matrix_product.py` | Moved to `matrix/product.py` |
| `py/pytanga/solver/tensor_contract.py` | Moved to `tensor/ops.py` |
| `py/pytanga/solver/tensor_convert.py` | Moved to `tensor/convert.py` |
| `py/pytanga/solver/tensor_product.py` | Moved to `tensor/product.py` |

`solver/solve.py` and `solver/__init__.py` stay in place.

---

## Step 10: Update test files

Update imports in every test file listed below. Use the old→new mapping from the
[design document, section 6.2](pytanga-submodule-restructure.md#62-test-files).

### Files with path changes:

| File | Updates |
|---|---|
| `py/tests/test_blade_mask.py` | `from pytanga.solver.blade_masks import product_blade_mask` → `from pytanga.blade_mask.predict import product_blade_mask` |
| `py/tests/test_matrix_conversion.py` | `from pytanga.solver.matrix_convert import from_matrix, to_matrix` → `from pytanga.matrix.convert import from_matrix, to_matrix` |
| `py/tests/test_product_matrix.py` | `solver.blade_masks` → `blade_mask.predict`; `solver.matrix_convert` → `matrix.convert`; `solver.matrix_product` → `matrix.product` |
| `py/tests/test_product_matrix_rev_conj.py` | `solver.matrix_convert` → `matrix.convert`; `solver.matrix_product` → `matrix.product`; `pytanga.product` → `pytanga.enums` |
| `py/tests/test_product_matrix_einv.py` | `solver.blade_masks` → `blade_mask.predict`; `solver.matrix_convert` → `matrix.convert`; `solver.matrix_product` → `matrix.product` |
| `py/tests/test_mv_tensor.py` | `solver.tensor_contract` → `tensor.ops`; `solver.tensor_convert` → `tensor.convert`; `solver.tensor_product` → `tensor.product` |
| `py/tests/test_product_tensor.py` | `solver.tensor_contract` → `tensor.ops`; `solver.tensor_convert` → `tensor.convert`; `solver.tensor_product` → `tensor.product`; `pytanga.product` → `pytanga.enums` |
| `py/tests/test_solve_float.py` | `pytanga.product import EProduct` → `pytanga.enums import EProduct` |
| `py/tests/test_solve_mod.py` | No path change needed (`solver.solve` stays). Check for `pytanga.product`/`EProduct` references. |
| `py/tests/test_least_squares.py` | `pytanga.product import EProduct` → `pytanga.enums import EProduct` |
| `py/tests/test_mvlike_coercion.py` | `solver.matrix_convert` → `matrix.convert`; `pytanga.product import EInv` → `pytanga.enums import EInv` |
| `py/tests/test_blade_ops.py` | `pytanga.product import EProduct` → `pytanga.enums import EProduct` |
| `py/tests/test_mvproductmatrix.py` | Check for old `pytanga.solver.*` or `pytanga.product` imports and update. |

### Files with no path changes but need `product` → `enums`:

Run a global search:

```bash
grep -rn "from pytanga\.product import\|from pytanga import.*EProduct\|from pytanga import.*EInv" py/tests/
```

Update any matches to `from pytanga.enums import ...`.

### `conftest.py`:

Check for `from pytanga.product import` or `from pytanga import.*EProduct` and update to
`from pytanga.enums import`.

---

## Step 11: Update example files

Update imports in every example file. Use the old→new mapping from the
[design document, section 6.1](pytanga-submodule-restructure.md#61-example-files).

| File | Updates |
|---|---|
| `py/examples/solver_basics_01.py` | `solver.matrix_convert` → `matrix.convert`; `solver.matrix_product` → `matrix.product`; `pytanga.product` → `pytanga.enums` |
| `py/examples/solver_basics_02.py` | No path changes needed. Check for `pytanga.product`. |
| `py/examples/solver_basics_03.py` | No path changes needed. Check for `pytanga.product`. |
| `py/examples/solver_line_fitting_p2.py` | `solver.matrix_convert` → `matrix.convert`; `solver.matrix_product` → `matrix.product` |
| `py/examples/solver_point_line_p3.py` | `solver.blade_masks` → `blade_mask.predict`; `solver.matrix_convert` → `matrix.convert`; `solver.matrix_product` → `matrix.product` |
| `py/examples/solver_rotor_estimation.py` | `solver.matrix_convert` → `matrix.convert`; `solver.matrix_product` → `matrix.product` |
| `py/examples/tensor_basics_01.py` | `solver.tensor_product` → `tensor.product`; `solver.matrix_convert` → `matrix.convert` |

Global check for any remaining old paths:

```bash
grep -rn "pytanga\.solver\.\w\+" py/examples/
grep -rn "pytanga\.product" py/examples/
```

---

## Step 12: Update documentation

### 12.1 `docs/py/solver.md`

This is the main solver documentation. Update:

1. **Module structure overview** — replace the old documentation of `pytanga.solver.PRODUCT` etc.
   with the new submodule table:

   ```markdown
   ## Submodule Structure

   | Submodule | File | Functions |
   |---|---|---|
   | `pytanga.blade_mask` | `predict.py` | `inverse_blade_mask`, `product_blade_mask` |
   | `pytanga.matrix` | `convert.py` | `to_matrix`, `from_matrix` |
   | `pytanga.matrix` | `product.py` | `product_matrix`, `product_matrix_rev`, `product_matrix_conj` |
   | `pytanga.tensor` | `convert.py` | `to_tensor`, `from_tensor` |
   | `pytanga.tensor` | `product.py` | `product_tensor` |
   | `pytanga.tensor` | `ops.py` | `contract` |
   | `pytanga.solver` | `solve.py` | `solve`, `solve_lsq`, `solve_mod` |
   ```

2. **Class references** — `MVSolver` class no longer exists. Update all references to
   point to the new module paths. The doc should describe free functions, not a class.
   For example: `solver.product_matrix(...)` → `pytanga.matrix.product.product_matrix(alg, ...)`.

3. **Import examples** — update all code blocks:
   - `from pytanga import MVSolver` → remove
   - `slv = MVSolver(alg)` / `alg.solver` → remove
   - `slv.product_matrix(...)` → `from pytanga.matrix.product import product_matrix` + `product_matrix(alg, ...)`
   - `slv.to_matrix(...)` → `from pytanga.matrix.convert import to_matrix` + `to_matrix(alg, ...)`
   - `slv.solve(...)` → `from pytanga.solver.solve import solve` + `solve(alg, ...)`
   - `from pytanga.product import EInv` → `from pytanga.enums import EInv`

4. **MVMatrix, MVProductMatrix, MVTensor paths** — update from `pytanga.MVMatrix` to
   `pytanga.matrix.MVMatrix` (or note it's still importable from `pytanga`).

5. **BladeMask path** — note it can be imported from `pytanga.blade_mask` or
   `pytanga.BladeMask`.

### 12.2 `docs/py/index.md`

1. Check for any references to `pytanga.solver.*`, `pytanga.product`, `MVSolver`.
2. Update import examples in the quick start / overview sections.

### 12.3 Other documentation files

Search for old paths across all docs:

```bash
grep -rn "pytanga\.product\b" docs/
grep -rn "pytanga\.solver\.\w\+" docs/
grep -rn "MVSolver" docs/
```

Update any matches.

---

## Step 13: Verification

1. **Run the test suite:**

   ```bash
   uv run python -m pytest py/tests/ -q
   ```

   All tests should pass. If any fail:
   - Check for missed import updates.
   - Check for stale `.pyc` files — `rm -rf py/pytanga/__pycache__ py/pytanga/*/__pycache__`.
   - Ensure all `__init__.py` files export the correct symbols.

2. **Run each example script:**

   ```bash
   uv run python py/examples/solver_basics_01.py
   uv run python py/examples/solver_basics_02.py
   uv run python py/examples/solver_basics_03.py
   uv run python py/examples/solver_line_fitting_p2.py
   uv run python py/examples/solver_point_line_p3.py
   uv run python py/examples/solver_rotor_estimation.py
   uv run python py/examples/tensor_basics_01.py
   ```

3. **Verify direct imports work:**

   ```bash
   uv run python -c "
   from pytanga.blade_mask import BladeMask
   from pytanga.blade_mask.predict import inverse_blade_mask, product_blade_mask
   from pytanga.matrix import MVMatrix, MVProductMatrix
   from pytanga.matrix.convert import to_matrix, from_matrix
   from pytanga.matrix.product import product_matrix, product_matrix_rev, product_matrix_conj
   from pytanga.tensor import MVTensor
   from pytanga.tensor.convert import to_tensor, from_tensor
   from pytanga.tensor.product import product_tensor
   from pytanga.tensor.ops import contract
   from pytanga.solver.solve import solve, solve_lsq, solve_mod
   from pytanga.enums import EProduct, EInv
   from pytanga.mv_utils import random_mask, random_mv, MVLike, _as_mv
   print('All imports successful')
   "
   ```

4. **Verify backward-compatible top-level imports:**

   ```bash
   uv run python -c "
   import pytanga
   print(pytanga.BladeMask)
   print(pytanga.MVMatrix)
   print(pytanga.MVProductMatrix)
   print(pytanga.MVTensor)
   print(pytanga.EProduct)
   print(pytanga.random_mask)
   print(pytanga.random_mv)
   print('Top-level imports OK')
   "
   ```

5. **Clean up stale bytecode:**

   ```bash
   find py/pytanga -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
   ```

---

## Summary of Files Touched

### Created (14 files):
- `py/pytanga/enums.py`
- `py/pytanga/blade_mask/__init__.py`
- `py/pytanga/blade_mask/_mask.py`
- `py/pytanga/blade_mask/_dispatch.py`
- `py/pytanga/blade_mask/predict.py`
- `py/pytanga/matrix/__init__.py`
- `py/pytanga/matrix/_data.py`
- `py/pytanga/matrix/_product_data.py`
- `py/pytanga/matrix/_dispatch.py`
- `py/pytanga/matrix/convert.py`
- `py/pytanga/matrix/product.py`
- `py/pytanga/tensor/__init__.py`
- `py/pytanga/tensor/_data.py`
- `py/pytanga/tensor/convert.py`
- `py/pytanga/tensor/product.py`
- `py/pytanga/tensor/ops.py`

### Deleted (13 files):
- `py/pytanga/product.py`
- `py/pytanga/blade_mask.py`
- `py/pytanga/mv_matrix.py`
- `py/pytanga/mv_product_matrix.py`
- `py/pytanga/mv_tensor.py`
- `py/pytanga/solver/_coerce.py`
- `py/pytanga/solver/_dispatch.py`
- `py/pytanga/solver/blade_masks.py`
- `py/pytanga/solver/matrix_convert.py`
- `py/pytanga/solver/matrix_product.py`
- `py/pytanga/solver/tensor_contract.py`
- `py/pytanga/solver/tensor_convert.py`
- `py/pytanga/solver/tensor_product.py`

### Modified (18+ files):
- `py/pytanga/__init__.py`
- `py/pytanga/algebra.py`
- `py/pytanga/mv.py` (if it imports from `product`)
- `py/pytanga/mv_utils.py` (merged `_coerce.py`)
- `py/pytanga/solver/solve.py`
- `py/tests/test_blade_mask.py`
- `py/tests/test_matrix_conversion.py`
- `py/tests/test_product_matrix.py`
- `py/tests/test_product_matrix_rev_conj.py`
- `py/tests/test_product_matrix_einv.py`
- `py/tests/test_mv_tensor.py`
- `py/tests/test_product_tensor.py`
- `py/tests/test_solve_float.py`
- `py/tests/test_solve_mod.py`
- `py/tests/test_least_squares.py`
- `py/tests/test_mvlike_coercion.py`
- `py/tests/test_blade_ops.py`
- `py/tests/test_mvproductmatrix.py`
- `py/tests/conftest.py`
- `py/examples/solver_basics_01.py`
- `py/examples/solver_basics_02.py`
- `py/examples/solver_basics_03.py`
- `py/examples/solver_line_fitting_p2.py`
- `py/examples/solver_point_line_p3.py`
- `py/examples/solver_rotor_estimation.py`
- `py/examples/tensor_basics_01.py`
- `docs/py/solver.md`
- `docs/py/index.md`