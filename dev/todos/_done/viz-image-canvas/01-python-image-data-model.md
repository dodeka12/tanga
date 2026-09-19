# Phase 1 — Python image data model + `pil_to_numpy`

## Goal

The pure-Python image value type and dtype/channel rules that `ImageView` and
`ImageCanvas` build on, plus the optional PIL bridge.  No rendering or server
code here.

## Files

- New: `py/pytanga/viz/image.py`
- New: `py/tests/viz/test_image.py`
- Edit: `pyproject.toml`

## Steps

- [x] **1.1 — `ImageDType` enum + codes + internal-format map in `image.py`**
  - `ImageDType` (`uint8`, `uint16`, `float32`) with `.code` (0/1/2), a
    `from_code()` classmethod, and a `to_internal_format()` mapping used later
    by the frontend (`UNSIGNED_BYTE` / float texture), plus the per-dtype
    default `[value_min, value_max]` (`[0,1]`, `[0,65535]`, `[None,None]`).

- [x] **1.2 — `ImageData` dataclass**
  - Fields: `id`, `width`, `height`, `channels` (1/3/4), `dtype`, and either
    `data: np.ndarray` or `url: str` (mutually exclusive, validated).
  - Validation: 2-D (H×W) for 1 channel, 3-D (H×W×C) for 3/4; dtype in the enum;
    `data` C-contiguous (copy if not).  `to_bytes()` returns the contiguous
    buffer; `to_base64()` for export.

- [x] **1.3 — normalization helpers**
  - `default_value_range(dtype, channels)` and a `normalize` description used to
    populate `u_value_min`/`u_value_max` defaults on the wire.

- [x] **1.4 — `pil_to_numpy(img, *, dtype="uint8") -> np.ndarray`**
  - Lazy `import PIL` inside the function; raise a clear `ImportError` when PIL
    is absent.
  - Map modes: `L`→1 channel, `RGB`→3, `RGBA`→4, `I;16`→uint16, `F`→float32;
    apply `np.asarray(...).astype(dtype)` with the documented rescale for
    `uint16`/`float32`; reject unmapped modes.

- [x] **1.5 — Pillow dev dependency**
  - Add `"pillow"` to the `[dependency-groups] dev` block in `pyproject.toml`
    (dev/test only, not a runtime extra), then `uv sync --group dev`.

- [x] **1.6 — Unit tests `py/tests/viz/test_image.py`**
  - dtype codes round-trip; channel validation errors; `to_bytes` contiguity;
    `pil_to_numpy` raises `ImportError` when PIL is mocked absent, and converts
    `L`/`RGB`/`RGBA`/`I;16`/`F` correctly when PIL is present.

## Validation

`uv run pytest py/tests/viz/test_image.py -q && uv run ruff check py/pytanga/viz/image.py py/tests/viz/test_image.py`

## Notes

- `image.py` is pure data (no server/rendering imports) so it stays
  unit-testable in isolation — the same principle as `camera.py`.
- `pil_to_numpy` is public; it is the only place PIL is imported, so `pytanga`
  never requires Pillow at import time.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
