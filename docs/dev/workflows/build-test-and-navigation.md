# Build, Test, And Navigation

## Build Shape

The top-level `CMakeLists.txt` builds four subprojects:

- `Tan.Core`
- `Tan.Math`
- `Tan.GA`
- `Tan.App.Test`

The project sets C++17 globally.

`Tan.App.Test/CMakeLists.txt` currently wires these executable entry points:

- `Test_Math_01`
- `Test_Basics_01`
- `Test_Crypt_03`
- `Test_Crypt_04`

## Typical Local Build

From the repository root:

```powershell
cmake -S . -B build
cmake --build build --config Release
```

On non-MSVC toolchains the test targets enable SSE4.1 and `popcnt`.

## Where To Start For Common Tasks

### Change a blade-level algebra rule

Open these first:

- `source/Tan.GA/Blade.h`
- `source/Tan.GA/Blade_Operators.h`

### Change multivector traversal or accumulation

Open these first:

- `source/Tan.GA/MV_Operators.h`
- `source/Tan.GA/DynamicMultivector.h`

### Change inversion behavior

Open these first:

- `source/Tan.GA/Algo.h`
- `source/Tan.GA/Matrix_MapToBladeMask.h`
- `source/Tan.Math/Matrix.Algo.GE.h`

### Change modular arithmetic behavior

Open these first:

- `source/Tan.Math/Congruence.h`
- `source/Tan.Math/InlineMath.h`

### Change the cryptographic experiments

Open these first:

- `source/Tan.App.Test/Test_Crypt_03.cpp`
- `source/Tan.App.Test/Test_Crypt_04.cpp`
- `source/Tan.App.Test/Test_Crypt_Func.h`

Do not start in `Tan.Crypt/AsymGeo1.*` unless you are explicitly moving the prototype into a reusable API.

## Validation Strategy

Use the smallest executable that covers the change.

- GA arithmetic changes: start with `Test_Basics_01`.
- matrix or inversion changes: start with `Test_Math_01` and then the relevant crypt test.
- NTRU experiment changes: start with `Test_Crypt_03`.
- integrity extension changes: start with `Test_Crypt_04`.

## Architectural Caution

Many cryptography assumptions depend on coefficient magnitudes staying inside centered modular windows. A change that looks algebraically harmless can still break decryption by increasing coefficient growth.