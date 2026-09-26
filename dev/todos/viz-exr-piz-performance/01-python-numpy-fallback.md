# Phase 1 — Python numpy fallback (vectorize the PIZ hot paths)

## Goal

Make the pure-Python PIZ decode fast enough that a dependency-free install
loads a 4096×2048 EXR in ~1–2 min (vs >30 min today), with the same output as
before.  This becomes the fallback when no C++ binding is available.

## Files

- Edit: `py/pytanga/viz/_image_io.py`

## Steps

- [x] **1.1 — Vectorize the LUT expansion**
  - Replace the `for i, value in enumerate(tmp): tmp[i] = lut[value]` loop with
    numpy fancy indexing: `tmp_np = lut_np[tmp_np]` where
    `lut_np = np.asarray(lut, dtype=np.uint16)` and `tmp_np` is a numpy array.
  - Keep the raw-fallback + interleaved-reassembly output byte-identical.

- [x] **1.2 — Vectorize the Huffman run expansion**
  - Convert `_huf_decode`'s `out` from a `[0] * n_raw` list to a numpy
    `uint16` array, and expand RLE runs with a slice assignment
    (`out[oi:oi+run] = value`) instead of the per-short `for _ in range(run)`
    loop.  Keep literal writes correct; ensure `oi`/bounds checks unchanged.
  - **Also fixed (root cause of the >30 s/chunk):** `_BitReader._c` was never
    masked, so it grew with the stream and made every bit op O(stream size),
    i.e. the decode was O(n²).  `_c` is now masked to 128 bits in `shift()`.

- [x] **1.3 — Vectorize the inverse wavelet (`_wav2_decode`)**
  - Rewrite `_wav2_decode` to operate on a numpy `uint16` array, vectorizing
    the per-level 2D passes with numpy slicing and vectorized `wdec14`/`wdec16`
    (the transform is a regular grid op at each level, so it maps to strided
    numpy views rather than per-element Python calls).
  - Preserve the exact `w14` vs `w16` selection (`mx < 1 << 14`) and the
    odd-column / odd-line edge handling.  The odd column/line index is
    `(dim // p2) * p2` (not `dim - p`), matching the reference for
    non-power-of-two dimensions.

- [x] **1.4 — Perf smoke**
  - Re-time `read_exr('~/Bilder/docklands_02_4k.exr', on_progress=…)`: a chunk
    should drop from >30 s to ~1–2 s.  Record the before/after in the commit
    message (no perf test committed — the file is not in the repo).

## Results (perf smoke)

- `docklands_02_4k.exr` (4096×2048 RGBA float, PIZ, 64 chunks) went from
  **>30 s per chunk** (~32 min total) to **~0.72 s per chunk / ~50 s total**.
- Per-chunk breakdown after vectorization: Huffman ~0.7 s, wavelet ~3 ms,
  LUT ~3 ms, reassembly ~3 ms.  The Huffman table build + bit decode is now the
  dominant cost; phases 2–3 (C++ `binding_piz`) remove it entirely.
- Byte-identity validated against `test_read_exr_piz` (`piz_rgb.exr`) plus a
  throwaway cross-check of the vectorized wavelet vs the scalar reference over
  4356 (w14/w16 × size 1/2 × 1..33×1..33) cases.

## Validation

```
uv run pytest py/tests/viz/test_image_io.py -q
```

## Notes

- The output (interleaved little-endian `uint16` bytes) must be byte-identical
  to the current implementation — `test_image_io.py` already pins it against
  the committed `piz_rgb.exr` reference and the hand-crafted raw fallback.
- `_wav2_decode` currently walks a Python `list`; after 1.3 `tmp` should be a
  numpy array through LUT → wavelet → reassembly to avoid list↔array copies.
- This phase is independent of the C++ work (phases 2–3) and is the
  "dependency-free" result that ships even without a compiler.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
