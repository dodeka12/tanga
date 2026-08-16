# TanGA

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

**→ [Full documentation](https://dodeka12.github.io/tanga/)** — C++ and Python
API guides, architecture overview, notebooks, and developer workflows.

---

## Key Features

### Visualization

- **Interactive 3D & 2D scenes** — Live WebSocket-driven Three.js visualizer in
  the browser. Rotate, pan, and zoom; add entities, apply per-entity styles, and
  work in 3D or 2D (`space_dim=2`). Usable without geometric algebra.

- **Animations** — Frame-by-frame streaming at ~60 FPS and keyframe tweening
  (`animate_to`) with a scene-aware `Timeline` sequencer.

- **Standalone HTML export** — Export self-contained, shareable HTML that
  includes animations, plus embeddable HTML for iframes, glTF/GLB for other 3D
  tools, PNG screenshots, and MP4 video.

- **Interactivity** — Interactive controls (sliders, dropdowns, buttons),
  pointer-based object interaction (click, drag, scroll), and a simplified
  `ActPoint` API. Jupyter notebook support with inline iframes.

### Geometric Algebra / Clifford Algebra

- **High-dimensional algebras** — Sparse blade encoding for vector spaces up to
  31 dimensions with arbitrary signature. Storage proportional to non-zero
  coefficients, not the full $2^D$ blade space.

- **Built-in spaces** — Explicit, ready-to-use algebras for **Euclidean**
  (E2/E3), **projective** (P2/P3), and **conformal** (N2/N3, PGA2/PGA3) spaces.

- **C++ template header library** — 100 % C++17 headers with `constexpr`-friendly
  templates. Compile-time dimension and signature let the compiler inline blade
  arithmetic down to machine instructions.

- **On‑demand Python compilation** — pytanga generates, compiles, and caches
  pybind11 bindings on first use. Pre‑compiled wheels for common configurations
  ship with the package — zero-setup `pip install` for most users.

- **GA formula solving** — Convert product equations into linear systems, solve
  with Gaussian elimination (floating-point or modular), and reconstruct the
  unknown multivector.

- **Matrix and tensor pipelines** — Blade-mask-aware matrices and labeled tensors
  with Einsum-style contractions, broadcasts, and slicing on multivector data.

- **Geometry analysis and creation** — `analyze()` extracts geometric meaning
  from a multivector; `create()` builds one from primitives. Works across E3,
  P3, N3, and PGA3 algebras.

- **galgebra interoperability** — Bidirectional conversion between
  [galgebra](https://github.com/pygae/galgebra) (sympy‑based) and tanga
  (numeric) multivectors via `GalgebraBridge`. Symbolic derivation → numeric
  computation → visualization, with support for non‑orthogonal bases.

→ [Full feature details](https://dodeka12.github.io/tanga/)

---

## Installation

```bash
pip install tanga-py
```

No C++ compiler or build tools required. pytanga ships with precompiled
bindings for the five most common algebra configurations on Linux (x86_64)
and Windows (win_amd64).

If you need a custom algebra not covered by the precompiled set, add the
`compile` extra (`pip install "tanga-py[compile]"`) — see the
[installation guide](https://dodeka12.github.io/tanga/py/env/installation/)
for per-platform compiler setup instructions.

---

## AI Tool Documentation Access

When pytanga is installed, the markdown documentation and example scripts are
packaged inside the wheel. AI coding tools can expose them by calling:

```python
import pytanga
pytanga.install_docs()     # copies docs to .dep-docs/pytanga/
pytanga.install_examples() # copies examples to .dep-examples/pytanga/
```

---

## License

TanGA is released under the [Apache License 2.0](LICENSE).
Every source file carries an `SPDX-License-Identifier: Apache-2.0` comment.