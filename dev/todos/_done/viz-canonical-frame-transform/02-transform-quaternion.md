# Phase 2 — Quaternion `Transform` + `Point`/`Direction` operators

## Goal

Switch `Transform` to store a **quaternion** for rotation (single source of
truth, gimbal-lock free), emit it on the wire, and add operator overloading so a
`Transform` can be applied to `Point` and `Direction` instances.

## Files

- Edit: `py/pytanga/geometry/transform.py` (quaternion + operators)
- Edit: `py/pytanga/geometry/transforms.py` (quaternion helpers)
- Edit: `py/pytanga/viz/templates/scene-builder.js` (quaternion apply)

## Steps

- [x] **2.1 — quaternion helpers in `geometry/transforms.py`**
  - Add pure helpers: `quat_to_matrix(q)`, `matrix_to_quat(m)`,
    `quat_from_axis_angle(axis, angle)`, `quat_from_vectors(a, b)`
    (unit-vector → unit-vector rotation, the `setFromUnitVectors` analog), and
    `quat_mul(a, b)`.
  - Keep the existing Euler helpers (`_mat3_to_euler`, `to_trs`,
    `operator_to_trs`) for the out-of-scope operator path; they remain for
    backward compatibility.

- [x] **2.2 — quaternion storage in `Transform`**
  - `self.rotation` becomes a quaternion `(x, y, z, w)`; `__init__` accepts
    either an Euler triple or a quaternion (coerce via `_as_euler` → quaternion).
  - `matrix()` = `T @ R(q) @ S` (computed lazily, unchanged call sites).
  - `set_matrix`/`from_matrix` decompose to `(position, quaternion, scale)`;
    `rotate(axis, angle)` composes a `quat_from_axis_angle` in local space;
    `apply_matrix`/`from_operator` go through the matrix and decompose to quat.
  - `to_dict()` emits `"rotation": [x, y, z, w]` (quaternion).

- [x] **2.3 — operator overloading for `Point`/`Direction`**
  - Add `apply(obj)` dispatching on type: `Point` → `R·S·p + t`;
    `Direction` → `R·S·d` (no translation — a direction is an ideal point).
  - Add `__matmul__` / `__rmatmul__` (and `__mul__` / `__rmul__` aliases) so
    `transform @ point`, `transform @ direction`, and the reverse order all
    return a fresh `Point`/`Direction`. Non-`Point`/`Direction` operands return
    `NotImplemented`.

- [x] **2.4 — frontend quaternion apply**
  - `scene-builder.js` `applyTransformToObject`: replace
    `obj.rotation.set(...)` with `obj.quaternion.set(x, y, z, w)`.
  - `isIdentityTransform`: identity quaternion check `[0, 0, 0, 1]`.

- [x] **2.5 — tests**
  - Quaternion round-trip (`matrix` ↔ `set_matrix`), `to_dict()` rotation has 4
    elements, `transform @ Point`/`Direction` (incl. no-translation for
    `Direction`), reverse order.

## Validation

`uv run pytest py/tests/viz -q && node --check py/pytanga/viz/templates/scene-builder.js`

## Notes

- `Point`/`Direction` already return `NotImplemented` from `__mul__`/`__rmul__`
  for non-scalars (`py/pytanga/entity/point.py:86-94`,
  `py/pytanga/entity/direction.py:82-90`), so `transform * point` and
  `point * transform` resolve to `Transform.__mul__`/`__rmul__`.
- This is a contained, internal breaking change to the `transform.rotation`
  wire (Euler triple → quaternion); the glTF exporter already emits quaternions.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
