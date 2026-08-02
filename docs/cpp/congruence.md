# Congruence Maps

A **congruence** in TanGA is an object that supplies two scalar operations to
the Gaussian elimination engine:

| Method | Role |
|--------|------|
| `Map(result, value) → bool` | Normalise a value before it enters a matrix row |
| `InvMap(result, value) → bool` | Compute the "inverse" of a value used as a pivot |

Both methods return `false` when the operation is undefined (division by zero,
non-invertible pivot), which causes `GA::Inverse` to return an error code
instead of producing a garbage result.

The name comes from number theory: two integers are *congruent modulo N* when
they have the same residue. By making `Map` and `InvMap` swappable, the same
Gaussian elimination code works over floating-point fields and over integer
residue rings.

---

## Required Header

```cpp
#include "Tan.Math/Congruence.h"
```

---

## `CCongruence_Float<T>` — floating-point field

Use this for multivectors with `float` or `double` components.

```cpp
Tan::CCongruence_Float<double> xCongruence;
```

| Method | Behaviour |
|--------|-----------|
| `Map(result, value)` | Identity: `result = value`. Always succeeds. |
| `InvMap(result, value)` | Reciprocal: `result = 1 / value`. Returns `false` when `value == 0`. |

`Map` is the identity because floating-point values do not need normalisation.
`InvMap` is ordinary division, so every non-zero pivot is invertible.

---

## `CCongruence_HMod<T>` — modular integer ring

Use this for multivectors with integer components (e.g. `int64_t`) whose
values are computed modulo a prime `N`.

```cpp
int64_t tMod = 7;
Tan::CCongruence_HMod<int64_t> xCongruence(tMod);
```

| Method | Behaviour |
|--------|-----------|
| `Map(result, value)` | Half-space modular reduction: maps `value` into $\bigl[\lfloor N/2 \rfloor - N + 1,\; \lfloor N/2 \rfloor\bigr]$ |
| `InvMap(result, value)` | Modular multiplicative inverse via extended Euclidean algorithm. Returns `false` when `gcd(value, N) ≠ 1`. |

### Half-space modular reduction (`hmod`)

Standard modular reduction maps to $[0, N)$. The half-space variant centres
the range around zero:

$$\text{hmod}(v, N) = ((v \bmod N) + N) \bmod N - \text{adjustment if} > N/2$$

Examples for $N = 7$: $-4 \mapsto 3$, $\;4 \mapsto -3$, $\;8 \mapsto 1$.

This keeps coefficient magnitudes small and avoids wrap-around artefacts in
intermediate steps of Gaussian elimination.

### Modular multiplicative inverse (`hmod_inv`)

`hmod_inv(a, N)` finds $a^{-1}$ such that $(a \cdot a^{-1}) \bmod N = 1$.
It uses the extended Euclidean algorithm internally. If $\gcd(a, N) \neq 1$
then no inverse exists and the method returns 0 (the caller sees `false`).
This is the reason the modulus must be prime (or at least coprime to every
expected pivot).

---

## How congruence is used in `GA::Inverse`

`GA::Inverse` solves $A \cdot X = 1$ for a multivector `X`:

```cpp
GA::EResult Inverse(TMultivector& wInv, const TMultivector& _wA,
                    const TCongruence& xCongruence);
```

Internally it proceeds in four steps:

1. **Normalise** — applies `Map` to every component of `A`. For floats this is
   a no-op; for integers it centres each component in $(-N/2, N/2]$.
2. **Build the matrix** — maps left-multiplication by `A` to a square matrix
   over the sub-algebra spanned by `A`.
3. **Gauss elimination** — whenever a pivot must be divided out, `InvMap` is
   called to obtain $1/\text{pivot}$ (float) or $\text{pivot}^{-1} \bmod N$
   (integer). If `InvMap` returns `false` the matrix is singular in this ring
   and `EResult::NotInvertible` is returned.
4. **Back-substitution** — same `InvMap` calls for the upper-triangular phase.

### Floating-point example

```cpp
#include "Tan.GA/DynamicMultivector.h"
#include "Tan.GA/Algo.h"
#include "Tan.Math/Congruence.h"

using namespace Tan;
using TBlade = GA::CBlade<3, 0>::TBlade;
using TMV    = GA::CDynamicMultivector<double, TBlade>;
using TE     = GA::SValueBlade<double, TBlade>;

TMV wA;
wA << TE(3.0, 0b001) << TE(1.0, 0b010) << TE(-1.0, 0b100); // e1 + e2 terms

CCongruence_Float<double> xCongruence;
TMV wInv;

if (GA::Inverse(wInv, wA, xCongruence) == GA::EResult::Success)
{
    // wA * wInv == 1 (scalar)
}
```

### Modular integer example

```cpp
#include "Tan.GA/DynamicMultivector.h"
#include "Tan.GA/Algo.h"
#include "Tan.Math/Congruence.h"

using namespace Tan;
using TBlade = GA::CBlade<3, 0>::TBlade;
using TMV    = GA::CDynamicMultivector<int64_t, TBlade>;
using TE     = GA::SValueBlade<int64_t, TBlade>;

const int64_t tMod = 97;   // prime modulus
CCongruence_HMod<int64_t> xCongruence(tMod);

TMV wA;
wA << TE(3, 0b001) << TE(14, 0b010) << TE(-5, 0b100);

TMV wInv;
GA::EResult eRes = GA::Inverse(wInv, wA, xCongruence);

if (eRes == GA::EResult::Success)
{
    // wA * wInv ≡ 1  (mod 97)
    // All coefficients of wInv lie in [-(97/2), 97/2]
}
```

---

## Congruence in geometric products: `GP_Congruence`

For products that must stay within a modular ring, use `GA::GP_Congruence`
instead of `GA::GP`. It runs the geometric product then applies `Map` to every
component of the result:

```cpp
// wC = (wA * wB) mod N  — all coefficients reduced by hmod
GA::GP_Congruence(wC, wA, wB, xCongruence);
```

Without this call the intermediate products can overflow or drift outside the
intended residue class.

---

## Choosing a modulus

| Requirement | Guidance |
|-------------|----------|
| Every pivot is invertible | Use a **prime** modulus |
| Smallest useful modulus | $N > 2$ (so $-1 \not\equiv 1$) |
| Overflow safety for `int64_t` | Intermediates of size $N^2 \cdot k$ (where $k$ is blade count) must fit; use $N < 2^{20}$ for large algebras |
| SVD / least-squares | Not available — SVD requires floating-point division. Use `CCongruence_Float` and a floating-point value type instead |

---

## Return codes from `GA::Inverse`

| Code | Meaning |
|------|---------|
| `EResult::Success` | Inverse computed successfully |
| `EResult::NotInvertible` | Matrix is singular — `A` has no inverse in this ring |
| `EResult::InvalidComponentCongruence` | `Map` returned `false` for some component |
| `EResult::InvalidComponentInverseCongruence` | `InvMap` returned `false` for a pivot — pivot is not invertible mod N |
