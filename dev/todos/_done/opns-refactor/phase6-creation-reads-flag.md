# Phase 6 — Creation Path Reads `basis.opns`

**Prerequisites:** Phase 5.

**Goal:** Remove the `opns` keyword from the creation path and make it read
`basis.opns`. Convert every internal `opns=True` sub-build (which mathematically
*must* produce an OPNS blade before a final dualization) into a private OPNS-only
helper. Bundle `Geometry.create` in this phase.

---

## 1. `geometry/create.py` dispatcher

- `def create_entity(basis, entity, *, opns=True)` → `def create_entity(basis, entity)`.
- Remove `opns=opns` from every `mod.create_*` call.
- `def create(basis, obj, *, opns=True)` → `def create(basis, obj)`.

Operator creation (`create_operator`) already has no `opns`; unchanged.

---

## 2. `geometry/_geometry.py` — `Geometry.create` + `Geometry.__call__`

- `create(self, obj, *, opns=None)` → `create(self, obj)` → `create(self._algebra, obj)`.
- Add `__call__` that aliases `create`, so
  ``geo = Geometry(BasisN3()); A = geo(Point(1, 2, 3))``:

  ```python
  def __call__(self, obj: Entity | Operator) -> MV:
      """Create an MV from *obj* (alias for :meth:`create`)."""
      return self.create(obj)
  ```

---

## 3. Per-algebra `create_*` modules — surface removal

For all 8 modules, change each `def create_*(..., *, opns: bool = True)` to drop the
`opns` parameter and replace the final `if <not> opns:` dualization with
`if not basis.opns:`.

| Module | Functions |
|--------|-----------|
| `create_e2.py` | `create_point`, `create_direction`, `create_line`, `create_space`, `create_sphere`, `create_point_pair`, `create_homogeneous_point` |
| `create_e3.py` | `create_point`, `create_direction`, `create_line`, `create_plane`, `create_space`, `create_sphere`, `create_point_pair`, `create_homogeneous_point` |
| `create_p2.py` | `create_point`, `create_direction`, `create_line`, `create_space`, `create_sphere`, `create_point_pair`, `create_homogeneous_point` |
| `create_p3.py` | `create_point`, `create_direction`, `create_line`, `create_plane`, `create_space`, `create_sphere`, `create_point_pair`, `create_homogeneous_point` |
| `create_n2.py` | `create_point`, `create_direction`, `create_homogeneous_point`, `create_homogeneous_direction`, `create_point_pair`, `create_line`, `create_circle`, `create_sphere`, `create_space`, `create_imag_point_pair`, `create_imag_circle` |
| `create_n3.py` | same as n2 plus `create_plane` |
| `create_pga2.py` | `create_point`, `create_direction`, `create_line`, `create_space`, `create_sphere`, `create_point_pair`, `create_homogeneous_point` |
| `create_pga3.py` | `create_point`, `create_direction`, `create_line`, `create_plane`, `create_space` |

Internal OPNS-forcing helpers are addressed in §4.

---

## 4. Internal `opns=True` sub-builds → private OPNS helpers

These call sites currently build an OPNS blade as an intermediate step and then
dualize at the public boundary. They must remain OPNS-explicit; after Phase 5 they
**must not** be switched to `basis.opns`:

- `create_n3.py` / `create_n2.py`:
  - `create_line`: `a = create_point(..., opns=True)`, `b = create_point(..., opns=True)`,
    `mv = a.op(b).op(einf)`. → extract `_point_opns(basis, x, y, z)` / `_direction_opns`.
  - `create_point_pair`: `cp1 = _point_opns(...)`, `cp2 = _point_opns(...)`, `mv = cp1.op(cp2)`.
  - `create_circle`: builds IPNS sphere + IPNS plane (both `opns=False`), wedges → `circle_ipns`,
    dualizes if public `opns`. → call `_sphere_ipns(...)` / `_plane_ipns(...)` directly.
  - `create_sphere`: builds IPNS `S` then `if opns: return S.dual()`.
  - `create_imag_point_pair`: `circle_opns = create_circle(..., opns=True)` then dual → `pp_ipns`.
    → call `_circle_opns(...)` directly.
  - `create_imag_circle`: `pp_opns = create_point_pair(..., opns=True)` then dual.
  - `create_space`: builds OPNS pseudoscalar, dualizes when IPNS.
- `create_p3.py` / `create_p2.py`:
  - `create_line`: `a = create_point(..., opns=True)`, `b = create_point(..., opns=True)`,
    `mv = a.op(b)`. → `_point_opns`.
- `create_pga3.py`:
  - `create_line`: recursion `create_line(basis, origin, direction, opns=True)` then `.dual()`.
    → restructure into `_line_opns(basis, origin, direction)` + public dualize wrapper.
- `create_pga3.py` `create_space` and all build-then-dualize steps keep the raw build
  in a private helper and apply `basis.opns` at the public function boundary only.

Naming convention: `_X_opns(basis, ...)` / `_X_ipns(basis, ...)` return the *raw*
blade; the public `create_X(basis, ...)` applies `basis.opns`.

---

## 5bis. Tests (Phase 6)

Update existing creation tests that pass `opns=`:

- `py/tests/geometry/test_geometry_e3.py` / `e2.py` / `p3.py` / `p2.py` /
  `n3.py` / `n2.py` / `pga3.py` / `pga2.py`.
- `py/tests/geometry/test_geometry_convenience.py` (`Geometry.create` no longer
  accepts `opns`; add a `Geometry.__call__` test).

Mechanical rewrite: drop `opns=True` arguments; where an IPNS result is asserted,
construct a dedicated `AlgType(opns=False)` or set `alg.opns = False` first.

Add a `Geometry.__call__` test:
- `geo = Geometry(BasisN3()); geo(Point(1, 2, 3))` returns an MV with the same
  grade as `geo.create(Point(1, 2, 3))`.
- `geo(Point(1, 2, 3))` with `geo.algebra.opns = False` produces the IPNS grade.

New regression coverage (append to `test_typed_analyzers.py` or a new
`test_creation_flag.py`): for each algebra, `create_entity(alg, X(...))` respects
`alg.opns` by asserting the produced blade grade matches OPNS vs IPNS
(e.g. N3 point: grade-1 OPNS vs grade-4 IPNS; PGA3 point: grade-3 OPNS vs grade-1 IPNS).

---

## 6. Implementation Checklist

- [ ] `create.py` dispatchers drop `opns`
- [ ] `Geometry.create` drops `opns`; add `Geometry.__call__`
- [ ] 8 `create_*` modules drop `opns` and read `basis.opns`
- [ ] Extract private `_*_opns`/`_*_ipns` helpers for internal sub-builds
- [ ] Update creation + convenience tests; add `test_creation_flag.py`
- [ ] Run: `pytest py/tests/geometry -q`

---

## 7. Verification

- [ ] `create_entity(basis, entity)` / `create(basis, obj)` no longer accept `opns`
- [ ] `Geometry.create(obj)` follows `algebra.opns`
- [ ] `geo(obj)` (i.e. `Geometry.__call__`) equals `geo.create(obj)`
- [ ] IPNS + OPNS round-trips still pass (create → analyze) for all algebras
- [ ] Internal OPNS sub-builds do not regress when `alg.opns` is `False`