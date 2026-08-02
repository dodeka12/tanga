# Duals and Complements in TANGA C++

## Overview

TANGA provides three operations for blade complementation and dualization:

| Function | Formula | dual-of-dual | Uses inverse? |
|----------|---------|-------------|---------------|
| `GA::Complement` | blade_id XOR pseudoscalar_id (no sign) | `A` always | N/A — bitwise |
| `GA::Dual` | ★A = A · I⁺ (right dual) | ±A | Yes (pseudoinverse) |
| `GA::LDual` | I · A (left dual) | ±A | No — uses I directly |

## Complement — `GA::Complement`

The complement maps each basis blade to its **bitwise complement** within
the algebra:

```
complement_blade_id = blade_id XOR pseudo_scalar_id
```

No sign change is applied to the coefficient. This is an involution:

```
Complement(Complement(A)) = A   for all dimensions and signatures
```

This operation is implemented in:
- **`CBlade::GetComplement(blComplement)`** — returns the complement blade mask only.
- **`CBlade::GetComplement(fValue, blComplement)`** — complement blade mask, coefficient unchanged.
- **`GA::Complement(wB, wA)`** — multivector-level complement.

```cpp
// Example (E3)
TDynMV wA = ...;              // 2.0 * e1 + 3.0 * e12
TDynMV wB;
GA::Complement(wB, wA);       // 2.0 * e23 + 3.0 * e3  (no sign changes)
GA::Complement(wB, wB);       // recovers wA exactly
```

The complement is a **purely combinatorial** operation — a simple XOR at
the bitmask level. Use it for bitmask-based algorithms, blade mask
trajectory tracking, or when the sign is irrelevant or handled separately.

**Do not use** `Complement` for geometric entity dualization. Use `Dual` for
that — it correctly accounts for the permutation parity between a blade and
its complement within the pseudoscalar.

## Signed Dual — `GA::Dual`

The signed dual implements the standard Clifford algebra dual:

```
★A = A · I⁺
```

where I⁺ is the pseudoinverse of the pseudoscalar I. The blade mask is the
same bitwise complement, but the coefficient receives a sign correction
derived from:

- The geometric product reordering swaps between A and I.
- The conjugate sign of the pseudoscalar (`I⁺ = conjugate(I) / IP(I, conjugate(I))`).

### Why `Dual` is the "correct" dual

In G(3,0) with I = e₁₂₃ (I² = −1), the signed dual satisfies:

```
★(a ∧ b) = (a ∧ b) · I⁻¹ = a × b
```

This is the standard vector cross product identity. `Complement` does **not**
satisfy this because it misses the permutation parity sign from `GPSign()`.
Concretely:

| Blade B | Complement(B) | Dual(B) | Swaps |
|---------|--------------|---------|-------|
| e₁₂ | e₃ | e₃ | 0 — even |
| e₁₃ | e₂ | **−**e₂ | 1 — odd |
| e₂₃ | e₁ | e₁ | 2 — even |

The dual-of-dual sign depends on dimension `D` and the number `s` of
negative-signature basis vectors:

```
★★A = (−1)^(D(D−1)/2 + s) · A
```

| D | s | sign(★★A) | Example |
|---|----|-----------|---------|
| 1 | 0 | +1 | G(1) |
| 2 | 0 | −1 | G(2) |
| 3 | 0 | −1 | E3 |
| 4 | 0 | +1 | G(4) |
| 4 | 1 | −1 | Spacetime G(3,1) |
| 4 | 2 | +1 | G(2,2) |

This operation is implemented in:
- **`CBlade::GetDualSign(uSign, blDual)`** — computes the sign.
- **`CBlade::GetDual(fValue, blDual)`** — applies the sign to the coefficient.
- **`GA::Dual(wB, wA)`** — multivector-level signed dual.

```cpp
// Example (E3, D=3, s=0)
TDynMV wA = ...;          // 2.0 * e1
TDynMV wB;
GA::Dual(wB, wA);         // 2.0 * e23  (correct sign from GPSign)
GA::Dual(wB, wB);         // −A in E3  (★★A = −A for D=3)
```

## Left Dual — `GA::LDual`

The left dual left-multiplies by the pseudoscalar:

```
LDual(A) = I · A
```

Unlike `Dual` (right multiplication with I⁺), `LDual` uses I directly —
no inverse is needed. This makes it simpler and more robust for algebras
where the pseudoscalar is not invertible (e.g. PGA with I² = 0).

**Relation in invertible algebras:**

Since I⁻¹ = −I in Cl(3):
```
LDual(A) = I · A = (−1)^k · Dual(A)   for grade‑k elements
```

This operation is implemented in:
- **`CBlade::GetLeftDualSign(uSign, blDual)`** — computes the sign.
- **`CBlade::GetLeftDual(fValue, blDual)`** — applies the sign to the coefficient.
- **`GA::LDual(wB, wA)`** — multivector-level left dual.

Key difference from `GetDual`: the `GPSign` call has the pseudoscalar as the
**left** operand (`GPSign(uSign, blDual, blPS, *this)`), and there is no
`GetConjugateSign()` correction (since we use I directly, not I⁺).

```cpp
TDynMV wA = ...;          // 2.0 * e1
TDynMV wB;
GA::LDual(wB, wA);        // −2.0 * e23  (I·e₁ = −e₂₃ in G(3,0))
```

## Implementation Reference

| File | Function / Method | Role |
|------|------------------|------|
| `cpp/Tan.GA/Blade.h` | `CBlade::GetComplement()` | Complement at blade level |
| `cpp/Tan.GA/Blade.h` | `CBlade::GetDual()` | Signed dual at blade level |
| `cpp/Tan.GA/Blade.h` | `CBlade::GetDualSign()` | Signed dual sign only |
| `cpp/Tan.GA/Blade.h` | `CBlade::GetLeftDual()` | Left dual at blade level |
| `cpp/Tan.GA/Blade.h` | `CBlade::GetLeftDualSign()` | Left dual sign only |
| `cpp/Tan.GA/MV_Operators.h` | `GA::Complement()` | Complement at multivector level |
| `cpp/Tan.GA/MV_Operators.h` | `GA::Dual()` | Signed dual at multivector level |
| `cpp/Tan.GA/MV_Operators.h` | `GA::LDual()` | Left dual at multivector level |

## When to Use Which

- Use **`GA::Complement`** for purely combinatorial complements: bitmask-based
  algorithms, blade mask trajectory tracking, or when the sign is irrelevant or
  handled separately.
- Use **`GA::Dual`** for the standard Clifford algebra dual ★A = A · I⁺ with
  the correct sign for all algebraic identities (e.g., PGA duality relationships,
  Hodge star applications, OPNS ↔ IPNS conversion).
- Use **`GA::LDual`** when you need the left dual I · A — simpler for
  non-invertible pseudoscalars (no pseudoinverse needed), or when a left
  convention is preferred.