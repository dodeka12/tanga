# Phase 6a — Creation Path Reads `basis.opns`

**Prerequisites:** Phase 5.

**Goal:** Remove the `opns` keyword from the creation path and make it read
`basis.opns`. Convert every internal `opns=True`/`opns=False` sub-build (which
mathematically *must* produce a specific OPNS/IPNS blade) into a private
`_*_opns(...)` / `_*_ipns(...)` helper. Bundle `Geometry.create` +
`Geometry.__call__` in this phase.

---

## Step 0 — Dispatcher & Geometry facade (do first)

### `py/pytanga/geometry/create.py`
- `create_entity(basis, entity, *, opns=True)` → `create_entity(basis, entity)`.
- Remove every `opns=opns` from the `mod.create_*` calls.
- `create(basis, obj, *, opns=True)` → `create(basis, obj)`.
- `create_operator` unchanged (has no `opns`).

### `py/pytanga/geometry/_geometry.py`
- `Geometry.create(self, obj, *, opns=None)` → `create(self, obj)` → `create(self._algebra, obj)`.
- Add `__call__(self, obj)` aliasing `create`.
- Update docstrings.

---

## Step 1 — `create_e2.py`

- `create_point`: drop `opns`.
- `create_direction`: drop `opns`; `if basis.opns:`.
- `create_line`: drop `opns`; drop `opns=opns` forwarding.
- `create_space`: drop `opns`; `if basis.opns:`.
- Stubs (`create_sphere`, `create_circle`, `create_point_pair`, `create_homogeneous_point`): drop `opns`.

No private helpers needed.

---

## Step 2 — `create_e3.py`

- `create_point`: drop `opns`.
- `create_direction`: drop `opns`; `if basis.opns:`.
- `create_line`: drop `opns`; drop forwarding.
- `create_plane`: drop `opns`; `if basis.opns: return ipns.dual()`.
- `create_space`: drop `opns`; `if basis.opns:`.
- Stubs: drop `opns`.

---

## Step 3 — `create_p2.py`

- `create_point`: drop `opns`; `if basis.opns:`.
- `create_direction`: drop `opns`; `if basis.opns:`.
- `create_line`: drop `opns`; internal `create_point(..., opns=True)` → `_point_opns(basis, x, y)`; final `if basis.opns:`.
- `create_space`: drop `opns`; `if basis.opns:`.
- Stubs: drop `opns`.

Add `_point_opns(basis, x, y)`.

Operator updates:
- `create_reflection_point`: `create_point(..., opns=True)` → `_point_opns(...)`.

---

## Step 4 — `create_p3.py`

- `create_point`: drop `opns`; `if basis.opns:`.
- `create_direction`: drop `opns`; `if basis.opns:`.
- `create_line`: drop `opns`; internal `create_point(..., opns=True)` → `_point_opns(basis, x, y, z)`; final `if basis.opns:`.
- `create_plane`: drop `opns`; `if basis.opns: return ipns.dual()`.
- `create_space`: drop `opns`; `if basis.opns:`.
- Stubs: drop `opns`.

Add `_point_opns(basis, x, y, z)`.

Operator updates:
- `create_reflection_point`: `create_point(..., opns=True)` → `_point_opns(...)`.

---

## Step 5 — `create_n2.py`

- `create_point`, `create_direction`, `create_homogeneous_point`, `create_homogeneous_direction`, `create_point_pair`, `create_line`: drop `opns`; `if not basis.opns:`.
- `create_sphere`: drop `opns` (keep `is_imaginary`); `if basis.opns: return ipns.dual()`; add `_sphere_ipns(basis, center, radius)`.
- `create_circle`: drop `opns`; delegate `create_sphere(basis, center, radius)`.
- `create_space`: drop `opns`; `if basis.opns:`.
- `create_imag_point_pair` / `create_imag_circle`: drop `opns`.

Add private helpers:
- `_sphere_ipns(basis, center, radius)`.
- `_homogeneous_point_opns(basis, point, weight=1.0)`.

Operator updates:
- `create_inversion`: `create_sphere(..., opns=False)` → `_sphere_ipns(...)`.
- `create_reflection_point`: `create_homogeneous_point(..., opns=True)` → `_homogeneous_point_opns(...)`.

---

## Step 6 — `create_n3.py`

