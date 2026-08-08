# Refactor: GeneralRotor — use `(angle, axis, origin)` instead of `(rotor, translator)`

**Status:** planned  
**Created:** 2026-08-07

## Rationale

The `GeneralRotor` dataclass currently stores `(rotor: Rotor, translator: Translator)`, which is geometrically misleading. A GeneralRotor represents a rotation about an **arbitrary origin point** (not the global origin). Its defining geometric parameters should be:

- **`angle: float`** — angle of rotation in radians
- **`axis: Direction`** — rotation axis (always `(0,0,1)` in 2D)
- **`origin: Point`** — the rotation center point (z=0 in 2D)

The current `translator: Translator` field is actually the displacement vector from the global origin to the rotation center. Flattening to three scalar/vector fields — no nested dataclass — makes the API self-documenting and prevents user errors.

### MV Construction

The underlying MV construction remains `G = T · R · T̃` (conjugate the rotor by the translator), which is mathematically correct. The change is purely in the dataclass API — the translation vector is computed internally from the origin point, and the rotor bivector is computed from angle+axis.

### Bug Fix

The change also fixes the **double-displacement bug** in `_general_rotor_from_versor`. The current code extracts raw translator coefficients from the null bivector part:
```python
dx = -2.0 * float(mv[5]) / scal  # produces double the expected value
```
The correct origin point is derived from the versor's internal structure: the null bivector encodes `c · R_bivector` where `c` is the rotation center. Solving gives `origin = (dx/2, dy/2)` from the raw coefficients.

## New Dataclass

```python
@dataclass(frozen=True)
class GeneralRotor:
    """A rotation about an arbitrary origin point.

    In 2D the axis is always Dir(0,0,1) and origin z=0.
    """
    angle: float
    axis: Direction
    origin: Point = field(default_factory=lambda: Point(0, 0, 0))

    def __repr__(self) -> str:
        deg = math.degrees(self.angle)
        return f"GenRotor({deg:.1f}° about {self.axis} at {self.origin})"
```

## Files to Change

### 1. Dataclass definition
- [ ] **`py/pytanga/geometry/operators.py`** — Redefine `GeneralRotor` as above. Remove `Rotor` import from it (still used by `Motor`). Add `field` import from dataclasses.

### 2. Creation modules
- [ ] **`py/pytanga/geometry/create_pga2.py`** — Change signature to `create_general_rotor(basis, angle, axis, origin)`:
  - Compute translator vector from `origin` → `Translator(Direction(origin.x, origin.y, 0))`.
  - Compute rotor MV from `angle` + `axis`.
  - Return `T·R·T̃`.
- [ ] **`py/pytanga/geometry/create_pga3.py`** — Same change, 3D version (origin z ≠ 0, axis arbitrary).
- [ ] **`py/pytanga/geometry/create_n2.py`** — Check if `create_general_rotor` exists; update if so.
- [ ] **`py/pytanga/geometry/create_n3.py`** — Check if `create_general_rotor` exists; update if so.

### 3. Analysis modules
- [ ] **`py/pytanga/geometry/analysis_pga2.py`** — `_general_rotor_from_versor(mv)` → returns `GeneralRotor(angle=..., axis=..., origin=...)`:
  - **angle** from `atan2(b_norm, scal)` (existing logic, unchanged)
  - **axis** → `Direction(0, 0, 1)` (2D)
  - **origin** from null bivector: `dx = -2.0 * mv[5]`, `dy = -2.0 * mv[6]` → **divide by 2** to get origin point (fixes double-displacement bug)
- [ ] **`py/pytanga/geometry/analysis_pga3.py`** — `_general_rotor_from_versor(mv)` → same but 3D axis + 3D origin
- [ ] **`py/pytanga/geometry/analysis_n2.py`** — `_classify_quad_reflector()`:
  Construct `GeneralRotor(angle=rotor.angle, axis=rotor.axis, origin=origin)` from extracted rotor + translator.
- [ ] **`py/pytanga/geometry/analysis_n3.py`** — `_classify_quad_reflector()`: Same change.

### 4. Dispatcher
- [ ] **`py/pytanga/geometry/create.py`** — Line 267:
  ```python
  return mod.create_general_rotor(basis, operator.angle, operator.axis, operator.origin)
  ```

### 5. Callers (instantiation sites)
- [ ] **`py/tests/geometry/test_geometry_pga2_analysis.py`** — `GeneralRotor(Rotor(...), Translator(...))` → `GeneralRotor(angle=..., axis=..., origin=...)`
- [ ] **`py/tests/geometry/test_geometry_pga2.py`** — Same pattern
- [ ] **`py/tests/geometry/test_geometry_n3.py`** — Same pattern
- [ ] **`py/tests/geometry/test_geometry_n2.py`** — Same pattern
- [ ] **`py/tests/viz/test_serializer.py`** — `test_general_rotor`: use `angle=..., axis=..., origin=...`
- [ ] **`py/examples/geometry/n3_operators.py`** — Any `GeneralRotor(...)` calls
- [ ] **`dev/src/bug_general_rotor_pga2.py`** — Update to new API

### 6. Visualization (access `.angle`, `.axis`, `.origin` instead of `.rotor.*` / `.translator.vector`)
- [ ] **`py/pytanga/viz/_label.py`** — Access `entity.angle`, `entity.axis`, `entity.origin`
- [ ] **`py/pytanga/viz/_label_frame.py`** — Same
- [ ] **`py/pytanga/viz/serializer.py`** — `_serialize_general_rotor`: serialize `angle`, `axis`, `origin`
- [ ] **`py/pytanga/viz/_styles/_operator_styles.py`** — No code change needed (style only)
- [ ] **`py/pytanga/viz/export/_gltf.py`** — Access `entity.get("origin")` instead of looking for rotor/translator

### 7. Analysis dispatcher
- [ ] **`py/pytanga/geometry/analysis.py`** — `analyze_operator` dispatcher may reference `GeneralRotor` in type hints; no change needed unless it constructs one.

## Implementation Order

1. Redefine `GeneralRotor` dataclass in `operators.py`
2. Update `create_pga2.py` and `create_pga3.py` creation functions
3. Update `analysis_pga2.py` and `analysis_pga3.py` analysis functions (incl. bug fix — origin = null_coeffs / 2)
4. Update `analysis_n2.py` and `analysis_n3.py`
5. Update `create.py` dispatcher
6. Update all callers (tests, viz, examples, bug scripts)
7. Run the full test suite

## Verification

After all changes:
- `py/tests/geometry/test_geometry_pga2_analysis.py` — all 13 tests pass, A6 (GeneralRotor application) unskipped and passing
- `py/tests/geometry/test_geometry_pga2.py` — test_general_rotor_round_trip passes
- `py/tests/geometry/test_geometry_n3.py` — test_general_rotor_round_trip passes
- `dev/src/bug_general_rotor_pga2.py` — outputs `Point(1, 2, 0)` instead of `(1, 4)`