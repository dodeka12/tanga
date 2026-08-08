# TanGA

Geometric algebra library with a C++ core and a Python interface (**pytanga**).

**→ [Full documentation](https://dodeka12.github.io/tanga/)** — C++ and Python
API guides, architecture overview, notebooks, and developer workflows.

---

## Key Features

- **High-dimensional algebras** — Sparse blade encoding for vector spaces up to
  31 dimensions with arbitrary signature. Storage proportional to non-zero
  coefficients, not the full $2^D$ blade space.

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

- **Interactive 3D visualization** — Live WebSocket-driven Three.js visualizer
  in the browser. Export to standalone HTML, glTF/GLB, PNG, or MP4.

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