# Update Plan: Algebraic Dilator Analysis

**Status:** draft  
**Prerequisite for:** test-plan-n3-analysis.md, test-plan-n2-analysis.md  
**Depends on:** merge-dilator-plan.md (unified `Dilator` class with `origin` field)

## Motivation

Current `_dilator_from_versor` in both N3 and N2 extracts the dilation factor using
blade coefficient access (`mv[0]` and `E_coefficient`):

```python
a0 = float(mv[0])
aE = E_coefficient(mv, mv.algebra)
factor = (a0 - aE) / (a0 + aE)
return Dilator(factor=factor)
```

This works for a pure `D = 1 + (1−d)/(1+d)·E` dilator, but for a general dilator
`D_t = T · D · T̃` the coefficients are mixed — the scalar `mv[0]` and E-coefficient
carry contributions from both the dilation and translation parts.

The algebra-based approach from `dev/src/entities_04.py` cleanly separates them
using left-contraction with E and a chain of inner/outer products:

```python
E = einf ^ eo
d_part = mv | E                              # 0-vector: scalar + possibly others
t_part = mv.ip(eo).op(eo).ip(einf)           # grade-1: translator coefficients
t_euc = -t_part / d_part[0]                  # Euclidean translation vector
D = d_part[0]                                # scalar coefficient
d = (1 - D) / (1 + D)                        # dilation factor
```

For a pure origin-dilator: `t_part ≈ 0`, `origin = (0,0,0)`.  
For a general dilator: `t_part ≠ 0`, `origin = Point(t_euc.x, t_euc.y, t_euc.z)`.

## Algebraic Derivation

Given `D = 1 + c·E` where `c = (1−d)/(1+d)` and `E = e∞∧e₀`:

| Step | Expression | Result |
|------|-----------|--------|
| 1 | `mv \| E` | `D \| E = (1 + c·E) \| E = 1\|E + c·(E\|E)` |
|   |   | Since `E\|E = 1`  |
|   | `1 \| E = 0` (scalar contravts with bivector → 0) | |
|   | `E \| E = 1` | `E\|E = E·E = 1` |
|   | So `D \| E = c·(−1) = −c` and `d_part[0] = −c` | |
| 2 | `d = (1 − D)/(1 + D)` → from Perwass: `D = −c` where `c = (1−d)/(1+d)` | |
|   | `d_part[0] = −(1−d)/(1+d)` | |
|   | `d = (1 + d_part[0]) / (1 − d_part[0])` | |

Check with entities_04.py: `D = d_part[0]; d = (1 - D) / (1 + D)`.
So if `d_part[0] = −c` and `c = (1−d)/(1+d)`, then:
`d = (1 − (−c)) / (1 + (−c)) = (1 + c) / (1 − c)`
If `c = (1−d)/(1+d)`, then `(1+c)/(1−c) = … = d`. ✅ Correct.

For the translator extraction from `D_t = T·D·T̃`:
`t_part = D_t.ip(eo).op(eo).ip(einf)` extracts the grade-1 translator vector part.
In the general dilator `T·D·T̃`, the E and translation coefficients are separable
via the contractions shown.

---

## Changes

### 1. `py/pytanga/geometry/_n3_helpers.py` — new helper `analyze_dilator_mv`

Add a new function that extracts both the dilation factor and origin point
from an MV using the algebraic approach.

