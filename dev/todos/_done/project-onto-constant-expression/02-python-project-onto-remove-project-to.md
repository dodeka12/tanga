# Phase 2 — Python `project_onto`, remove `project_to`, tests

## Goal

Add `Algebra.project_onto` / `MV.project_onto`, remove `project_to` from the
Python API and from C++/codegen, and update the algebra tests to the new,
correct direction.

## Files

- Edit: `py/pytanga/algebra/_algebra.py`
- Edit: `py/pytanga/algebra/_mv.py`
- Edit: `cpp/Tan.GA/MV_Operators.h`
- Edit: `cpp/Tan.GA/_CompileTest_Ops.cpp`
- Edit: `py/pytanga/codegen/_mv_operators.py`
- Edit: `py/pytanga/codegen/_generator.py`
- Edit: `py/pytanga/_template.cpp`
- Edit: `py/tests/algebra/test_galgebra_phase_c.py`

## Steps

- [x] **2.1 — Add Python `project_onto`**
  - In `py/pytanga/algebra/_algebra.py`, add:
    ```python
    def project_onto(self, a: MV, other: MV | BladeMask) -> MV:
        """Restrict *a* to a blade set.

        - ``MV`` — retain *a*'s blades that are non-zero in *other*.
        - ``BladeMask`` — retain *a*'s blades whose id is in ``other.ids``.
        """
        if isinstance(other, MV):
            return MV(self._mod.project_onto(a._impl, other._impl), self)
        if isinstance(other, BladeMask):
            return MV(self._mod.project_onto_mask(a._impl, other.ids), self)
        raise TypeError(
            f"project_onto expects MV or BladeMask, got {type(other).__name__}"
        )
    ```
  - In `py/pytanga/algebra/_mv.py`, add `MV.project_onto(other)` delegating to
    `self._alg.project_onto(self, other)`.
  - Confirm `BladeMask` is importable where needed (it already is in
    `_expression.py`; add the import to `_algebra.py` if not present).

- [x] **2.2 — Remove Python `project_to`**
  - Delete `Algebra.project_to` (`_algebra.py:713-746`) and `MV.project_to`
    (`_mv.py:269-276`).

- [x] **2.3 — Remove C++ `ProjectTo`**
  - In `cpp/Tan.GA/MV_Operators.h`, delete `ProjectTo` and `ProjectToBlade`.
  - In `cpp/Tan.GA/_CompileTest_Ops.cpp`, remove the `ProjectTo`/`ProjectToBlade`
    instantiation lines.

- [x] **2.4 — Remove the `project_to` binding**
  - In `py/pytanga/codegen/_mv_operators.py`, delete `project_to_def`.
  - In `py/pytanga/codegen/_generator.py`, drop the `project_to_def` import and
    the `sub_bare(template, "PROJECT_TO_DEF", ...)` line.
  - In `py/pytanga/_template.cpp`, delete the `{ { PROJECT_TO_DEF } }` block.

- [x] **2.5 — Rewrite tests**
  - In `py/tests/algebra/test_galgebra_phase_c.py`, replace
    `TestProjectToExtended` with `TestProjectOnto`:
    - MV: `a = s·1 + 1·e1 + 2·e2 + 3·e12`, `b = 1·e1 + 4·e12` →
      `a.project_onto(b)` keeps `e1` and `e12`, drops `e2`.
    - Direction guard: a case where `b` has a blade `a` lacks (proves it is
      `a`→`b`, not `b`→`a`).
    - BladeMask: `a.project_onto(BladeMask(alg, [1, 3]))` keeps exactly `e1`,
      `e12` (exact membership).

## Validation

`uv run pytest py/tests/algebra/test_galgebra_phase_c.py -q`

## Notes

- After this phase `project_to` is fully gone from the Python surface; the
  changelog records the breaking change in Phase 4.
- The binding recompiles on the first `Algebra(...)` in the test because the
  cache key changed again (C++/codegen/template removed `project_to`).
