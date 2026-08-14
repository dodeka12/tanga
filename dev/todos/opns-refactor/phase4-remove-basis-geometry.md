# Phase 4 — Remove Geometry-Creating Methods from Basis Classes

**Prerequisites:** Phases 1–3 (entity constructors + typed analyzers exist, so
geometry can be created exclusively through the `geometry` submodule).

**Goal:** Geometry multivectors must be created **only** via the `geometry`
submodule. Remove the geometry-creating methods that are partially defined on some
`Basis*` classes, and update the `hasattr(basis, ...)`/`hasattr(alg, ...)` fallbacks
in the `geometry.create_*` / `analysis_*` code to build blades directly.

---

## 1. Methods to remove

| Class | Methods to remove |
|-------|-------------------|
| `BasisE2` | `vector`, `rnd_vector`, `rotor` |
| `BasisE3` | `vector`, `rnd_vector`, `rotor` |
| `BasisP2` | `point`, `direction`, `rnd_point`, `rnd_direction`, `rotor` |
| `BasisP3` | `point`, `direction`, `rnd_point`, `rnd_direction`, `rotor` |
| `BasisPGA2` | `point`, `direction`, `line` |
| `BasisPGA3` | `point`, `direction`, `plane` |
| `BasisN2` | — (raw basis; no geometry-creating methods) |
| `BasisN3` | — (raw basis; no geometry-creating methods) |

The classes keep **raw** named-basis blades (`e1`, `e2`, `einf`, `eo`, `e0`,
`e0_inv`, `I`, etc.) and any non-geometry conveniences (none of the above remain).

---

## 2. Fix `geometry.create_*` / `analysis_*` `hasattr` fallbacks

Several modules branch on the now-removed methods and must instead always build the
blade directly (or delegate to the shared helpers):

- `py/pytanga/geometry/create_p2.py`
  - `create_point`: `if hasattr(basis, "point"): return basis.point(x, y)` →
    drop the branch; always build ``{E1: x, E2: y, E3: 1}``.
  - `create_direction`: ``hasattr(basis, "direction")`` → always ``{E1: x, E2: y}``.
- `py/pytanga/geometry/create_p3.py`
  - `create_point`: ``hasattr(basis, "point")`` → always ``{E1: x, E2: y, E3: z, E4: 1}``.
  - `create_direction`: ``hasattr(basis, "direction")`` → always ``{E1: x, E2: y, E3: z}``.
- `py/pytanga/geometry/analysis_pga2.py`
  - `make_point`: ``hasattr(alg, "point")`` → always ``{E1: x, E2: y, EP: 1.0, EM: 1.0}``.
  - `make_direction`: ``hasattr(alg, "direction")`` → always ``{E1: x, E2: y}``.
  - `make_line`: ``hasattr(alg, "line")`` → always ``{E1: nx, E2: ny, EP: d, EM: d}``.
- `py/pytanga/geometry/analysis_pga3.py`
  - `make_point`: ``hasattr(alg, "point")`` → always ``{E1: x, E2: y, E3: z, EP: 1.0, EM: 1.0}``.
  - `make_direction`: ``hasattr(alg, "direction")`` → always ``{E1: x, E2: y, E3: z}``.
  - `make_plane`: ``hasattr(alg, "plane")`` → always ``{E1: nx, E2: ny, E3: nz, EP: d, EM: d}``.

`analysis_e2/e3.py` already have `make_point`/`make_plane`/`make_rotor` that use
``hasattr(alg, "vector")``; replace those with direct builds too.

---

## 3. Update dependent library/test code

Search for the removed method invocations (from `rg`) and replace with
`geometry.create_entity` / typed entity constructors:

- **Tests**
  - `py/tests/basis/test_basis.py` and `py/tests/basis/test_basis_2d.py` call
    `self.b.point(...)`, `self.b.direction(...)`, `self.b.line(...)`,
    `self.b.rnd_point(...)`, `self.b.rnd_direction(...)`. Replace with
    `create_entity(self.b, Point(...))` / `create_entity(self.b, Direction(...))` /
    `create_entity(self.b, Line(...))`, or the typed entity constructors
    (`Point(self.b.e1 ^ ...)` etc.).
  - Any other basis tests asserting `vector(...)`/`rotor(...)` → use
    `alg.multivector({...})` (raw) or `geometry.create_*` accordingly.

- **Examples** (shown here; mechanically rewritten in Phase 7)
  - `py/examples/viz/demo_mv_visualization.py` uses `pga.plane`, `pga.point`,
    `n3.point`, `n3.point_pair`, `n3.circle`, `n3.plane`, `n3.sphere`,
    `n3.line_from_origin_direction`, `n3.line_from_direction`. These all become
    `geometry.create(...)` / typed constructors. (Note: `n3.point_pair`/`n3.circle`/
    `n3.sphere` are not defined on `BasisN3` today — this example already relies on
    helpers that only exist in this demo; rewrite via the `geometry` submodule.)
  - `py/examples/basis/base_p3_demo.py`, `base_pga3_demo.py` use `.point(...)` → `geometry`.
  - `py/examples/numerics/solver_point_line_p3.py`, `py/examples/tensor/rotor-point-on-ray_01.py`
    use `P3.point/rnd_point/rnd_direction/rotor` → replace with `create_entity` /
    `create_operator` (or equivalent raw construction via `algebra.multivector`).

---

## 4. Naming note

Removing generators does **not** touch the `rotor(...)` operators generated under
`geometry.create_*` (e.g. `create_rotor`). Those remain the canonical path via
`geometry.create_operator(basis, Rotor(...))`.

---

## 5. Tests (Phase 4)

- Update `py/tests/basis/test_basis.py` and `py/tests/basis/test_basis_2d.py`
  to use the `geometry` submodule instead of basis methods.
- Add regression: `hasattr(BasisP3(), "point") is False`, and likewise for the other
  removed methods, so re-introduction is caught.
- Ensure `create_entity(basis, Point(...))`/`Direction(...)`/`Line(...)` round-trip
  still pass after removing the basis methods (these already exist).

---

## 6. Implementation Checklist

- [ ] Remove methods from `BasisE2`, `BasisE3` (`vector`, `rnd_vector`, `rotor`)
- [ ] Remove methods from `BasisP2`, `BasisP3` (`point`, `direction`, `rnd_point`, `rnd_direction`, `rotor`)
- [ ] Remove methods from `BasisPGA2` (`point`, `direction`, `line`)
- [ ] Remove methods from `BasisPGA3` (`point`, `direction`, `plane`)
- [ ] Replace `hasattr(..., "point"/"direction"/"line"/"plane"/"vector")` fallbacks in `analysis_*`/`create_*`
- [ ] Update `py/tests/basis/*` to the `geometry` submodule
- [ ] Update `py/examples/basis/*`, `py/examples/numerics/*`, `py/examples/tensor/*` (mechanical)
- [ ] Run: `pytest py/tests/basis py/tests/geometry -q`

---

## 7. Verification

- [ ] `rg "(point|direction|line|plane|vector|rotor)\(" py/pytanga/basis` returns only non-geometry internal hits (none expected)
- [ ] `hasattr(BasisP3(), "point")` is `False`; same for all removed methods
- [ ] Geometry round-trips still pass via the `geometry` submodule