```python
def analyze_dilator_mv(mv: MV, basis: Algebra) -> tuple[float, float, float, float]:
    """Extract (factor, origin_x, origin_y, origin_z) from a dilator MV.

    Uses algebraic extraction (no blade factorization):

        E = einf ∧ eo
        d_part = mv | E                          # scalar related to D
        t_part = mv.ip(eo).op(eo).ip(einf)        # grade-1 translator vector
        t_euc = -t_part / d_part[0]               # Euclidean origin point
        factor = (1 - d_part[0]) / (1 + d_part[0])

    For a pure origin-dilator D = 1 + c·E: t_part ≈ 0, origin = (0,0,0).
    For a general dilator D_t = T·D·T̃: t_part ≠ 0, origin = t_euc.

    Returns (factor, ox, oy, oz).
    """
    einf = get_einf(basis)
    eo = get_eo(basis)

    E = einf.op(eo)                              # e∞∧e₀
    d_part = mv.ip(E)                            # left-contraction: extract D part
    if abs(float(d_part[0])) < 1e-15:
        raise ValueError("Degenerate dilator: D coefficient is zero")

    t_part = mv.ip(eo).op(eo).ip(einf)           # translator part extraction
    t_euc = t_part * (-1.0 / float(d_part[0]))   # Euclidean origin

    D = float(d_part[0])
    factor = (1.0 - D) / (1.0 + D)
    if factor <= 0:
        raise ValueError(f"Dilator factor must be positive, got {factor}")

    return factor, float(t_euc[E1]), float(t_euc[E2]), float(t_euc[E3])
```

