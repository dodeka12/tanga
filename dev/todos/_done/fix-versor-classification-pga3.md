# Fix PGA3 Versor Classification in Operator Analysis

## Problem

`analyze_operator` in `py/pytanga/geometry/analysis_pga3.py` uses `blade_factorize_versor()` to decompose a versor into grade-1 vector factors, then classifies the versor by inspecting null-vector content of those factors (`_has_null` on EP/EM blade IDs). This fails in the 5D embedding because `e0 = ep + em` splits null content across two factor components, causing:

- **Pure translator** (`1 - ½·e10`) → one factor appears Euclidean, one null → `has_null_flags = [True, False]` → classified as "mixed" → routes to `_general_rotor_from_versor` → fails with "GeneralRotor has zero Euclidean bivector part"

Additionally:
- No error handling around `blade_factorize_versor` — if factorization fails, the raw C++ exception is unhelpful
- `n == 3` (three reflectors → e.g. reflection·rotor/translator) is unhandled → crashes with "Unexpected 3 factors"

## Root Cause

The classification relies on **secondary factor properties** (null content of grade-1 factors) which behave differently in the 5D embedding, rather than on the **versor's own geometric content** via actual PGA products.

## Proposed Solution

### 1. Versor validation

Wrap `blade_factorize_versor` in `try/except` in `analyze_operator()`. On failure, raise a clear `ValueError("MV is not a versor — cannot be factorized into grade-1 vectors")`.

### 2. Geometric classification for n == 2

Classify the versor by directly testing its geometric content, not its factors:

| Test | Meaning |
|---|---|
| `V · e0_inv` contains non-zero E1/E2/E3 parts | V has null bivector (translational) content |
| `V ^ e0` contains grade > 1 components | V has Euclidean bivector (rotational) content |

Classification:

| `V · e0_inv` has E1/E2/E3 | `V ^ e0` has grade > 1 | Result |
|---|---|---|
| No | Yes | **Rotor** |
| Yes | No | **Translator** |
| Yes | Yes | **GeneralRotor** |
| No | No | Error: unrecognized |

Implement two helper functions:
- `_versor_has_null_part(versor, basis)` — compute `V · e0_inv`, check for E1/E2/E3 components
- `_versor_has_euclidean_bivector(versor, basis)` — compute `V ^ e0`, check for grade > 1

### 3. Triple reflection (n == 3)

Three plane reflections composed is geometrically a **reflection × rotor** (or reflection × translator, or reflection × general rotor). Since the decomposition is not unique, we don't attempt to factor into rotor+translator. Instead, introduce a new operator type that preserves the raw factor information.

#### New dataclass in `py/pytanga/geometry/operators.py`

```python
@dataclass(frozen=True)
class TripleReflection:
    """Three successive plane reflections."""
    planes: tuple[Plane, Plane, Plane]

    def __repr__(self) -> str:
        return f"TripleRefl({self.planes[0]}, {self.planes[1]}, {self.planes[2]})"
```

#### New helper in `analysis_pga3.py`

```python
def _triple_reflection_from_factors(factors: list[MV]) -> TripleReflection:
    planes = tuple(_plane_from_vector(f) for f in factors)
    return TripleReflection(planes=planes)
```

### 4. Update n == 4 (Motor)

Already uses factors for the Euclidean rotor part and versor coefficients for the translator part. Keep as-is but use the new geometric helpers? Maybe, but not required for this fix.

## Files to Change

1. **`py/pytanga/geometry/operators.py`**
   - Add `TripleReflection` dataclass
   - Add to `Operator` union type

2. **`py/pytanga/geometry/analysis_pga3.py`**
   - Add `try/except` around `blade_factorize_versor`
   - Add `_versor_has_null_part()` and `_versor_has_euclidean_bivector()` helpers
   - Replace `n == 2` classification block (lines 349–356) with geometric tests
   - Add `_triple_reflection_from_factors()` helper
   - Handle `n == 3` → `TripleReflection`

3. **`py/pytanga/geometry/analysis.py`**
   - Import `TripleReflection` from `.operators`

4. **`py/pytanga/geometry/__init__.py`** (if needed)
   - Export `TripleReflection`

## Verification

Run `python dev/src/entities_03.py` — should now output:
```
...
translator: 1 - 0.5 e01
...
Transl(Dir(-1.00, 0.00, 0.00))