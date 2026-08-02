# TanGA User Documentation

This section describes the public C++ API for working with multivectors,
products, and matrix-based equation solving.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Fixed-space multivectors (E3, P3, N3)](multivectors-e3-p3-n3.md) | How to construct and work with the fully dense multivector types for 3D Euclidean, projective, and conformal spaces |
| [Subspace multivectors (E3, P3, N3)](subspace-multivectors.md) | How to restrict a multivector to a known blade subset for compact, deterministic storage |
| [Dynamic multivectors](dynamic-multivectors.md) | How to use sparse multivectors for any algebra dimension and signature |
| [Matrix mapping and equation solving](matrix-mapping-and-equations.md) | How to convert multivector products into a matrix equation and solve it with Gaussian elimination |
| [Product matrices — API and math](product-matrices.md) | The tensor-contraction view of GA products, how partial contraction yields a product matrix, blade-mask subspace restriction, and a complete API reference for `Matrix_MapToBladeMask.h` |
| [Congruence maps](congruence.md) | What congruence is, how it enables `GA::Inverse` for floats, and how the same inverse extends to integer multivectors via modular arithmetic |

## Common Headers

```cpp
// Specific-space full multivectors
#include "Tan.GA/MultivectorE3.h"      // CMultivectorE3<T>
#include "Tan.GA/MultivectorP3.h"      // CMultivectorP3<T>
#include "Tan.GA/MultivectorN3.h"      // CMultivectorN3<T>

// Specific-space subspace multivectors
#include "Tan.GA/SubspaceMultivectorE3.h"   // CSubspaceMultivectorE3<T, N>
#include "Tan.GA/SubspaceMultivectorP3.h"   // CSubspaceMultivectorP3<T, N>
#include "Tan.GA/SubspaceMultivectorN3.h"   // CSubspaceMultivectorN3<T, N>

// Generic sparse multivector for any algebra
#include "Tan.GA/DynamicMultivector.h"      // CDynamicMultivector<T, TBlade>

// Products (GP, IP, OP) — included transitively by all multivector headers
#include "Tan.GA/MV_Operators.h"

// Inversion via Gaussian elimination
#include "Tan.GA/Algo.h"

// Matrix representation of products
#include "Tan.GA/Matrix_MapToBladeMask.h"

// String conversion for printing
#include "Tan.GA/String.h"

// Congruence maps (floating-point or modular)
#include "Tan.Math/Congruence.h"
```

All multivector headers include a `source/` prefix because the build system adds
`source/` to the include path:

```cmake
include_directories(PUBLIC ${CMAKE_SOURCE_DIR}/source)
```