- `create_point`, `create_direction`, `create_homogeneous_point`, `create_homogeneous_direction`, `create_point_pair`, `create_line`: drop `opns`; `if not basis.opns:`.
- `create_plane`: drop `opns`; `if basis.opns: return ipns.dual()`; add `_plane_opns(basis, plane)`.
- `create_sphere`: drop `opns` (keep `is_imaginary`); `if basis.opns:`; add `_sphere_ipns(basis, center, radius)`.
- `create_circle`: drop `opns`; `if basis.opns: return circle_ipns.dual()`.
- `create_space`: drop `opns`; `if basis.opns:`.
- `create_imag_point_pair` / `create_imag_circle`: drop `opns`.

Add private helpers:
- `_plane_opns(basis, plane)`.
- `_sphere_ipns(basis, center, radius)`.
- `_homogeneous_point_opns(basis, point, weight=1.0)`.

Operator updates:
- `create_reflection_plane`: `create_plane(..., opns=True)` → `_plane_opns(...)`.
- `create_inversion`: `create_sphere(..., opns=False)` → `_sphere_ipns(...)`.
- `create_reflection_point`: `create_homogeneous_point(..., opns=True)` → `_homogeneous_point_opns(...)`.
- `create_reflection_line`: unchanged (raw OPNS via `_cop`).

---

## Step 7 — `create_pga2.py`

- `create_point`: drop `opns`; `if not basis.opns: return p_ipns` else `p_ipns.dual()`.
- `create_direction`: drop `opns`; `if not basis.opns:`.
- `create_line`: drop `opns`; `if not basis.opns: mv = mv.dual()`.
- `create_space`: drop `opns`; `if not basis.opns:`.
- Stubs: drop `opns`.

Add `_point_opns(basis, x, y)`.

Operator updates:
- `create_reflection_line`: `create_line(..., opns=True)` → `_line_opns(...)` (new helper).
- `create_reflection_point`: `create_point(..., opns=True)` → `_point_opns(...)`.

---

## Step 8 — `create_pga3.py`

- `create_point`: drop `opns`; `if not basis.opns: return p_ipns` else `p_ipns.dual()`.
- `create_direction`: drop `opns`; `if not basis.opns:`.
- `create_line`: restructure — `_line_opns(basis, origin, direction)` computes the two planes and returns `p1.op(p2)`; public `create_line` applies `if not basis.opns: mv = mv.dual()`.
- `create_plane`: drop `opns`; `if not basis.opns: mv = mv.dual()`.
- `create_space`: drop `opns`; `if not basis.opns:`.

Add private helpers: `_line_opns(basis, origin, direction)`, `_point_opns(basis, x, y, z)`, `_plane_opns(basis, plane)`.

Operator updates:
- `create_reflection_line`: `create_line(..., opns=True)` → `_line_opns(...)`.
- `create_reflection_plane`: `create_plane(..., opns=True)` → `_plane_opns(...)`.
- `create_reflection_point`: `create_point(..., opns=True)` → `_point_opns(...)`.

---

## Step 9 — Tests

Rewrite `opns=` call sites across `py/tests/geometry/`:
- `test_geometry_e2.py`, `test_geometry_e2_analysis.py`
- `test_geometry_e3.py`, `test_geometry_e3_analysis.py`
- `test_geometry_p2.py`, `test_geometry_p3.py`
- `test_geometry_n2.py`, `test_geometry_n3.py`
- `test_geometry_pga2.py`, `test_geometry_pga3.py`
- `test_typed_analyzers.py` (drop `opns=opns` from `create_entity` calls)
- `test_entity_constructors.py`

`test_geometry_convenience.py`:
- Replace `test_create_override_opns` (passed `opns=False` to `geo.create`) with an `alg.opns = False` test.
- Add `Geometry.__call__` tests.

New file `py/tests/geometry/test_creation_flag.py`:
- For each of the 8 algebras, assert `create_entity(alg, X(...))` respects `alg.opns` by checking produced blade grade.

---

## Step 10 — Verify

- `uv run python -m pytest py/tests/geometry -q`
- `uv run ruff check py/pytanga/geometry/`
- Spot-check `create_entity`/`create` no longer accept `opns`; `Geometry.__call__` works.

---

## Verification checklist

- [ ] `create_entity(basis, entity)` / `create(basis, obj)` no longer accept `opns`
- [ ] `Geometry.create(obj)` follows `algebra.opns`
- [ ] `geo(obj)` (i.e. `Geometry.__call__`) equals `geo.create(obj)`
- [ ] IPNS + OPNS round-trips still pass (create → analyze) for all algebras
- [ ] Internal OPNS sub-builds do not regress when `alg.opns` is `False`