# Type System And Storage Model

## Blade Encoding

`GA::CBlade<Dimension, Signature>` is the foundational type.

Its two template parameters fix the algebra at compile time:

- `Dimension`: vector-space dimension.
- `Signature`: bit mask describing which basis vectors square to `-1`.

At runtime, a blade is just a `uint32_t` bit pattern.

Examples:

- bit `0b00001` means basis vector `e0`
- bit `0b00101` means blade `e0 ^ e2`
- the pseudoscalar is `2^Dimension - 1`

This gives three important properties:

- grade is the number of set bits,
- blade multiplication can be reduced to xor plus sign bookkeeping,
- the algebra is capped at 32 basis vectors because the blade id fits into 32 bits.

## Why High Dimensions Are Feasible

The expensive part of a geometric algebra is not naming blades, it is storing coefficients for all of them.

TanGA avoids dense storage in two ways.

### Sparse Dynamic Multivectors

`GA::CDynamicMultivector<TValue, TBlade>` stores blade coefficients in `std::map<TBlade, TValue>`.

Implications:

- only non-zero blades consume memory,
- product loops scale with populated blades rather than full algebra dimension,
- pruning removes near-zero or zero terms after arithmetic.

This is the workhorse representation for cryptography experiments because those examples generate random but still sparse multivectors.

### Restricted Subspace Multivectors

`GA::_CSubspaceMultivector<TValue, TBlade, SubspaceDimension>` stores a fixed list of blades plus a fixed number of coefficients.

Use this when:

- you know the object lives in a particular subspace,
- you want compact storage without a map,
- you want deterministic layout for matrix conversion or basis work.

## Blade Masks

`GA::CBladeMask<TBlade>` is a compact set of blade ids.

It is used to answer questions such as:

- which blades are present in a multivector,
- which blades can appear after repeated products,
- which minimal sub-algebra must be considered when building an inverse.

This is a key optimization. The inversion code does not solve over the whole algebra unless it has to.

## Value Domains

The algebra engine is generic over value type, but the repository uses two broad domains:

- floating-point values with precision tolerance,
- signed integers with modular congruence mapping.

The congruence abstraction in `Tan.Math/Congruence.h` is what lets the same operator templates serve both geometric computations and cryptographic modular arithmetic.

## Architectural Constraint To Keep In Mind

The compile-time algebra shape and the runtime multivector sparsity are separate concerns.

Changing dimension or signature changes the type system.
Changing the number of active blades changes only runtime state.

That split is the reason the codebase can be both template-heavy and still usable for exploratory algorithms.