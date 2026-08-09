# Merge Plan: Unify Dilator and GeneralDilator

**Status:** draft  
**Prerequisite for:** test-plan-n3-analysis.md, test-plan-n2-analysis.md

## Motivation

Currently there are two separate classes:

- `Dilator(factor)` — uniform scaling about the origin only
- `GeneralDilator(factor, translator)` — scaling about an arbitrary point, stores a `Translator` object

The geometric form of a general dilator is `D_t = T · D · T̃` (reverse translate, dilate, forward translate). The analysis in `dev/src/entities_04.py` shows that the translator and dilator parts can be extracted algebraically without blade factorization:

```python
E = einf ^ eo
d_part = dil_t | E         # extract D coefficient
t_part = dil_t.ip(eo).op(eo).ip(einf)  # extract translator coefficients
t_euc = -t_part / d_part[0]  # Euclidean translation vector
D = d_part[0]
d = (1 - D) / (1 + D)       # dilation factor
```

Because the same algebraic extraction works for both origin-only and displaced dilators, the two classes should be merged into a single `Dilator` class with an optional `origin` field.

## New API

```python
@dataclass(frozen=True)
class Dilator:
    """A uniform dilation (scaling) about an origin point.

    Form: D_t = T · D · T̃ where T translates from the global origin
    to the dilation center and D = 1 + (1−d)/(1+d)·E is the
    origin‑centered dilator (E = e∞∧e₀, Perwass).

    When origin=(0,0,0), this is a pure dilator about the origin:
    D = 1 + (1−d)/(1+d)·E, sandwich D·p·D̃ scales p by factor d.
    """

    factor: float
    origin: Point = field(default_factory=lambda: Point(0, 0, 0))
```

**Migration:**
- `Dilator(2.0)` → unchanged
- `GeneralDilator(2.0, Translator(Dir(1,0,0)))` → `Dilator(2.0, origin=Point(1,0,0))`

---

## Files to Modify

### 1. `py/pytanga/geometry/operators.py`

**Remove:**
- `GeneralDilator` class (lines 177–189)

**Modify `Dilator` class (lines 116–126):**
- Add `origin: Point = field(default_factory=lambda: Point(0, 0, 0))`
- Update docstring to describe both forms

**Update `Operator` union type (lines 210–223):**
- Remove `GeneralDilator` from the union

**Before:**
```python
@dataclass(frozen=True)
class Dilator:
    """A uniform dilation (scaling) about the origin.
    Supported algebras: N3 only (needs E = einfi∧eo)
    """
    factor: float
```

**After:**
```python
@dataclass(frozen=True)
class Dilator:
    """A uniform dilation (scaling) about an origin point.

    Form: D_t = T · D · T̃ where T translates from the global origin
    to the dilation center and D = 1 + (1−d)/(1+d)·E is the
    origin‑centered dilator (E = e∞∧e₀, Perwass).

    When ``origin=(0,0,0)``, this is a pure dilator about the origin.
    Supported algebras: N3/N2 only (needs E = e∞∧e₀)
    """
    factor: float
    origin: Point = field(default_factory=lambda: Point(0, 0, 0))
```

Also add `Point` to the imports at top:
```python
from .entities import Direction, Plane, Point
```
(`Point` is already imported, verify.)

---

### 2. `py/pytanga/geometry/analysis_n3.py`

**Update imports (lines 51–63):**
- Remove `GeneralDilator` from import

**Modify `_classify_double_reflector` (lines 533–559):**

**Before:**
```python
if has_E and not has_t:
    return _dilator_from_versor(mv)
elif has_E and has_t:
    dilator = _dilator_from_versor(mv)
    tx, ty, tz = translator_coeffs(mv, mv.algebra)
    translator = Translator(vector=Direction(tx, ty, tz))
    return GeneralDilator(factor=dilator.factor, translator=translator)
```

**After:**
```python
if has_E and not has_t:
    return _dilator_from_versor(mv)
elif has_E and has_t:
    dilator = _dilator_from_versor(mv)
    tx, ty, tz = translator_coeffs(mv, mv.algebra)
    return Dilator(factor=dilator.factor, origin=Point(tx, ty, tz))
```

**Add `Point` to imports** — already imported via `from .entities import ...` at lines 40–50. Verify `Point` is in the list.

**Update `analyze_operator` return type annotation** (lines 418–432):
- Remove `GeneralDilator` from the union
- Add `Point` to imports if not already present

**Update `_dilator_from_versor` (lines 605–615):**
- No change needed — it already returns `Dilator(factor=...)`. The `origin` field defaults to `(0,0,0)` which is correct for origin‑only dilators.

---

### 3. `py/pytanga/geometry/analysis_n2.py`

**Same changes as N3** — update imports, `_classify_double_reflector`, return type annotation.

