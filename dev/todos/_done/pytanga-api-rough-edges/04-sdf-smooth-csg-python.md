# Phase 4 — smooth CSG: Python model + serializer

## Goal

Add smooth combine modes (`smooth_union`/`smooth_intersection`/`smooth_subtract`)
and a per-member `smoothness` value to the standard viewer's SDF object model,
so `Composed`/`SdfGroup`/`Combine` can request rounded, blended joins that flow
to the wire as a `smoothness` field on each `SdfNode`.

## Files

- Edit: `py/pytanga/viz/sdf/_compose.py`
- Edit: `py/pytanga/viz/sdf/primitives.py`
- Edit: `py/pytanga/viz/sdf/group.py`
- Edit: `py/pytanga/viz/sdf/composed.py`
- Edit: `py/pytanga/viz/sdf/serializer.py`
- Edit: `py/pytanga/viz/_styles/_sdf_style.py`
- Edit: `py/tests/viz/sdf/test_ecompose_operators.py`
- Edit: `py/tests/viz/sdf/test_sdf_group.py` (and/or `test_composed.py`)

## Steps

- [x] **4.1 — `ECompose` smooth modes + kind map**
  - In `_compose.py`, add `SMOOTH_UNION = "smooth_union"`,
    `SMOOTH_INTERSECTION = "smooth_intersection"`, and
    `SMOOTH_SUBTRACT = "smooth_subtract"` to `ECompose`.
  - Extend `_COMBINE_KIND` to map each smooth mode to its kind string
    (`"smooth_union"`, `"smooth_intersection"`, `"smooth_subtract"`).
  - Confirm `_coerce_mode` treats the smooth modes as valid *fold* modes (they
    must not be rejected the way binary-only `XOR` is).

- [x] **4.2 — `SdfNode.smoothness` + `combine()`/`group()`**
  - In `primitives.py`, add `smoothness: float | None = None` to the `SdfNode`
    dataclass and emit `"smoothness"` in `SdfNode.to_dict()` when set.
  - Add a `smoothness: float | None = None` keyword to `combine()` and stamp it
    on the returned `SdfNode`.

- [x] **4.3 — `SdfElement.smoothness` + `_normalize_part` 3-tuple**
  - In `_compose.py`, add `smoothness: float | None = None` to the `SdfElement`
    base dataclass (inherited by `SdfObject`/`Combine`/`Composed`/`SdfGroup`).
  - Extend `_normalize_part` to accept a legacy `(obj, mode, smoothness)` tuple
    in addition to `(obj, mode)`; stamp the resolved `smoothness` onto the
    returned element (`SdfElement.smoothness` or `SdfNode.smoothness`).
    Keep the returned tuple shape `(element, mode)` (see README decision).
  - Add a `smoothness: float | None = None` field to `Combine` and pass it to
    `combine(...)` in `Combine.to_sdf_node()`.

- [x] **4.4 — `Composed`/`SdfGroup` stamp child smoothness**
  - In `composed.py` and `group.py`, in each `to_sdf_node()`, after
    `child.combine = mode.value`, also set `child.smoothness` from the member
    element's `smoothness` (via `getattr(element, "smoothness", None)`).
  - In `serializer.py` (`_composed_tree` and `_serialize_group`), do the same
    `child.smoothness = getattr(obj, "smoothness", None)` next to the existing
    `child.combine = ...` lines so the standard-viewer group serializer carries
    the value too.

- [x] **4.5 — `SdfStyle.smoothness` convenience default**
  - In `_styles/_sdf_style.py`, add `smoothness: float | None = None` to
    `SdfStyle` and include it in `to_dict()` when set.

- [x] **4.6 — Tests**
  - In `test_ecompose_operators.py`, assert the new `ECompose` members
    string-coerce and that `_coerce_mode` accepts them as fold modes while still
    rejecting `XOR`.
  - In `test_sdf_group.py`/`test_composed.py`, assert the 3-tuple form
    `(obj, "smooth_union", 0.15)` round-trips: the serialized tree carries
    `combine: "smooth_union"` and `smoothness: 0.15` on the member node.

## Validation

`uv run pytest py/tests/viz/sdf/ -q`

## Notes

- The GLSL smooth functions (`opSmoothUnion`/`opSmoothIntersect`/
  `opSmoothSubtract`) already exist in
  `py/pytanga/viz/templates/sdf/shaders/combinators.glsl`; this phase only makes
  the Python model emit the data. Phase 5 consumes it in the frontend.
- `SdfGroup`/`Composed` `parts` stay `(element, mode)` 2-tuples, so the
  serializer's `for obj, combine_mode in group.parts` / `for m, _ in
  entity.parts` unpacking sites are untouched — smoothness rides on the element.
- Call sites that stamp `child.combine` (three of them: `group.py`,
  `composed.py`, `serializer.py`) are the ones that must also stamp
  `child.smoothness`; keep them in sync.
