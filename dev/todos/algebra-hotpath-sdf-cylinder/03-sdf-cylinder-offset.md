# Phase 3 — Fix SDF cylinder `align_center` offset

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make `SdfObject(Cylinder(...))` place the cylinder's base at `origin` for
`align_center=0.0`, matching the mesh renderer and the documented semantics
(report `_input/pytanga-sdf-cylinder-align-center-offset-bug.md`).

## Files

- Edit: `py/pytanga/viz/sdf/object.py`
- Edit: `py/tests/viz/sdf/test_sdf_object.py`

## Steps

- [x] **3.1 — Fix the offset formula**
  - In `py/pytanga/viz/sdf/object.py::_cylinder_node`, change:
    ```python
    offset = half * (0.5 - float(entity.align_center))
    ```
    to:
    ```python
    offset = float(entity.length) * (0.5 - float(entity.align_center))
    ```
  - Keep `half = float(entity.length) / 2.0` — it is still passed to
    `capped_cylinder(half, ...)` as the half-height.

- [x] **3.2 — Update the test that encoded the bug**
  - In `py/tests/viz/sdf/test_sdf_object.py::test_entity_to_sdf_cylinder_align_zero`,
    change the assertion from the buggy `[0.0, 0.75, 0.0]` to the correct
    `[0.0, 1.5, 0.0]` (length 3.0 → midpoint at `length/2`). The comment already
    states the correct expectation.

- [x] **3.3 — Add an intermediate `align_center` case**
  - Add `test_entity_to_sdf_cylinder_align_quarter` with `length=4.0`,
    `align_center=0.25`, `axis=Direction(0, 1, 0)`, asserting
    `node.transform["position"] == [0.0, 1.0, 0.0]` (offset =
    `4.0 * (0.5 - 0.25) = 1.0`; midpoint at `origin + axis * 1.0`).
  - The `align_center=0.5` case (`test_entity_to_sdf_cylinder_centered`) is
    already correct and stays unchanged.

## Validation

```
uv run pytest py/tests/viz/sdf/test_sdf_object.py -q
uv run ruff check py/pytanga/viz/sdf/object.py py/tests/viz/sdf/test_sdf_object.py
```

## Notes

- The mesh path (`_decompose.py`) already uses `length * (0.5 - align_center)`;
  this change brings the SDF path in line with it, so both renderers agree for
  every `align_center`, not just `0.5`.
- No public API change: `Cylinder.align_center` docs already describe the
  corrected behavior.
