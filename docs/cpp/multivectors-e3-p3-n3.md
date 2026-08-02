# Fixed-Space Multivectors — E3, P3, N3

TanGA provides three fixed-space multivector types. Each stores a dense
coefficient array covering the entire algebra of that space.

| Type | Space | Dimension | Blades | Typical use |
|------|-------|-----------|--------|-------------|
| `CMultivectorE3<T>` | 3D Euclidean | 3 | 8 | rotors, reflections, vectors |
| `CMultivectorP3<T>` | 3D Projective | 4 | 16 | homogeneous points, lines, planes |
| `CMultivectorN3<T>` | Conformal (CGA) | 5 | 32 | spheres, circles, translations, motors |

---

## E3 — 3D Euclidean Space

### Algebra structure

Signature `(3, 0, 0)`: all three basis vectors square to `+1`.

| Blade constant | Bit pattern | Grade | Meaning |
|----------------|-------------|-------|---------|
| `uSc = 0` | `000` | 0 | scalar |
| `uE1 = 1` | `001` | 1 | basis vector e₁ |
| `uE2 = 2` | `010` | 1 | basis vector e₂ |
| `uE3 = 4` | `100` | 1 | basis vector e₃ |
| `3` | `011` | 2 | bivector e₁∧e₂ |
| `5` | `101` | 2 | bivector e₁∧e₃ |
| `6` | `110` | 2 | bivector e₂∧e₃ |
| `uPs = 7` | `111` | 3 | pseudoscalar e₁∧e₂∧e₃ |

### Required headers

```cpp
#include "Tan.GA/MultivectorE3.h"
#include "Tan.GA/MV_Operators.h"
#include "Tan.GA/String.h"
```

### Constructing a multivector

```cpp
using namespace Tan;
using TValue = double;
using TMV    = GA::CMultivectorE3<TValue>;

// 1. Default (zero multivector)
TMV wZero;

// 2. From parallel value / blade-id arrays
//    Set coefficients for e1 and e2 only
TValue  vals[]   = { 3.0, -1.0 };
unsigned blades[] = { TMV::uE1, TMV::uE2 };
TMV wV(vals, blades);      // wV = 3*e1 - e2

// 3. From a full 8-element dense array (blade order = bit-pattern order)
TValue all[8] = { 1, 0, 0, 0, 0, 0, 0, 0 };   // scalar = 1
TMV wSc(all);
```

### Arithmetic

```cpp
TMV wA(valsA, bladesA);
TMV wB(valsB, bladesB);
TMV wC;

// Geometric product  wC = wA * wB
GA::GP(wC, wA, wB);

// Outer (wedge) product  wC = wA ^ wB
GA::OP(wC, wA, wB);

// Inner product  wC = wA · wB
GA::IP(wC, wA, wB);

// Scalar multiply / add / subtract via operators
TMV wD = wA * 2.0;
TMV wE = wA + wB;
TMV wF = wA - wB;
```

### Printing

```cpp
printf("wA = %s\n", GA::ToString(wA).c_str());
// Output example:  wA = 3*E1 - E2
```

### Rotor example

A rotor `R` representing a 45° rotation in the e₁∧e₂ plane:

```cpp
// R = cos(π/8) + sin(π/8)*e12
// Blade id for e12 = 3 (bits 0b011)
double angle = M_PI / 4.0;   // rotation angle
TValue rVals[]    = { std::cos(angle / 2.0), std::sin(angle / 2.0) };
unsigned rBlades[] = { TMV::uSc, 3u };   // scalar + e12

TMV wR(rVals, rBlades);

// Rotate a vector v using the sandwich product R * v * R~
// (R~ = reverse of R; reverse negates grade-2 and grade-3 parts)
TMV wV2, wRv, wResult;
GA::GP(wRv, wR, wV);          // wRv   = R * v
GA::GP_Reverse(wResult, wRv, false, wR, true);  // wResult = wRv * ~R
```

---

## P3 — 3D Projective Space

### Algebra structure

Signature `(4, 0, 0)`: four basis vectors all squaring to `+1`.  The
extra dimension (`e4` or `e0`) acts as the homogeneous coordinate.