**Before:**
```python
elif has_E and has_t:
    dilator = _dilator_from_versor(mv)
    tx, ty = translator_coeffs(mv, mv.algebra)
    translator = Translator(vector=Direction(tx, ty, 0.0))
    return GeneralDilator(factor=dilator.factor, translator=translator)
```

**After:**
```python
elif has_E and has_t:
    dilator = _dilator_from_versor(mv)
    tx, ty = translator_coeffs(mv, mv.algebra)
    return Dilator(factor=dilator.factor, origin=Point(tx, ty, 0.0))
```

---

### 4. `py/pytanga/geometry/create_n3.py`

**Merge `create_general_dilator` into `create_dilator`:**

**Before** (two functions, lines 276–348):
```python
def create_dilator(basis: Algebra, factor: float) -> MV:
    """D = 1 + (1−d)/(1+d)·E where E = e∞∧e₀ (Perwass)."""
    ...

def create_general_dilator(basis: Algebra, factor: float, translator: Translator) -> MV:
    """General dilator: D_t = T·D·T̃ (Perwass)."""
    t = create_translator(basis, translator.vector.x, translator.vector.y, translator.vector.z)
    d = create_dilator(basis, factor)
    return t.gp(d).gp(t.rev())
```

**After** (single function):
```python
def create_dilator(
    basis: Algebra,
    factor: float,
    *,
    origin: Point | None = None,
) -> MV:
    """Dilator about an origin point.

    D = 1 + (1−d)/(1+d)·E where E = e∞∧e₀ (Perwass).
    If origin is given, returns D_t = T·D·T̃ where T translates
    from global origin to the dilation center.
    """
    if factor <= 0:
        raise ValueError(f"Dilator factor must be positive, got {factor}")
    coeff = (1.0 - factor) / (1.0 + factor)
    E = get_einf(basis).op(get_eo(basis))
    d = basis.multivector({0: 1.0}) + E * coeff

    if origin is None:
        return d

    t = create_translator(basis, origin.x, origin.y, origin.z)
    return t.gp(d).gp(t.rev())
```

**Remove** `create_general_dilator` function entirely.

**Remove `Translator` from imports** if it was only used by `create_general_dilator` (check: it's also used by `create_motor` and `create_general_rotor`, so keep it).

**Add `Point` to imports** at top (line 32).

---

### 5. `py/pytanga/geometry/create_n2.py`

**Same changes as N3** — merge `create_general_dilator` into `create_dilator` with `origin` parameter, remove the old function.

---

### 6. `py/pytanga/geometry/create.py` (dispatcher)

**Update the dispatcher** (lines 208–273):

**Remove:**
```python
elif isinstance(operator, GeneralDilator):
    return mod.create_general_dilator(basis, operator.factor, operator.translator)
```

**Modify the `Dilator` case:**
```python
elif isinstance(operator, Dilator):
    return mod.create_dilator(basis, operator.factor, origin=operator.origin)
```

**Remove `GeneralDilator` from imports** (line 29).

---

### 7. `py/pytanga/geometry/__init__.py`

**Remove `GeneralDilator`** from the `from .operators import` block and from `__all__`.

---

### 8. All other `create_*.py` files (stubs that raise ValueError)

These files have `create_general_dilator` stubs that just raise `ValueError`. Remove them:

- `create_e3.py`
- `create_e2.py`
- `create_p3.py`
- `create_p2.py`
- `create_pga3.py`
- `create_pga2.py`

Check `create_pga3.py` especially — verify it doesn't have a working implementation.

---

### 9. `dev/src/entities_04.py`

No changes needed — already demonstrates the merged approach with `T · D · T̃`.

---

## Summary of Changes

| File | Action |
|------|--------|
| `operators.py` | Merge classes: add `origin` to `Dilator`, remove `GeneralDilator`, update `Operator` union |
| `analysis_n3.py` | Return `Dilator(factor, origin=Point(...))` instead of `GeneralDilator`, remove import |
| `analysis_n2.py` | Same as N3 |
| `create_n3.py` | Merge `create_general_dilator` into `create_dilator(..., origin=Point)`, remove old function |
| `create_n2.py` | Same as N3 |
| `create.py` | Update dispatcher: `Dilator` case passes `origin`, remove `GeneralDilator` case |
| `__init__.py` | Remove `GeneralDilator` from exports |
| `create_e3.py` | Remove `create_general_dilator` stub |
| `create_e2.py` | Remove `create_general_dilator` stub |
| `create_p3.py` | Remove `create_general_dilator` stub |
| `create_p2.py` | Remove `create_general_dilator` stub |
| `create_pga3.py` | Remove `create_general_dilator` stub (verify no working impl) |
| `create_pga2.py` | Remove `create_general_dilator` stub |

## Verification

After the merge, running existing PGA tests should still pass (PGA doesn't use dilators). Running any existing N3/N2 tests should also pass once the `GeneralDilator` references are updated.

The new N3/N2 analysis test files will be written against the merged API afterward.