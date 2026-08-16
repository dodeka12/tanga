# TanGA Documentation

TanGA is a Python and C++ library for **interactive technical visualization**
and **geometric algebra (Clifford algebra)** — two independent toolkits under
one roof.

- **Visualization** — build animated, interactive 3D and 2D technical scenes in
  the browser, and export them as standalone HTML (animations included),
  glTF/GLB, PNG, or MP4. No knowledge of geometric algebra required.
- **Geometric algebra / Clifford algebra** — sparse multivectors over vector
  spaces of up to 31 dimensions with arbitrary signature, with explicit support
  for Euclidean, projective, and conformal spaces (E2/E3, P2/P3, N2/N3,
  PGA2/PGA3). Backed by a C++ template core with a zero-setup Python interface
  (**pytanga**).

---

## Key Features

### Visualization

- **Interactive 3D & 2D scenes** — `pytanga.viz` provides a live
  WebSocket‑driven Three.js visualizer in the browser.  Add entities, style
  them, rotate/pan/zoom the camera, and work in 3D or 2D (`space_dim=2`).
  Usable without geometric algebra.
  → [3D Visualization](py/viz/index.md)

- **Animations** — Frame-by-frame streaming at ~60 FPS and keyframe tweening
  (`animate_to`) with a scene-aware `Timeline` sequencer.
  → [Animation](py/viz/animation.md)

- **Standalone HTML export** — Export self-contained, shareable HTML that
  supports animations:

    - **standalone HTML** (self‑contained, shareable, supports animations),
    - **embeddable HTML** for iframes (e.g. Reveal.js slides, supports animations),
    - **glTF / GLB** for use in other 3D tools,
    - **PNG screenshots** and **MP4 video** (requires a local browser).

  → [Export & Capture](py/viz/export.md)

- **Interactivity** — Interactive controls (sliders, dropdowns, buttons),
  pointer-based object interaction (click, drag, scroll), and a simplified
  `ActPoint` API.  Jupyter notebook support with inline iframes.
  → [Interactive Controls](py/viz/interactive.md)
  · [Object Interaction](py/viz/object-interaction.md)
  · [Jupyter Notebooks](py/viz/jupyter.md)

### Geometric Algebra / Clifford Algebra

- **High-dimensional algebras** — Work with geometric algebras over
  vector spaces of up to 31 dimensions with **any signature**.  Sparse
  blade encoding keeps storage and computation proportional to the number
  of non-zero coefficients, not the full $2^D$ blade space.
  → [Dynamic multivectors](cpp/dynamic-multivectors.md)

- **Built-in spaces** — Explicit, ready-to-use algebras for **Euclidean**
  (E2/E3), **projective** (P2/P3), and **conformal** (N2/N3, PGA2/PGA3)
  spaces.
  → [Basis Classes](py/basis/index.md)

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

- **galgebra interoperability** — `GalgebraBridge` provides bidirectional
  conversion between galgebra (sympy‑based, symbolic) and tanga (numeric)
  multivectors.  Derive symbolically, compute numerically, visualize — or
  work the other way.  Handles both orthogonal and non‑orthogonal bases
  via automatic metric diagonalization.
  → [Galgebra Bridge](py/algebra/galgebra_bridge.md)

---

## Documentation Sections

| Section | Audience | Contents |
|---------|----------|----------|
| [**C++ Documentation**](cpp/index.md) | C++ users | Public C++ API: multivectors, products, matrix equations, congruence maps |
| [**Python Documentation**](py/index.md) | Python users | pytanga: algebra basics, basis classes, blade masks, matrix/solver/tensor pipelines, geometry, visualization, galgebra interop |
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
