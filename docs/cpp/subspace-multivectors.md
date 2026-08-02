# Subspace Multivectors — E3, P3, N3

A subspace multivector stores coefficients for a **fixed, known set of blades**
only. This is useful when:

- you know at compile time which blades are non-zero (rotors, translators, …),
- you want compact array storage without a hash map, and
- you need deterministic layout for matrix conversion.

The trade-off is that the blade set is chosen once at construction and cannot
grow at runtime.

---

## Template Parameters

```cpp
CSubspaceMultivectorE3<TValue, N>   // E3 — 8 blades total
CSubspaceMultivectorP3<TValue, N>   // P3 — 16 blades total
CSubspaceMultivectorN3<TValue, N>   // N3 — 32 blades total
```

`N` is the number of blades in the subspace. It must be a compile-time constant.

Internally the type stores two fixed-length arrays: one for blade ids
(`TBlade[N]`) and one for coefficients (`TValue[N]`).

---

## Required Headers

```cpp
#include "Tan.GA/SubspaceMultivectorE3.h"
#include "Tan.GA/SubspaceMultivectorP3.h"
#include "Tan.GA/SubspaceMultivectorN3.h"
#include "Tan.GA/MV_Operators.h"
#include "Tan.GA/String.h"
```

---

## E3 Examples

### A pure vector (grade-1 subspace, 3 blades)

```cpp
using namespace Tan;
using TValue  = double;
using TBlade  = GA::CBlade<3, 0>::TBlade;
using TVector = GA::CSubspaceMultivectorE3<TValue, 3>;

// blade ids: e1=1, e2=2, e3=4
TValue   vals[]   = { 1.0, 2.0, 3.0 };
TBlade   blades[] = { TBlade(1), TBlade(2), TBlade(4) };
TVector  wV(vals, blades);

printf("v = %s\n", GA::ToString(wV).c_str());
// Output: v = E1 + 2*E2 + 3*E3
```

### A rotor (even sub-algebra, 4 blades: scalar + e12 + e13 + e23)

```cpp
using TRotor = GA::CSubspaceMultivectorE3<double, 4>;

double angle = M_PI / 4.0;   // 45° rotation in e1∧e2 plane

// scalar=0, e12=3, e13=5, e23=6
TValue  rVals[]   = { std::cos(angle/2), std::sin(angle/2), 0.0, 0.0 };
TBlade  rBlades[] = { TBlade(0), TBlade(3), TBlade(5), TBlade(6) };
TRotor  wR(rVals, rBlades);
```

### Using the subspace multivector in products

Subspace multivectors are fully compatible with all product functions and
with the full multivector types. The result type must be large enough to
hold all possible output blades:

```cpp
using TFullMV = GA::CMultivectorE3<double>;
TFullMV wC;

// Rotate wV by wR  (sandwich product)
TFullMV wRv;
GA::GP(wRv, wR, wV);
GA::GP_Reverse(wC, wRv, false, wR, true);  // wC = R * v * ~R

printf("R*v*~R = %s\n", GA::ToString(wC).c_str());
```

---

## P3 Examples

### A homogeneous plane (grade-3, 4 blades)

In P3, a plane through the origin normal to `(a, b, c)` is represented by a
trivector. Four basis trivectors exist.

```cpp
using namespace Tan;
using TValue  = double;
using TBlade  = GA::CBlade<4, 0>::TBlade;
using TPlane  = GA::CSubspaceMultivectorP3<TValue, 4>;

// trivector blade ids in 4D: e123=7, e124=11, e134=13, e234=14
TValue  pVals[]   = { 0.0, 0.0, 1.0, 0.0 };  // plane normal in z direction
TBlade  pBlades[] = { TBlade(7), TBlade(11), TBlade(13), TBlade(14) };
TPlane  wPlane(pVals, pBlades);
```

---

## N3 Examples

### A point in conformal space (grade-1, 5 blades)

```cpp
using namespace Tan;
using TValue  = double;
using TBlade  = GA::CBlade<5, 16>::TBlade;   // N3 signature = 0b10000 = 16
using TPoint  = GA::CSubspaceMultivectorN3<TValue, 5>;

double x = 1, y = 2, z = 0;

// In N3 the 5 grade-1 blades are e1=1, e2=2, e3=4, ei=8, eo=16
TValue  ptVals[]   = { x, y, z, 0.5*(x*x+y*y+z*z), 1.0 };
TBlade  ptBlades[] = { TBlade(1), TBlade(2), TBlade(4), TBlade(8), TBlade(16) };
TPoint  wPt(ptVals, ptBlades);
```

### A translator (4 blades: scalar + 3 null-plane bivectors)

```cpp
using TTranslator = GA::CSubspaceMultivectorN3<double, 4>;

// T = 1 + 0.5*(tx*e1i + ty*e2i + tz*e3i)
// e1i = e1^ei = blade(1|8)=9, e2i=10, e3i=12
double tx = 1.0, ty = 0.0, tz = 0.0;

TValue  tVals[]   = { 1.0, 0.5*tx, 0.5*ty, 0.5*tz };
TBlade  tBlades[] = { TBlade(0), TBlade(9), TBlade(10), TBlade(12) };
TTranslator wT(tVals, tBlades);
```

---

## Converting Between Subspace and Full Multivectors

Assignment between subspace and full multivectors is supported directly:

```cpp
// Subspace → full
GA::CMultivectorE3<double> wFull = wR;

// Full → subspace (only the declared blades are copied; others are ignored)
TRotor wR2 = wFull;
```