16 blades (grades 0–4). Common named blades defined in `CBasisP3`:

| Named element | Meaning |
|---------------|---------|
| `uE1`, `uE2`, `uE3` | Euclidean basis vectors |
| `uE0` (or `uE4`) | Homogeneous basis vector |
| Line blades | Bivectors (grade 2) |
| Plane blades | Trivectors (grade 3) |
| `uPs` | Pseudoscalar (grade 4) |

### Required headers

```cpp
#include "Tan.GA/MultivectorP3.h"
#include "Tan.GA/MV_Operators.h"
#include "Tan.GA/String.h"
```

### Constructing a homogeneous point

```cpp
using namespace Tan;
using TValue = double;
using TMV    = GA::CMultivectorP3<TValue>;

// Point at (x, y, z) in P3: p = x*e1 + y*e2 + z*e3 + e0
// Blade ids for e1=1, e2=2, e3=4, e0=8  (4-bit patterns)
TValue  pVals[]   = { 1.0, 2.0, 3.0, 1.0 };
unsigned pBlades[] = { TMV::uE1, TMV::uE2, TMV::uE3, TMV::uE0 };
TMV wP(pVals, pBlades);

printf("P = %s\n", GA::ToString(wP).c_str());
```

### Joining two points to form a line

```cpp
TMV wP1(p1Vals, p1Blades);
TMV wP2(p2Vals, p2Blades);
TMV wLine;
GA::OP(wLine, wP1, wP2);     // line = p1 ^ p2
```

### Joining a line and a point to form a plane

```cpp
TMV wPlane;
GA::OP(wPlane, wLine, wP3);  // plane = line ^ p3
```

---

## N3 — Conformal 3D Space (CGA)

### Algebra structure

Signature `(4, 1, 0)`: basis vectors `e1`, `e2`, `e3` square to `+1`;
the null basis `eo` (origin) and `ei` (point at infinity) are formed
from `e+` and `e-` where `e+² = +1` and `e-² = -1`.

32 blades (grades 0–5). The `CBasisN3` class exposes named element types:

| Named subspace | Grade | Meaning |
|----------------|-------|---------|
| Point | 1 | conformal point |
| PointPair | 2 | pair of two points |
| Circle | 3 | circle or line |
| Sphere | 4 | sphere or plane |
| Rotor | even | Euclidean rotation |
| Translator | even | pure translation |
| Motor | even | rotation + translation |
| Dilator | even | uniform scaling |

### Required headers

```cpp
#include "Tan.GA/MultivectorN3.h"
#include "Tan.GA/MV_Operators.h"
#include "Tan.GA/String.h"
```

### Embedding a Euclidean point

A Euclidean point `(x, y, z)` is lifted to a conformal point:

$$p = x\,e_1 + y\,e_2 + z\,e_3 + \tfrac{1}{2}(x^2+y^2+z^2)\,e_i + e_o$$

```cpp
using namespace Tan;
using TValue = double;
using TMV    = GA::CMultivectorN3<TValue>;

double x = 1, y = 0, z = 0;

// Blade ids in 5D: e1=1, e2=2, e3=4, e4(=ei)=8, e5(=eo)=16
// (exact bit patterns depend on how CBasisN3 orders eo/ei —
//  use the CBasisN3 constants to stay portable)
TValue  pVals[]   = { x, y, z, 0.5*(x*x+y*y+z*z), 1.0 };
unsigned pBlades[] = { TMV::uE1, TMV::uE2, TMV::uE3, TMV::uEi, TMV::uEo };
TMV wP(pVals, pBlades);
```

### Constructing a sphere from four points

```cpp
TMV wS;
// sphere = p1 ^ p2 ^ p3 ^ p4
TMV wTmp;
GA::OP(wTmp, wP1, wP2);
GA::OP(wTmp, wTmp, wP3);
GA::OP(wS,   wTmp, wP4);
```

### Applying a motor (rigid body motion)

A motor `M` encodes a combined rotation and translation. Apply it to a
geometric object `X` using the sandwich product:

```cpp
TMV wMX, wResult;
GA::GP(wMX, wM, wX);
GA::GP_Reverse(wResult, wMX, false, wM, true);  // result = M * X * ~M
```
