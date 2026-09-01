# TanGA Developer Documentation

This documentation is intentionally architecture-first.
It is meant to help a developer answer questions such as:

- Where is a geometric algebra product actually computed?
- Why can this library work with algebras up to 32 vector-space dimensions without storing dense multivectors?
- How do the cryptography examples map standard NTRU ideas into geometric algebra?
- Which files should I open first for a specific change?

The docs are organized by decision-making surface instead of by header name.

## Reading Order

1. [architecture/system-overview.md](architecture/system-overview.md)
2. [architecture/type-system-and-storage.md](architecture/type-system-and-storage.md)
3. [architecture/viz-controls-and-interactions.md](architecture/viz-controls-and-interactions.md) — the Python visualization frontend/backend event model
4. [ga/operation-pipeline.md](ga/operation-pipeline.md)
5. [workflows/build-test-and-navigation.md](workflows/build-test-and-navigation.md)
6. [workflows/use-case-examples.md](workflows/use-case-examples.md)
7. [workflows/precompiled-wheels.md](workflows/precompiled-wheels.md) — building, cleaning, and uploading platform-specific wheels

## What This Library Is

TanGA is a C++17 template library for geometric algebra with an emphasis on:

- compile-time algebra shape via template parameters,
- bit-level blade encoding,
- sparse runtime multivectors for high-dimensional algebras,
- matrix-backed inversion and basis/subspace tooling,
- experimental cryptographic constructions built on top of modular multivector arithmetic.

## What This Library Is Not

- It is not a dense full-algebra runtime for arbitrary 32D multivectors.
- It is not a reference-manual-style API document.
- The `Tan.Crypt` module is not the main implementation site for the published cryptography experiments yet; the concrete algorithm flows currently live in the test applications.

## Fast Orientation

- Core utilities: `source/Tan.Core`
- Numeric and matrix support: `source/Tan.Math`
- Geometric algebra engine: `source/Tan.GA`
- Cryptography stub and key structs: `source/Tan.Crypt`
- Executable examples and experiments: `source/Tan.App.Test`
- Wheel packaging tools: `tools/build-precompiled.py`, `tools/clean-precompiled.py`, `tools/upload-pypi.py`

If you only have five minutes, read the architecture overview and the NTRU-in-GA note first.

## Repository Structure

```
tanga/
├── cpp/
│   ├── Tan.Core/        # bit utilities, assertions, value formatting
│   ├── Tan.Math/        # matrix algebra, Gaussian elimination, congruence
│   ├── Tan.GA/          # blade types, multivector representations, GA products
│   ├── Tan.Crypt/       # cryptographic key-material type stubs
│   ├── Tan.Crypt.Test/  # NTRU-style GA cryptography tests
│   └── Tan.App.Test/    # C++ example programs and experiments
├── py/
│   ├── pytanga/         # Python package (pybind11 auto-compile binding)
│   │   ├── codegen/     # code generation, CMake build, disk cache
│   │   ├── algebra/     # Algebra and MV classes
│   │   ├── basis/       # named basis classes (E3, P3, N3, PGA3)
│   │   ├── blade_mask/  # blade mask type for labeling axes
│   │   ├── matrix/      # product-matrix pipeline
│   │   ├── solver/      # solve, solve_lsq, solve_mod
│   │   ├── tensor/      # labeled tensor operations
│   │   ├── geometry/    # geometric entities and operators
│   │   └── viz/         # 3D visualization (three.js)
│   ├── examples/        # runnable demo scripts
│   ├── tests/           # pytest suite
│   └── cmake/           # legacy CMakeLists.txt location
├── docs/
│   ├── cpp/             # C++ API guides
│   ├── py/              # pytanga (Python) guides
│   ├── dev/             # architecture notes, type-system docs, workflow guides
│   └── analysis/        # research notes on NTRU in GA and modulus sizing
├── dev/
│   ├── todos/           # implementation plans
│   └── notes/           # research and design notes
├── tools/               # build/packaging scripts, license headers, hooks
├── precompiled/         # precompiled .so artifacts for platform wheels (build output, git-ignored)
└── pyproject.toml       # hatchling build config, dependencies
```

The module dependency order is strictly:
`Tan.Core` → `Tan.Math` → `Tan.GA` → `Tan.App.Test`

## License

Run [`add_license_headers.py`](https://github.com/dodeka12/tanga/blob/main/tools/add_license_headers.py) from the repo root
to stamp any new files that are missing it.
