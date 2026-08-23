# Phase 1 — Basis Classes

Create the four 2D algebra basis classes: `BasisE2`, `BasisP2`, `BasisN2`,
`BasisPGA2`. Each mirrors its 3D counterpart but with reduced dimension.

## Algebra Signatures

| Class | dim | sig | Blade Count | Key Features |
|-------|-----|-----|-------------|--------------|
| `BasisE2` | 2 | 0 | 4 | e1, e2, e12 (pseudoscalar I) |
| `BasisP2` | 3 | 0 | 8 | e1, e2, e3 (homogeneous), e123 (I) |
| `BasisN2` | 4 | 0b1000 | 16 | e1, e2, ep, em; einf=ep+em, eo=-0.5·ep+0.5·em |
| `BasisPGA2` | 4 | 0b1000 | 16 | Inherits `BasisN2`; e0=ep+em, e0_recip=0.5·ep−0.5·em |

## Files to Create

### `py/pytanga/basis/e2.py` — `BasisE2`

- Blade IDs: `E1=1, E2=2, E12=3`
- Constructor: `Algebra.__init__(2, 0, dtype, **kw)`
- Named blades: `e1`, `e2`, `e12`, `I`
- Method: `vector(x, y)` → `{1: x, 2: y}`
- Method: `rnd_vector(x_range, y_range)` → random vector
- Method: `rotor(theta, axis_mv)` — delegates to `create_rotor` from create_e2 module
- `_display_basis`: `[(e1,"e1"), (e2,"e2")]` → 4 blades

### `py/pytanga/basis/p2.py` — `BasisP2`

- Blade IDs: `E1=1, E2=2, E3=4, E12=3, E13=5, E23=6, E123=7`
- Constructor: `Algebra.__init__(3, 0, dtype, **kw)`
- Named blades: `e1`, `e2`, `e3`, `e123`, `I`
- Methods: `point(x, y)` → `{1:x, 2:y, 4:1}`, `direction(x, y)` → `{1:x, 2:y}`
- `rnd_point(x_range, y_range)`, `rnd_direction(x_range, y_range)`
- `rotor(theta, axis_mv)`

### `py/pytanga/basis/n2.py` — `BasisN2`

- Blade IDs: `E1=1, E2=2, EP=4, EM=8, E12=3`
- Constructor: `Algebra.__init__(4, 0b1000, dtype, **kw)`
- Named blades: `e1`, `e2`, `ep`, `em`
- Composed blades: `einf = {EP:1, EM:1}`, `eo = {EP:-0.5, EM:0.5}`
- `_display_basis` with null swap: `{"einf": "eo", "eo": "einf"}`

### `py/pytanga/basis/pga2.py` — `BasisPGA2`

- Extends `BasisN2` (same dim=4, sig=0b1000)
- Named blades: `e1`, `e2`, `e0=ep+em`, `e0_recip=0.5·ep−0.5·em`
- Methods: `point(x, y)` → `{1:x, 2:y, EP:1, EM:1}`, `direction(x, y)` → `{1:x, 2:y}`
- `plane(nx, ny, d)` → `{1:nx, 2:ny, EP:d, EM:d}`
- `_display_basis`: `[(e1,"e1"), (e2,"e2"), (e0,"e0")]`

## Files to Modify

### `py/pytanga/basis/__init__.py`

- Import `BasisE2`, `BasisP2`, `BasisN2`, `BasisPGA2`
- Add to `_CLASS_MAP`: `"E2": BasisE2`, `"P2": BasisP2`, `"N2": BasisN2`, `"PGA2": BasisPGA2`
- Add to `__all__`

### `py/pytanga/algebra/_algebra.py`

- Add `"E2"`, `"P2"`, `"N2"` to `_BASIS_CLASS_NAMES` (for `from_name()` dispatch)

## Implementation Checklist

- [ ] 1.1  Create `py/pytanga/basis/e2.py` with `BasisE2`
- [ ] 1.2  Create `py/pytanga/basis/p2.py` with `BasisP2`
- [ ] 1.3  Create `py/pytanga/basis/n2.py` with `BasisN2`
- [ ] 1.4  Create `py/pytanga/basis/pga2.py` with `BasisPGA2`
- [ ] 1.5  Update `py/pytanga/basis/__init__.py` — imports + `_CLASS_MAP` + `__all__`
- [ ] 1.6  Update `py/pytanga/algebra/_algebra.py` — add 2D names to `_BASIS_CLASS_NAMES`
- [ ] 1.7  Verify: `Algebra.from_name("E2")` returns a `BasisE2`
- [ ] 1.8  Verify: `Algebra.from_name("P2")` returns a `BasisP2`
- [ ] 1.9  Verify: `Algebra.from_name("N2")` returns a `BasisN2`
- [ ] 1.10 Verify: `Algebra.from_name("PGA2")` returns a `BasisPGA2`
- [ ] 1.11 Verify: `e1.gp(e2) == e12` in E2 (geometric product generates bivector)
- [ ] 1.12 Verify: `Algebra.from_name("PGA2")` is detected as PGA2 (not N2) — PGA2 is checked first in `_detect()`
- [ ] 1.13 Update `tools/build-precompiled.py` — add `(2, 0, "float64", "E2")` and `(4, 8, "float64", "N2/PGA2")` to `ALGEBRAS`. P2 reuses the existing `(3, 0, "float64", "E3/P2")` binding (same dim/sig as E3).
- [ ] 1.14 Verify: `uv run python tools/build-precompiled.py` bundles 2D algebra extensions in `precompiled/`
