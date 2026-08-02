# Dynamic Multivectors

`CDynamicMultivector<TValue, TBlade>` is the workhorse representation for
high-dimensional and exploratory work. It stores only the **non-zero blade
coefficients** in a `std::map`, so memory and computation scale with the
number of populated blades rather than the full algebra dimension (2ⁿ).

---

## Template Parameters

```cpp
template<typename TValue, typename TBlade>
class CDynamicMultivector;
```

| Parameter | What it controls |
|-----------|-----------------|
| `TValue` | Coefficient type: `double`, `float`, `int64_t`, … |
| `TBlade` | Algebra shape via `CBlade<Dim, Sig>` (see below) |

### Defining the algebra with `CBlade`

```cpp
#include "Tan.GA/Blade.h"

// CBlade<VectorSpaceDimension, VectorSpaceSignature>
// Signature is a bitmask: bit k = 1 means basis vector eₖ squares to -1

// 3D Euclidean (all positive)
using TBlade3 = GA::CBlade<3, 0>::TBlade;       // 8 blades

// 4D Projective
using TBlade4 = GA::CBlade<4, 0>::TBlade;       // 16 blades

// 5D Conformal (e5 squares to -1, bit 4 set → signature = 0b10000 = 16)
using TBlade5 = GA::CBlade<5, 16>::TBlade;      // 32 blades

// Generic 10D (for crypto / ring experiments)
using TBlade10 = GA::CBlade<10, 0>::TBlade;     // 1024 blades
```

---

## Required Headers

```cpp
#include "Tan.GA/DynamicMultivector.h"
#include "Tan.GA/MV_Operators.h"
#include "Tan.GA/Algo.h"         // for Inverse
#include "Tan.GA/String.h"       // for ToString
#include "Tan.Math/Congruence.h" // for CCongruence_Float / CCongruence_HMod
```

---

## Construction and Population

```cpp
using namespace Tan;

using TBlade = GA::CBlade<5, 0>::TBlade;
using TValue = double;
using TMV    = GA::CDynamicMultivector<TValue, TBlade>;

// 1. Default (zero, no storage allocated)
TMV wA;

// 2. Add individual blades
//    Blade ids are uint32_t bit patterns: e1=1, e2=2, e1∧e2=3, …
wA.AddValueBlade(2.0, 1u);   // 2*e1
wA.AddValueBlade(3.0, 2u);   // 3*e2
// identical blade ids are accumulated: AddValueBlade(x, id) adds x to existing coefficient

// 3. Zero and repopulate
wA.Zero();

// 4. Remove near-zero coefficients (uses ValuePrecision tolerance)
wA.Prune();
```

---

## Useful Introspection

```cpp
// Number of stored (non-zero after Prune) blades
unsigned n = wA.GetBladeCount();

// Retrieve the coefficient for a specific blade id
TValue coeff;
bool found = wA.GetValueBlade(coeff, TBlade(3u));  // e12

// Iterate over all stored blades
wA.ForEachBlade([](const TValue& val, const TBlade& blade) {
    printf("blade %u: %g\n", blade.GetId(), val);
    return true;  // return false to stop early
});

// Check whether wA and wB are equal within precision
bool eq = GA::IsZero(wA - wB);
```

---

## Products

All products write into the first argument (result). The operands can be
any combination of multivector types (dynamic, fixed, subspace).

```cpp
TMV wB, wC;

// Geometric product  C = A * B
GA::GP(wC, wA, wB);

// Outer (wedge) product  C = A ^ B
GA::OP(wC, wA, wB);

// Inner product  C = A · B
GA::IP(wC, wA, wB);

// Geometric product with modular reduction of each coefficient
Tan::CCongruence_HMod<int64_t> xMod(97);
GA::GP_Congruence(wC, wA, wB, xMod);
```

---

## Congruence Maps

A congruence object controls how coefficients are mapped after each
arithmetic operation. Two built-in classes are available.

### `CCongruence_Float<T>` — floating-point (identity)

```cpp
Tan::CCongruence_Float<double> xCongruence;
// Map(x)    = x   (identity)
// InvMap(x) = 1/x (reciprocal for inverse)
```

### `CCongruence_HMod<T>` — centred modular arithmetic

```cpp
// All coefficients are reduced to the range (-mod/2, mod/2]
Tan::CCongruence_HMod<int64_t> xMod(97);

// Reduce a full multivector in-place
GA::Congruence(wA, xMod);    // wA coefficients → (-49, 48]

// Product with immediate reduction
GA::GP_Congruence(wC, wA, wB, xMod);
```

---

## Inversion

`GA::Inverse` solves `wA * wInv = scalar_identity` using Gaussian
elimination on a matrix derived from left-multiplication by `wA`.

```cpp
Tan::CCongruence_Float<double> xCongruence;
TMV wInv;

GA::EResult eRes = GA::Inverse(wInv, wA, xCongruence);

if (eRes == GA::EResult::Success)
{
    // Verify:  A * A^{-1} ≈ scalar 1
    TMV wTest;
    GA::GP(wTest, wA, wInv);
    wTest.Prune();
    printf("A * A^{-1} = %s\n", GA::ToString(wTest).c_str());
}
else
{
    printf("wA is not invertible in this algebra.\n");
}
```

For integer coefficient rings, use `CCongruence_HMod`:

```cpp
Tan::CCongruence_HMod<int64_t> xMod(97);
TMV wInvMod;
GA::EResult eRes = GA::Inverse(wInvMod, wA, xMod);
// wInvMod satisfies  (wA * wInvMod) ≡ 1  (mod 97)
```

---

## Scalar Multiply and Linear Arithmetic

```cpp
// Scale
TMV wScaled = wA * TValue(3);

// Add / subtract (coefficient-wise, matching blades)
TMV wSum  = wA + wB;
TMV wDiff = wA - wB;

// Negate
TMV wNeg = wA * TValue(-1);
```

---

## Example: 10-Dimensional Algebra

```cpp
using TBlade10 = GA::CBlade<10, 0>::TBlade;
using TValue   = int64_t;
using TMV10    = GA::CDynamicMultivector<TValue, TBlade10>;

// AlgebraDimension = 2^10 = 1024 possible blades
// But only populated ones consume memory
static_assert(TMV10::AlgebraDimension == 1024);

TMV10 wA, wB, wC;

// Add a handful of blades
wA.AddValueBlade(1, 1u);    // e1
wA.AddValueBlade(2, 4u);    // e3
wA.AddValueBlade(-1, 16u);  // e5

wB.AddValueBlade(3, 2u);    // e2
wB.AddValueBlade(1, 8u);    // e4

GA::GP(wC, wA, wB);
wC.Prune();
printf("A*B = %s\n", GA::ToString(wC).c_str());
// Only the few resulting blades are stored, not all 1024
```
