# Duals and Complements in pytanga

pytanga exposes three operations for blade complementation and dualization:

| Method | Formula | dual-of-dual | Uses inverse? |
|--------|---------|-------------|---------------|
| `mv.complement()` | blade_id XOR pseudoscalar_id (no sign) | `A` always | N/A — bitwise |
| `mv.dual()` | ★A = A · I⁺ (right dual) | ±A | Yes (pseudoinverse) |
| `mv.ldual()` | I · A (left dual) | ±A | No — uses I directly |

## Complement — `mv.complement()`

The complement maps each basis blade to its **bitwise complement** within
the algebra. No sign changes are applied to coefficients:

```python
from pytanga import Algebra

alg = Algebra(3, 0)  # E3
a = alg({"e1": 2.0, "e12": 3.0})

b = a.complement()
print(b)  # 2.0 e23 + 3.0 e3  (no sign changes)
print(b.complement())  # recovers a exactly
```

This is an involution for all dimensions and signatures:
```
a.complement().complement() == a   # always True
```

The complement is a **purely combinatorial** operation — a simple
`blade_id XOR pseudoscalar_id` at the bitmask level. It is NOT the
Clifford dual and does **not** satisfy geometric dual identities
like `★(a ∧ b) = a × b`.

Use `complement()` for:

- Bitmask-based algorithms
- Blade mask trajectory tracking
- Index gymnastics where sign is irrelevant or handled separately

**Do not use** `complement()` for geometric entity dualization
(OPNS ↔ IPNS conversion). Use `dual()` for that — it correctly accounts
for the permutation parity between a blade and its complement within
the pseudoscalar.

## Signed Dual — `mv.dual()`

The signed dual implements the standard Clifford algebra dual:

```
★A = A · I⁺
```

where I⁺ is the pseudoinverse of the pseudoscalar I. The blade mask is
the same bitwise complement as `complement()`, but the coefficient
receives a sign correction accounting for the geometric product with the
inverse pseudoscalar:

```python
alg = Algebra(3, 0)  # E3
a = alg({"e1": 2.0})

b = a.dual()
# b = 2.0 * e23  (with correct sign — ± depends on metric and dimension)
```

### Why `dual()` is the "correct" dual

In G(3,0) with pseudoscalar I = e₁₂₃ (I² = −1, I⁻¹ = −I = e₃₂₁), the
signed dual satisfies:

```
★(a ∧ b) = (a ∧ b) · I⁻¹ = a × b
```

This is the standard vector cross product identity. The complement does
**not** satisfy this because it misses the sign from reordering the blade
basis vectors with the pseudoscalar. Concretely:

| Blade B | complement(B) | dual(B) | Reason |
|---------|--------------|---------|--------|
| e₁₂ | e₃ | e₃ | 0 swaps — even |
| e₁₃ | e₂ | **−**e₂ | 1 swap — odd |
| e₂₃ | e₁ | e₁ | 2 swaps — even |

The sign arises from the permutation parity counted by `GPSign()` in the
C++ backend — swapping basis vectors of the blade with those of the
pseudoscalar to bring them into canonical order.

### Dual-of-Dual Sign

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

## Left Dual — `mv.ldual()`

The left dual multiplies by the pseudoscalar from the left:

```
ldual(A) = I · A
```

Unlike `dual()` (right multiplication with the pseudoinverse I⁺),
`ldual()` uses I directly — no inverse is needed. This makes it simpler
and more robust for algebras where the pseudoscalar is not invertible
(e.g. PGA, where I² = 0 and I has no proper inverse).

```python
alg = Algebra(3, 0)  # E3
a = alg({"e1": 2.0})

b = a.ldual()
# b = -2.0 * e23  (I·e₁ = −e₂₃ in G(3,0) since I = e₁₂₃)
```

**Relation in G(3,0):**

Since I⁻¹ = −I in Cl(3):
```
ldual(A) = I · A = −(A · I⁻¹) = −dual(A)   for odd-grade A
ldual(A) = I · A = A · I⁻¹ = dual(A)       for even-grade A (since I² = −1)
```

Equivalently: `ldual(A) = (−1)^k · dual(A)` for grade‑k elements.

## Operation Summary

| Operation | Formula | In G(3,0) on a∧b | Use case |
|-----------|---------|-------------------|----------|
| `complement(A)` | bitwise XOR, no sign | wrong sign on e₂ component | Bitmask gymnastics |
| `dual(A)` | A · I⁺ | **a × b** ✓ | Standard geometry dual (OPNS↔IPNS) |
| `ldual(A)` | I · A | −(a × b) = −dual(A) | When I is non-invertible, or left convention |

## Implementation Reference

| Layer | Location | Details |
|-------|----------|---------|
| C++ blade | `CBlade::GetComplement()`, `CBlade::GetDual()`, `CBlade::GetLeftDual()` | Bitmask XOR and sign computation |
| C++ MV | `GA::Complement()`, `GA::Dual()`, `GA::LDual()` | Per-blade iteration |
| Python | `MV.complement()`, `MV.dual()`, `MV.ldual()`, plus `Algebra` counterparts | User-facing API |