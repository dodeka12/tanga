# Phase 3 — `Transform.from_operator()` + public export

## Goal

Let callers build a `pytanga.viz` `Transform` directly from a GA operator
(`Translator | Rotor | GeneralRotor | Motor | Dilator`), and import `Transform`
from the public `pytanga.viz` namespace instead of the private
`pytanga.viz._nodes`.

## Files

- Edit: `py/pytanga/viz/_nodes.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/tests/viz/test_nodes.py`

## Steps

- [x] **3.1 — Add `Transform.from_operator` classmethod**
  - In `_nodes.py`, in `class Transform` (after `from_matrix`, ~line 144), add:
    ```python
    @classmethod
    def from_operator(cls, op: TransformOperator) -> "Transform":
        return cls().set_matrix(_T.operator_to_matrix(op))
    ```
  - `TransformOperator` and `_T` (`from . import _transforms as _T`) are already
    imported at module top; `operator_to_matrix` is the same conversion
    `VizSceneObject.apply_transform()` already uses.

- [x] **3.2 — Export `Transform` from `pytanga.viz`**
  - In `py/pytanga/viz/__init__.py`, add `Transform` to the
    `from ._nodes import VizGroup, VizOverlayObject, VizSceneObject` line.
  - Add `"Transform"` to `__all__` (alphabetical, before `"TranslatorStyle"`).

- [x] **3.3 — Tests**
  - In `test_nodes.py`, add to `TestTransform`:
    - `Transform.from_operator(Translator(...))` equals
      `Transform().set_matrix(_transforms.operator_to_matrix(op))` (compare
      `.to_dict()`), and `from pytanga.viz import Transform` resolves (public
      export).
    - A `Rotor` and a `Motor` round-trip via `from_operator` to the expected
      TRS (`position`/`rotation`/`scale`), verified against
      `operator_to_matrix`/`operator_to_trs`.

## Validation

`uv run pytest py/tests/viz/test_nodes.py -q`

## Notes

- This removes the need for the `FrameTransform` workaround (hand-built 4×4
  matrix) and the private `pytanga.viz._nodes.Transform` import described in the
  note.
- `Transform` is a TRS node; `from_operator` inherits the existing
  `operator_to_matrix` behavior (decompose back to Euler-XYZ + scale), so a
  `Dilator` yields a scale, a `Rotor` a rotation, etc.
