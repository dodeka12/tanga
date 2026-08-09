# TanGA Documentation

TanGA is a geometric algebra library with a C++ core and a Python interface
(**pytanga**).

---

## Key Features

- **High-dimensional algebras** — Work with geometric algebras over
  vector spaces of up to 31 dimensions with **any signature**.  Sparse
  blade encoding keeps storage and computation proportional to the number
  of non-zero coefficients, not the full $2^D$ blade space.
  → [Dynamic multivectors](cpp/dynamic-multivectors.md)

- **C++ template header library** — The core engine is 100 % C++17
  headers with `constexpr`-friendly templates.  Fixing dimension and
  signature at compile time lets the compiler inline and constant-fold
  blade arithmetic down to a handful of machine instructions.
  → [C++ documentation](cpp/index.md)

- **On‑demand Python compilation** — pytanga generates, compiles, and
  caches pybind11 bindings on first use of an `Algebra(dim, sig, dtype)`.
  Every unique combination is compiled once and loaded in milliseconds
  thereafter.  Pre‑compiled wheels for the most common configurations
  ship with the package, so zero‑setup `pip install` works for most users.
  → [Environment & Setup](py/env/index.md)
  · [Compile & Binding](py/env/compile-and-binding.md)

- **GA formula solving** — Convert GA product equations ($A \circ X = Y$)
  into **linear systems**, solve with Gaussian elimination (floating‑point
  or modular), and reconstruct the unknown multivector.  This operates at
  C++ level with blade‑mask‑restricted matrices.
  → [Matrix mapping & equations (C++)](cpp/matrix-mapping-and-equations.md)
  · [Equation Solving (Python)](py/solver/index.md)

- **Matrix and tensor pipelines** — Every blade‑mask‑aware operation is
  available as a **matrix** (`MVMatrix`, `MVProductMatrix`) or a labelled
  **tensor** (`MVTensor`, `MVLabeledTensor`).  Label‑driven Einsum‑style
  contractions, broadcasts, and slicing work directly on multivector data.
  → [Matrix Operations](py/matrix/index.md)
  · [Tensor Operations](py/tensors/index.md)

- **Geometry analysis and creation** — `analyze()` extracts the geometric
  meaning from a multivector (point, line, plane, rotor, motor, …) and
  `create()` constructs a multivector from geometric primitives.  Works
  across E3, P3, N3, and PGA3 algebras with a unified, algebra‑independent
  data model.
  → [Geometry (Python)](py/geometry/index.md)

- **Interactive 3D visualization** — `pytanga.viz` provides a live
  WebSocket‑driven Three.js visualizer in the browser.  Add entities,
  style them, animate keyframes, and export to:

    - **standalone HTML** (self‑contained, shareable, supports animations),
    - **embeddable HTML** for iframes (e.g. Reveal.js slides, supports animations),
    - **glTF / GLB** for use in other 3D tools,
    - **PNG screenshots** and **MP4 video** (requires a local browser).

  → [3D Visualization](py/viz/index.md)

---

## Documentation Sections

| Section | Audience | Contents |
|---------|----------|----------|
| [**C++ Documentation**](cpp/index.md) | C++ users | Public C++ API: multivectors, products, matrix equations, congruence maps |
| [**Python Documentation**](py/index.md) | Python users | pytanga: algebra basics, basis classes, blade masks, matrix/solver/tensor pipelines, geometry, visualization |
| [**Developer Documentation**](dev/index.md) | Contributors | Architecture overview, type system, GA pipeline internals, coding style guides, build workflows |

---

## AI-Tool Documentation Access

When pytanga is installed as a dependency, the markdown documentation and
example scripts are packaged inside the wheel. AI coding tools can expose
them by calling:

```python
import pytanga

pytanga.install_docs()     # copies docs to .dep-docs/pytanga/
pytanga.install_examples() # copies examples to .dep-examples/pytanga/
```

In a source checkout the functions copy from the local `docs/` and
`py/examples/` directories respectively. See the
[Python docs](py/index.md#ai-tool-documentation-access) for details.

---

## License

TanGA is released under the [Apache License 2.0](https://github.com/dodeka12/tanga/blob/main/LICENSE).
Every source file carries an `SPDX-License-Identifier: Apache-2.0` comment.
