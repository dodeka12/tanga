# System Overview

## Module Graph

The repository is layered in one direction:

`Tan.Core -> Tan.Math -> Tan.GA -> Tan.App.Test`

`Tan.Crypt` currently contains type shells for asymmetric-key material, but the executable cryptographic workflows are demonstrated in `Tan.App.Test`.

## Module Responsibilities

### Tan.Core

Low-level utilities shared everywhere else:

- `Array.h`: generic array container utilities.
- `Defines.h`: assertions, exceptions, overflow helpers, static assertions.
- `IntrinsicFunctions.h`: bit counting and overflow-adjacent helpers used by blade arithmetic.
- `StdAlgo.h`, `StrideIterator.h`, `ValueFormatString.*`: support code.

This layer matters because blade products and mask operations depend on predictable bit operations and overflow checks.

### Tan.Math

Numeric infrastructure used by GA and cryptography:

- `Matrix.h` and `Matrix.Algo.GE.h`: matrix storage and Gaussian elimination.
- `Congruence.h`: pluggable value-domain mappings, especially `CCongruence_HMod` for centered modular arithmetic.
- `ValuePrecision.*`: tolerance-aware comparisons and pruning.
- `FixedVector*` and `FixedGeoTypes.h`: support types for lower-dimensional geometry and examples.

This layer is what turns multivector inversion into a solvable linear system.

### Tan.GA

The main engine.

Key concepts:

- `Blade.h`: compile-time algebra metadata plus runtime blade id.
- `Blade_Operators.h`: sign logic for geometric, inner, and outer products.
- `DynamicMultivector.h`: sparse multivector representation using `std::map`.
- `Multivector.h` and `SubspaceMultivector.h`: denser or restricted representations for known subspaces.
- `BladeMask.h` and `Matrix_MapToBladeMask.h`: track which blades are present and map multivectors to matrices.
- `Algo.h`: inversion by matrix construction and Gaussian elimination.
- `Basis*.h`: basis-specialized convenience types for common signatures.

### Tan.Crypt

At present this is mostly a design placeholder:

- `AsymGeo1.h`: public/private key structs and a `CreateKeyPair` declaration.
- `AsymGeo1.cpp`: constructor and destructor only.

That is an important architectural fact: the cryptographic experiments are not yet encapsulated as a reusable library API.

### Tan.App.Test

This folder is more than tests. It is also the experimental notebook for the project.

- `Test_Basics_*`, `Test_Matrix_*`, `Test_ModMVRing.cpp`: algebra and numeric experiments.
- `Test_Crypt_03.cpp`: base NTRU-style public-key workflow expressed in geometric algebra.
- `Test_Crypt_04.cpp`: a custom extension that adds a consistency check during recovery.
- `Test_Crypt_Func.*`: helper generation, printing, and modulus selection utilities.

## Execution Model

Most important operations follow this pattern:

1. A blade is represented as a bitset in a `uint32_t`.
2. A multivector stores only non-zero blade coefficients.
3. A product loops only over present blades, not over all algebra elements.
4. Sign and resulting blade id are computed from bit operations.
5. Optional congruence mapping keeps integer coefficients in a modular domain.
6. When an inverse is needed, the relevant sub-algebra is detected, mapped into a matrix problem, and solved numerically or modularly.

## Practical Design Consequence

The library can describe algebras whose full dense dimension is `2^n` up to `n = 32`, but it remains practical only because most runtime objects are sparse or subspace-restricted. The design assumes you work with structured multivectors, not fully dense `2^32` coefficient arrays.