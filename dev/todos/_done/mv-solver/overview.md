# MVSolver — Overview

> **Always consider the developer docs** under `docs/dev/` when implementing any step in this plan.  
> In particular: the [Python Coding Style Guide](../../../docs/dev/guides/py-coding-style-guide.md) and [C++ Coding Style Guide](../../../docs/dev/guides/cpp-coding-style-guide.md).  
> Also review any relevant architecture docs, use-case examples, and best practice documentation found there.

## Goal

Expose the product-matrix and equation-solving machinery from
`Tan.GA/Matrix_MapToBladeMask.h` as a clean Python API in pytanga.
The feature is delivered as a standalone `MVSolver` class that wraps an
`Algebra` instance, keeping all linear-algebra logic out of `Algebra` itself.

Design references:
- [Product matrices — API and math](../../../docs/cpp/product-matrices.md)
- [Matrix mapping and equation solving](../../../docs/cpp/matrix-mapping-and-equations.md)

## Deliverables

- `py/pytanga/_parse.py` — `_parse_mv_string` extracted from `algebra.py`
- `py/pytanga/blade_mask.py` — `BladeMask` class
- `py/pytanga/mv_matrix.py` — `MVMatrix` dataclass
- `py/pytanga/solver.py` — `MVSolver` class
- Extended `py/pytanga/_template.cpp` and `py/pytanga/_codegen.py` — new C++ binding functions for blade-mask and matrix operations
- `Algebra.solver` property and `Algebra.random_mv()` method — the only additions to `algebra.py`
- `py/tests/test_solver.py` — unit tests
- Updated `py/pytanga/__init__.py` — export `BladeMask`, `MVMatrix`, and `MVSolver`
- `py/examples/solver_basics.py`, `solver_line_fitting_p2.py`, `solver_rotor_estimation.py`

---

## Phases

| # | Phase | Description |
|---|-------|-------------|
| 1 | [BladeMask, MVMatrix, and parse utilities](./phase-1-mvmatrix.md) ✓ | Extract `_parse_mv_string` to `_parse.py`; `BladeMask` in `blade_mask.py`; `MVMatrix` in `mv_matrix.py` |
| 2 | [C++ binding additions](./phase-2-cpp-bindings.md) ✓ | New free functions in `_template.cpp` / `_codegen.py`: blade-mask prediction, matrix conversion, product-matrix construction, and modular-integer solve |
| 3 | [MVSolver class](./phase-3-mvsolver.md) ✓ | The Python `MVSolver` class in `solver.py`, including all high-level solver methods and `blade_mask_from_str` |
| 4 | [Integration](./phase-4-integration.md) ✓ | Wire `Algebra.solver`, update `__init__.py` exports, and add `numpy` to declared dependencies |
| 5 | [Tests](./phase-5-tests.md) ✓ | Unit tests covering blade-mask utilities, matrix round-trip, product-matrix correctness, and all solver paths |
| 6 | [Developer documentation](./phase-6-docs.md) ✓ | Update `docs/cpp/` and `docs/py/` to reflect the new API |
| 7 | [Example scripts](./phase-7-examples.md) ✓ | Three `py/examples/` scripts: solver basics, P2 line fitting, and rotor estimation |

---

## Ordering Rationale

**Circular-import prevention.**
`_parse.py` has no pytanga imports.  `blade_mask.py` imports only `_parse`
and uses `TYPE_CHECKING` for `Algebra` and `MV`.  `mv_matrix.py` imports
only `_blade_mask`.  `algebra.py` lazy-imports `BladeMask` inside methods.
This gives a strict DAG with no cycles.

**Phase 1 before everything else.** `MVMatrix` is a pure-Python dataclass with
no dependencies. It is the return type used by phases 3 and 4, so it must exist
first.

**Phase 2 before Phase 3.** `MVSolver` delegates every blade-mask and matrix
call to the compiled C++ binding. The new binding functions must exist before
`MVSolver` can be written and tested.

**Phase 3 before Phase 4.** `Algebra.solver` is a property that returns
`MVSolver(self)`. `MVSolver` must be importable before the property can be
added.

**Phase 4 before Phase 5.** Tests use the complete public API surface; all
pieces must be wired together first.

**Phase 5 before Phase 6.** Documentation is written after the verified,
working API; it describes what was built.

**Phase 6 before Phase 7.** Example scripts are written last, after the
documentation establishes the intended usage patterns.  The scripts also
serve as living documentation, so they are best written with the reference
docs in hand.

---

## Architecture Notes

**No new C++ library.** All new C++ code is added to `_template.cpp` and
generated via `_codegen.py`. The compiled per-algebra binding already links
the required TanGA headers (`Matrix_MapToBladeMask.h`, `Matrix.Algo.GE.h`).

**Blade masks are `list[int]`.** `std::vector<uint32_t>` is auto-converted by
pybind11's STL support (already included). No `CBladeMask` wrapper class is
needed in Python.

**Matrices are `numpy.ndarray`.** `pybind11/numpy.h` (`py::array_t<CTYPE>`) is
added to the template. numpy is added as a declared dependency of pytanga.

**Float solving stays in Python.** `numpy.linalg.solve` and
`numpy.linalg.lstsq` handle float systems. Only modular-integer solving
requires a new C++ binding (`solve_mod`), because numpy has no modular GE.

**`product` string dispatch.** All `MVSolver` methods that accept a `product`
keyword (`'gp'`, `'ip'`, `'op'`) dispatch internally to the corresponding
C++ binding call (`product_matrix_gp`, etc.).
