# Changes since version 2.10.0 (2.11.0-rc1)

## Bug Fixes
- **`SdfObject(Cylinder(...))` now honours `align_center=0.0`** — the SDF
  cylinder is based at `origin` (not centred), matching the mesh renderer and
  the documented `align_center` semantics.

## Refactor
- **Cached blade-name parsing** — `Algebra._resolve_key_signed` caches the
  string → blade-id resolution per algebra, removing the per-access parse cost
  of `mv["e14"]` / `mv["e12"] = x`.
- **Branch-free `MV` operator dispatch** — the six GA operators are bound once
  to plain/modular implementations, and the `MV` dunders route through them,
  skipping the per-call `modulus` re-check.
- **`EImageCodec` enum + `ImageFrameHeader` dataclass** — rename
  `ImageCodec` → `EImageCodec`; `ImageData.codec` / `encode_image_frame(codec=…)`
  now take the enum (`None` = auto), and binary-frame headers parse into an
  explicit `ImageFrameHeader` dataclass instead of positional `struct` unpacking.
