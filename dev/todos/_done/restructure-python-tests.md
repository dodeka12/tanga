# Restructure `py/tests/` ✅ **COMPLETE**

## Overview

Restructured the Python test suite so that:
- Each submodule under `py/pytanga/` gets a corresponding subfolder under `py/tests/`
- Cross-module tests stay directly under `py/tests/`
- Phase-named test files are renamed to describe what they actually test
- All mentions of plans or plan phases are removed from docstrings/comments
- Long test files (>500-600 lines) are split into smaller, focused files
- No `__init__.py` files in test subfolders
- **Result: 554/555 tests pass. 1 pre-existing failure (`TestVisualizer.test_scene_property`) unrelated to restructure.**

---

## Phase 1 — Move/Rename Files (no content changes)

### Subfolders to create

```
py/tests/algebra/
py/tests/basis/
py/tests/blade_mask/
py/tests/codegen/
py/tests/geometry/
py/tests/matrix/
py/tests/solver/
py/tests/tensor/
```

(`py/tests/viz/` already exists.)

### File moves

| Source | Destination |
|---|---|
| `test_algebra_e3.py` | `algebra/test_algebra_e3.py` |
| `test_algebra_random.py` | `algebra/test_algebra_random.py` |
| `test_blade_names.py` | `algebra/test_blade_names.py` |
| `test_mvlike_coercion.py` | `algebra/test_mvlike_coercion.py` |
| `test_basis.py` | `basis/test_basis.py` |
| `test_blade_mask.py` | `blade_mask/test_blade_mask.py` |
| `test_blade_ops.py` | `codegen/test_blade_ops.py` |
| `test_cache.py` | `codegen/test_cache.py` |
| `test_geometry_e3.py` | `geometry/test_geometry_e3.py` |
| `test_geometry_n3.py` | `geometry/test_geometry_n3.py` |
| `test_geometry_n3_phase5.py` | → *merged into* `geometry/test_geometry_n3.py` (see Phase 2) |
| `test_geometry_p3.py` | `geometry/test_geometry_p3.py` |
| `test_geometry_phase6.py` | `geometry/test_geometry_convenience.py` |
| `test_matrix_conversion.py` | `matrix/test_matrix_conversion.py` |
| `test_mvproductmatrix.py` | `matrix/test_mvproductmatrix.py` |
| `test_least_squares.py` | `solver/test_least_squares.py` |
| `test_solve_float.py` | `solver/test_solve_float.py` |
| `test_solve_mod.py` | `solver/test_solve_mod.py` |
| `test_mv_tensor.py` | `tensor/test_mv_tensor.py` |
| `test_labeled_tensor.py` | `tensor/test_labeled_tensor.py` |
| `test_product_tensor.py` | `tensor/test_product_tensor.py` |
| `viz/test_phase1_session_scene.py` | `viz/test_scene_session.py` |
| `viz/test_phase2_serializer.py` | `viz/test_serializer.py` |
| `viz/__init__.py` | → *removed* |
| `__init__.py` | `__init__.py` (stays at root) |
| `conftest.py` | `conftest.py` (stays at root) |

### Files staying at `py/tests/` root (cross-module)
- `test_modular.py` — uses Algebra with integer modulus, cross-cutting
- (no `test_product_matrix*.py` files — these are all closely tied to matrix and will go under `matrix/`)

Wait — check `test_product_matrix.py`, `test_product_matrix_einv.py`, `test_product_matrix_rev_conj.py`. These test product matrices which live under `py/pytanga/matrix/`. Add them:
| `test_product_matrix.py` | `matrix/test_product_matrix.py` |
| `test_product_matrix_einv.py` | `matrix/test_product_matrix_einv.py` |
| `test_product_matrix_rev_conj.py` | `matrix/test_product_matrix_rev_conj.py` |

---

## Phase 2 — Content Changes

### 2a. Rename phase-named files and update docstrings

- `viz/test_phase1_session_scene.py` → `viz/test_scene_session.py`
  - Change module docstring from `"Tests for Phase 1: CameraConfig, SceneConfig, Scene, Visualizer basics."` to `"Tests for CameraConfig, SceneConfig, Scene, and Visualizer basics."`
  
- `viz/test_phase2_serializer.py` → `viz/test_serializer.py`
  - Change module docstring from `"Tests for Phase 2: Entity/Operator → JSON serializer."` to `"Tests for Entity/Operator → JSON serialization."`

- `test_geometry_n3_phase5.py` → merge into `geometry/test_geometry_n3.py`
  - Append content of `test_geometry_n3_phase5.py` to `geometry/test_geometry_n3.py`
  - Remove `"Phase 5 tests — missing N3 entities and operators."` docstring header
  - Remove the original `test_geometry_n3_phase5.py` file

- `test_geometry_phase6.py` → `geometry/test_geometry_convenience.py`
  - Change module docstring from `"Phase 6 tests — Geometry convenience class."` to `"Tests for the Geometry convenience class."`

### 2b. Split long files (>350 lines)

Need to read each file first to determine logical split points. Candidates:

| File | Lines |
|---|---|
| `test_product_tensor.py` | 611 |
| `test_labeled_tensor.py` | 547 |
| `test_geometry_e3.py` | 436 |
| `test_geometry_p3.py` | 441 |
| `viz/test_scene_session.py` (ex-phase1) | 377 |
| `viz/test_serializer.py` (ex-phase2) | 373 |
| `viz/test_imaginary_styles.py` | 345 |

**Approach:** Read each file to identify class/function groups, split at logical boundaries so each resulting file is ≤350 lines and has a clear area of concern.

---

## Phase 3 — Remove `__init__.py` Files

Remove any `__init__.py` files from test subfolders:
- `py/tests/viz/__init__.py` — remove
- No new `__init__.py` files created for new subfolders

Keep `py/tests/__init__.py` at root.

---

## Phase 4 — Run Tests & Fix Issues

After all moves and edits:
1. Run the full test suite: `cd py && python -m pytest tests/ -v`
2. Fix any import errors caused by relative imports that broke
3. Fix any collection issues
4. Verify all tests pass
5. Check for stale `.pyc` files under old paths and clean if needed

---

## Acceptance Criteria

- [ ] All test files moved to submodule folders according to the map above
- [ ] Phase-named files renamed to descriptive names
- [ ] All "Phase N" mentions removed from docstrings
- [ ] Long files split into focused files ≤350 lines each
- [ ] No `__init__.py` files in test subfolders (except root `py/tests/__init__.py`)
- [ ] Full test suite passes: `cd py && python -m pytest tests/ -v`
- [ ] `conftest.py` still works correctly for all tests
- [ ] No stale files remain at old paths