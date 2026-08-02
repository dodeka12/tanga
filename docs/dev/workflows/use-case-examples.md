# Use-Case Examples

## Example 1: Trace A Geometric Product Bug

Symptom:
An output multivector contains the wrong sign or the wrong blade after `GP(...)`.

Trace:

1. Reproduce with a small basis in `Test_Basics_01.cpp`.
2. Confirm which input blades are actually present after pruning.
3. Step through `GA::GP(...)` in `MV_Operators.h`.
4. Step into `GA::GPSign(...)` in `Blade_Operators.h`.
5. Check whether the metric signature or permutation count caused the unexpected sign.

Why this works:
Traversal bugs and blade-sign bugs live in different files.
Splitting them early saves time.

## Example 2: Add A New High-Level Algebra Experiment

Goal:
Prototype a new operation on sparse multivectors without committing to a library API.

Recommended path:

1. Add an executable in `source/Tan.App.Test/CMakeLists.txt`.
2. Use `CDynamicMultivector<TValue, TBlade>` as the first representation.
3. Reuse `GenRanMV(...)`, `EvalNextHigherPrime(...)`, and the print helpers from `Test_Crypt_Func.h` if modular arithmetic is involved.
4. Only move the code into `Tan.GA` or `Tan.Crypt` after the algebra and data flow stabilize.

This matches the existing repository style: experiments land in test applications first.

## Example 3: Port The Cryptography Prototype Into `Tan.Crypt`

Goal:
Turn the current research code into a reusable component.

Suggested decomposition:

1. Move parameter selection and validation into a dedicated config type.
2. Move key-generation logic from `Test_Crypt_03.cpp` into `CAsymGeo1::CreateKeyPair(...)`.
3. Define explicit `Encrypt(...)` and `Decrypt(...)` functions using the `SPublicKey` and `SPrivateKey` structs.
4. Keep a separate executable example that verifies round-trip behavior and failure cases.

Important constraint:
The public and private key structs currently use plain arrays of blade ids and values. That is serialization-friendly, but it means the runtime GA types need conversion layers.

## Example 4: Investigate An Inversion Failure

Symptom:
`GA::Inverse(...)` returns `NotInvertible` for a multivector you expected to work.

Checklist:

1. Check whether the input became zero after congruence mapping.
2. Inspect the blade mask produced for the source multivector.
3. Inspect the closure mask produced by repeated geometric products.
4. Check whether Gaussian elimination failed due to singularity or missing modular inverse.
5. Verify the modulus is compatible with the coefficients you generated.

The common failure modes in this repository are algebraic singularity and modular non-invertibility, not generic container bugs.

## Example 5: Understand The NTRU Mapping Quickly

If you already know standard NTRU, read `Test_Crypt_03.cpp` as a translation exercise:

- polynomial ring element -> sparse multivector,
- convolution product -> geometric product,
- coefficient reduction mod `p` or `q` -> `CCongruence_HMod`,
- inverse modulo the ring -> matrix-solved multivector inverse.

That mental mapping makes the cryptography examples much easier to follow than reading them as entirely new schemes.