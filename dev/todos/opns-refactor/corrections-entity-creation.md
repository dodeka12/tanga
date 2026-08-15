# Corrections — OPNS/IPNS Entity-Creation Semantics

Follow-up to the per-algebra OPNS-creation review (`dev/notes/opns-entity-creation-*.md`).
Fixes the creation rules so each algebra maps entities consistently to OPNS/IPNS,
and disables imaginary entities that are not yet implemented.

## Background / Problems found

1. **E2/E3 `create_point`** incorrectly raised `ValueError`. A point should map to
   its Euclidean blade components independent of OPNS/IPNS.
   - E2 → `x·e1 + y·e2`
   - E3 → `x·e1 + y·e2 + z·e3`
2. **E2/E3 `create_direction` / `create_line`** ignored the OPNS/IPNS flag.
   Directions/lines through origin must dualize for IPNS.
3. **`create_space` IPNS** in E2/E3/N2/N3 returned the OPNS pseudoscalar; it must
   return the grade-0 scalar (the dual of the pseudoscalar).
4. **Imaginary entities** (`ImagPointPair`, `ImagCircle`, `ImagSphere`) in N2/N3
   are not yet correctly implemented; creation must raise `NotImplementedError`
   until proper code lands.

## Changes to make

### 1. `py/pytanga/geometry/create_e2.py`
- [x] `create_point` → `basis.multivector({E1: x, E2: y})` (always; no raise).
- [x] `create_direction` → `opns_mv = {E1:x, E2:y}`; return `opns_mv` or `opns_mv.dual()`.
- [x] `create_line` → forward `opns` to `create_direction`.
- [x] `create_space` → OPNS `{E12: scale}`; IPNS `opns_mv.dual()`.

### 2. `py/pytanga/geometry/create_e3.py`
- [x] `create_point` → `{E1:x, E2:y, E3:z}` (always; no raise).
- [x] `create_direction` → `{E1:x, E2:y, E3:z}`; OPNS direct, IPNS `.dual()`.
- [x] `create_line` → forward `opns` to `create_direction`.
- [x] `create_space` → OPNS `{E123: scale}`; IPNS `.dual()`.

### 3. `py/pytanga/geometry/create_n2.py`
- [x] `create_space` → IPNS `.dual()`.
- [x] `create_sphere(is_imaginary=True)` → `raise NotImplementedError`.
- [x] `create_imag_point_pair` → `raise NotImplementedError`.
- [x] `create_imag_circle` → `raise NotImplementedError`.

### 4. `py/pytanga/geometry/create_n3.py`
- [x] `create_space` → IPNS `.dual()`.
- [x] `create_sphere(is_imaginary=True)` → `raise NotImplementedError`.
- [x] `create_imag_point_pair` → `raise NotImplementedError`.
- [x] `create_imag_circle` → `raise NotImplementedError`.

### 5. Docs — `dev/notes/opns-entity-creation-{e2,e3,n2,n3}.md`
- [x] e2/e3: point = Euclidean components (OPNS/IPNS independent); direction/line
      dualize for IPNS; space IPNS = scalar.
- [x] n2/n3: space IPNS = scalar; imaginary entities marked unsupported.

### 6. Test updates (currently failing — must be updated)

Point no longer raises:
- [ ] `test_geometry_e2.py::test_create_point_raises`
- [ ] `test_geometry_e2_analysis.py::test_create_point_raises`
- [ ] `test_geometry_e3.py::test_create_point_raises`
- [ ] `test_geometry_e3_analysis.py::test_create_point_raises`
  → assert `create_entity(..., Point(...))` returns the `e1/e2(/e3)` coefficient vector.

Direction IPNS now dualized:
- [ ] `test_geometry_e2_analysis.py::test_entity_direction_ipns_round_trip`
  → IPNS direction is the perpendicular dual `(y, −x)` normalized.
- [ ] `test_geometry_e3.py::test_create_direction_round_trip_ipns`
  → IPNS direction is a bivector; `analyze_entity` now resolves to `Line` (not `Plane`).

Imaginary entities now raise `NotImplementedError`:
- [ ] `test_geometry_n2.py::test_imag_sphere_ipns_squared_negative`
- [ ] `test_geometry_n2.py::test_imag_sphere_round_trip`
- [ ] `test_geometry_n3.py::test_imag_sphere_ipns_squared_negative`
- [ ] `test_geometry_n3.py::test_imag_sphere_round_trip`
- [ ] `test_geometry_n3.py::test_imag_point_pair_via_circle_dual`
- [ ] `test_geometry_n3.py::test_imag_circle_via_point_pair_dual`
  → `with pytest.raises(NotImplementedError):`

### 7. Regression tests (new/optional)
- [ ] E2/E3 space IPNS is grade-0 scalar.
- [ ] E2/E3 point maps to `e1/e2(/e3)` for both `opns=True` and `opns=False`.
- [ ] `create_imag_*` / imaginary sphere raise `NotImplementedError` in N2/N3.

### 8. Optional: PGA3 imaginary normalization
- [ ] `create.py` dispatches `PointPair(...is_imaginary=True)` / `Circle(...is_imaginary=True)`
      for PGA3 to `create_imag_point_pair`/`create_imag_circle`, which don't exist in
      `create_pga3.py` (currently `AttributeError`). Decide whether to also raise
      `NotImplementedError` there.

## Verification
- [ ] `uv run python -m pytest py/tests/geometry -q`
- [ ] `uv run python -m pytest -q` (full suite)
- [ ] `uv run ruff check` on changed files (no new lint issues)

## Notes
- Code/doc changes already applied to the working tree; only the tests and a final
  commit remain.
- Correctness of the E3 direction-IPNS → Line round-trip result should be confirmed
  against Perwass before locking the assertion in.