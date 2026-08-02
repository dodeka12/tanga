# GA Operation Pipeline

## The Core Product Path

For most developer work, the critical call chain is:

1. `GA::GP`, `GA::IP`, or `GA::OP` in `MV_Operators.h`
2. `Product(...)` template in `MV_Operators.h`
3. `ProductInnerLoop_*`
4. `ProductOperator(...)`
5. blade-level operator in `Blade_Operators.h`
6. target multivector accumulation via `AddValueBlade(...)`

That split is deliberate.

- `MV_Operators.h` decides traversal and accumulation.
- `Blade_Operators.h` decides the algebraic meaning of one blade-blade product.
- the multivector type decides storage.

## Bit-Level Geometric Product

`GPSign(...)` is the heart of the implementation.

It does three things:

1. compute the resulting blade id with xor,
2. compute sign changes from basis-vector swaps,
3. apply extra sign flips caused by the metric signature.

This means the expensive algebraic reasoning is reduced to cheap bit arithmetic.

## Congruence-Aware Product

`GP_Congruence(...)` fuses product and modular reduction.

That matters for the cryptography examples because it:

- keeps coefficients in the expected centered interval,
- reduces risk of drifting outside modulus assumptions,
- avoids a second full traversal when product and reduction always occur together.

## Involution Handling

`Product(...)` also supports reverse and conjugation via flags and callback hooks.

That design avoids copy-pasting traversal code for:

- ordinary products,
- reversed products,
- conjugated products.

Instead, the traversal is generic and only the sign behavior changes.

## Inversion Flow

`GA::Inverse(...)` in `Algo.h` is the main higher-order algorithm.

It works as follows:

1. apply congruence to the input multivector,
2. compute the blade mask of the smallest product-closed sub-algebra containing the input,
3. build the product matrix for left multiplication by that multivector,
4. map the scalar unit into the same matrix space,
5. solve the linear system with Gaussian elimination,
6. map the solution back into a multivector.

This is the most important architectural bridge between Tan.GA and Tan.Math.

## Where To Debug Specific Failures

If the wrong blade appears:

- start in `Blade_Operators.h`

If the right blades appear with wrong coefficients:

- inspect `Blade_Operators.h` and `DynamicMultivector.h`

If modular products behave oddly:

- inspect `Congruence.h`, `InlineMath.h`, and `GP_Congruence(...)`

If inversion fails for a multivector that should be invertible:

- inspect `Algo.h`, `Matrix_MapToBladeMask.h`, and `Tan.Math/Matrix.Algo.GE.h`