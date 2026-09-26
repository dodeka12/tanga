# Phase 2 — C++ PIZ decode + pybind11 binding

## Goal

A self-contained C++ `binding_piz` extension exposing
`piz_decode(chunk, width, n_lines, sizes) -> bytes`, adapted from the
BSD-3-Clause tinyexr/OpenEXR PIZ reference, that returns byte-identical output
to the Python `_piz_uncompress`.

## Files

- New: `py/pytanga/codegen/binding_piz.cpp`

## Steps

- [x] **2.1 — Port the PIZ decode to C++**
  - In `binding_piz.cpp`, implement (self-contained, no Tan.* includes):
    the Huffman decoder (bit reader + decode table + RLE), the inverse Haar
    wavelet (`wdec14`/`wdec16` + `wav2Decode`), and the bitmap→LUT→apply
    range expansion, mirroring `_piz_uncompress` / `_decode_exr_piz` in
    `_image_io.py`.
  - Handle the raw fallback (chunk length == `n_shorts * 2` → return the
    channel-planar-per-scanline data converted to interleaved) exactly as the
    Python path does.
  - Add a header comment attributing the algorithm to OpenEXR / tinyexr
    (BSD-3-Clause) and Christian Rouet's PIZ routines.

- [x] **2.2 — pybind11 module**
  - `PYBIND11_MODULE(binding_piz, m) { m.def("piz_decode", &piz_decode, py::arg("chunk"), py::arg("width"), py::arg("n_lines"), py::arg("sizes")); }`.
  - `piz_decode` takes `py::bytes`, `int width`, `int n_lines`,
    `std::vector<int> sizes`, returns `py::bytes` (interleaved little-endian
    `uint16` bytes).  Raise `std::runtime_error` on malformed data (Python
    side turns it into `ValueError`).

- [x] **2.3 — Compile + load smoke**
  - Build manually via `pytanga.codegen._build.build_binding(...,
    module_name="binding_piz")` and `pytanga.codegen._cache._load(...)`;
    assert `piz_decode` on a reference fixture equals the Python
    `_piz_uncompress` bytes (temporary check; the durable test is phase 4).

## Results (smoke)

- `binding_piz.cpp` compiles (g++ via the codegen CMake) and loads; `piz_decode`
  is byte-identical to `_piz_uncompress` for `piz_rgb.exr` (RGB half), the raw
  fallback (HALF and FLOAT), and `docklands_02_4k.exr` (RGBA float) chunks.
- Per-chunk speedup ~38× (19 ms vs ~724 ms) on the docklands chunks.

## Validation

```
uv run python - <<'PY'
# compile + load binding_piz and round-trip a reference PIZ chunk against _piz_uncompress
PY
```

## Notes

- `codegen/CMakeLists.txt` already builds any `BINDING_CPP` into `MODULE_NAME`
  (it also compiles three Tan.* impl files — harmless; `binding_piz.cpp` just
  doesn't include them).  Reuse it; do not add a parallel CMake build.
- `build_binding` requires `TANGA_SOURCE` (bundled `_ga_src/` or repo `cpp/`),
  which resolves automatically in `_build.py`.
- The C++ decode must be little-endian `uint16` on output; guard with a
  static_assert on `CHAR_BIT == 8` / endianness or use explicit little-endian
  packing to match the Python path.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