Note: `mv.ip(E)` is the left-contraction (inner product on E). In the codebase,
`|` operator is the left-contraction (`ip`). The `E` is already a bivector.
Verify that `mv | E` in the TANGA codebase corresponds to `mv.ip(E)`.
Based on `entities_04.py`:
```python
d_part = dil_t | E      # uses | operator
```
So in the helper, use `mv.ip(E)` (or `mv.sp(E)` if that's the same) — but `|` is `ip`.
We'll call it through the MV directly.

Actually, the helper should just be integrated into the analysis functions directly,
not added as a separate helper. Keep it inline. Let me revise.

---

### 2. `py/pytanga/geometry/analysis_n3.py` — rewrite `_dilator_from_versor`

**Before:**
```python
def _dilator_from_versor(mv: MV) -> Dilator:
    """Perwass: D = a0 + aE·E, d = (a0 − aE)/(a0 + aE)."""
    a0 = float(mv[0])
    aE = E_coefficient(mv, mv.algebra)
    denom = a0 + aE
    if abs(denom) < 1e-15:
        raise ValueError("Degenerate dilator: a0 + aE ≈ 0")
    factor = (a0 - aE) / denom
    if factor <= 0:
        raise ValueError(f"Dilator factor must be positive, got {factor}")
    return Dilator(factor=factor)
```

**After:**
```python
def _dilator_from_versor(mv: MV) -> Dilator:
    """Extract factor and origin from a dilator MV via algebraic extraction.

    Uses left-contraction with E = e∞∧e₀ and ip-op-op-ip chain
    (see dev/src/entities_04.py).  No blade factorization needed.

    Pure dilator:   origin defaults to (0,0,0).
    General dilator (T·D·T̃): origin extracted from translator part.
    """
    alg = mv.algebra
    einf = get_einf(alg)
    eo = get_eo(alg)
    E = einf.op(eo)  # e∞∧e₀

    # Extract scalar D part: d_part = mv | E
    d_part = mv.ip(E)
    D_val = float(d_part[0])
    if abs(D_val) < 1e-15:
        raise ValueError("Degenerate dilator: D coefficient is zero")

    # Extract translator part: t_part = mv.ip(eo).op(eo).ip(einf)
    t_part = mv.ip(eo).op(eo).ip(einf)
    t_euc = t_part * (-1.0 / D_val)

    factor = (1.0 - D_val) / (1.0 + D_val)
    if factor <= 0:
        raise ValueError(f"Dilator factor must be positive, got {factor}")

    # Determine if general dilator (has non-zero translator part)
    tx = float(t_euc[E1])
    ty = float(t_euc[E2])
    tz = float(t_euc[E3])
    t_norm = math.sqrt(tx * tx + ty * ty + tz * tz)

    if t_norm < 1e-10:
        return Dilator(factor=factor)
    else:
        return Dilator(factor=factor, origin=Point(tx, ty, tz))
```

Key differences:
- No `E_coefficient` / `mv[0]` blade access
- Extracts both factor and origin in one function
- Handles both pure and general dilators

---

### 3. `py/pytanga/geometry/analysis_n3.py` — simplify `_classify_double_reflector`

Now that `_dilator_from_versor` handles both cases, the double reflector
just needs to check `has_E_component` and delegate:

**Before:**
```python
def _classify_double_reflector(mv: MV, einf: MV, eo: MV, factors: list[MV]):
    ...
    if has_E and not has_t:
        return _dilator_from_versor(mv)
    elif has_E and has_t:
        dilator = _dilator_from_versor(mv)
        tx, ty, tz = translator_coeffs(mv, mv.algebra)
        translator = Translator(vector=Direction(tx, ty, tz))
        return GeneralDilator(factor=dilator.factor, translator=translator)
    else:
        ...
```

**After:**
```python
def _classify_double_reflector(mv: MV, einf: MV, eo: MV, factors: list[MV]):
    """Classify 2-factor versor by blade components.

    - E-only (e∞∧e₀) → Dilator (possibly with origin via T·D·T̃)
    - Everything else → delegated to :func:`ana_versor_generic`
    """
    has_E = has_E_component(mv, mv.algebra)

    if has_E:
        return _dilator_from_versor(mv)
    else:
        # Rotor, Translator, or GeneralRotor
        return ana_versor_generic(
            mv,
            einf_like=einf,
            e0_inv_like=-eo,
            extract_translator=_translator_from_versor,
            is_2d=False,
        )
```

Removed: `has_translator_components` check, `translator_coeffs` call,
`Translator` construction, `GeneralDilator` usage.

---

### 4. `py/pytanga/geometry/analysis_n2.py` — same changes

Apply identical changes to the N2 `_dilator_from_versor` and `_classify_double_reflector`.
The only difference: tx, ty only (2D, z=0).

**`_dilator_from_versor` after:**
```python
def _dilator_from_versor(mv: MV) -> Dilator:
    ...same as N3 but:
    tx = float(t_euc[E1])
    ty = float(t_euc[E2])
    t_norm = math.sqrt(tx * tx + ty * ty)

    if t_norm < 1e-10:
        return Dilator(factor=factor)
    else:
        return Dilator(factor=factor, origin=Point(tx, ty, 0.0))
```

**`_classify_double_reflector` after:**
Identical simplified logic as N3 (just `has_E → _dilator_from_versor`).

---

### 5. Remove now-unused imports

After these changes, the following may become unused:

**In `analysis_n3.py`:**
- `has_translator_components` — no longer used in `_classify_double_reflector`
  (but check: is it used elsewhere?  Only in `_classify_double_reflector` and in `analyze_operator` docstring)
- `translator_coeffs` — still used by `_translator_from_versor`, so keep
- `GeneralDilator` — removed as part of merge-dilator-plan.md
- `Translator` — still used by `_translator_from_versor` and type annotations
- `E_coefficient` — no longer used in `_dilator_from_versor`; check other uses

**In `analysis_n2.py`:**
- Same analysis applies.

---

### 6. Verify: `has_E_component` is still needed

Yes — `_classify_double_reflector` uses it to decide whether to route to
`_dilator_from_versor` or `ana_versor_generic`.

---

## Summary of Changes

| File | Change |
|------|--------|
| `analysis_n3.py` | Rewrite `_dilator_from_versor` with algebraic extraction; simplify `_classify_double_reflector`; remove unused imports |
| `analysis_n2.py` | Same as N3 (2D variant) |

No new helper functions needed — the logic is short enough to stay inline.

## Verification

After the change:
- `Dilator(2.0)` round-trip: factor=2.0, origin=(0,0,0)
- `Dilator(2.0, origin=(1,0,0))` round-trip: factor=2.0, origin=(1,0,0)
- General dilator → `T·D·T̃` sandwich should produce the same geometric result as before
- Existing PGA tests remain unaffected (no dilator usage)