# Phase 2 — Frame delivery + `viz.add(surface=…)` convenience

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (image-frame delivery and
> `Visualizer._image_frames_for`) and read `py/pytanga/viz/scene.py` (`add_viz`,
> `image_frames`, `depth_image_frames`) + `py/pytanga/viz/_image_wire.py`.  This
> phase reuses the existing binary-frame seam; it does not add a new protocol.

## Goal

Make surface-texture pixels travel as binary frames (default codec via
`encode_image_frame`) and expose a `surface=` convenience on `viz.add` /
`Scene.add_viz`.

## Files

- **Edit** `py/pytanga/viz/scene.py` — surface-texture registry, `surface_texture_frames()`, `add_viz(surface=…)`.
- **Edit** `py/pytanga/viz/visualizer.py` — `add(..., surface=…)` forward + `_image_frames_for` sum.
- **New** `py/tests/viz/test_surface_frames.py`

## Steps

- [x] **2.1 — `Scene` surface-texture registry + frames**
  - Add `self._surface_textures: dict[str, list[SurfaceTexture]] = {}` to `Scene.__init__`.
  - Add `Scene.surface_texture_frames() -> list[tuple[str, bytes]]`: for each registered entity's `SurfaceTexture`s whose `image.data is not None`, append
    `(img.id, encode_image_frame(img.id, img.data, codec=img.codec, jpeg_quality=img.jpeg_quality or 85))`
    (mirror `depth_image_frames()`).  Skip `source == "url"` textures (no bytes).
  - Remove a key's registry entry in `Scene.remove`/`clear` (where nodes are dropped).

- [x] **2.2 — `Scene.add_viz(..., surface=…)`**
  - Add a `surface: SurfaceMaterial | SurfaceShader | SurfaceTexture | list[SurfaceTexture] | tuple[SurfaceTexture, ...] | None = None` parameter.
  - Normalize with `surface_material(surface)`; when the result has textures, store `self._surface_textures[eid] = material.textures` after `self.add(...)`/`add_object(...)` returns `eid`.
  - Merge `material` into the style: if the caller supplied a `style`, set its `surface` only when not already set; otherwise build the kind-appropriate style with `surface=material` (mirror the existing `tex_label` merge in `add_viz`).

- [x] **2.3 — `Visualizer` forward + frame sum**
  - Forward `surface=` from `Visualizer.add(...)` → `scene.add_viz(...)` (match the existing `tex_label=`/`style=` forwarding).
  - In `Visualizer._image_frames_for` (line ~1373), return `scene.image_frames() + scene.depth_image_frames() + scene.surface_texture_frames()`.

- [x] **2.4 — update/remove parity**
  - On `update_entity`/re-`add_viz` of the same `eid`, replace the registry entry (and drop it when the new surface has no textures).
  - Confirm `remove`/`clear` clean the registry (no dangling frames).

- [x] **2.5 — tests (`py/tests/viz/test_surface_frames.py`)**
  - `Scene.surface_texture_frames()` encodes a `uint8` 3-channel texture with JPEG (assert the frame's codec byte resolves to `EImageCodec.JPEG`) and a `float32` texture with zlib.
  - `Scene.add_viz(Sphere(...), surface=SurfaceTexture(image=ImageData("t0", data=...)))` registers one frame and serializes `style.surface.textures[0].id == "t0"`.
  - `surface_material()` with a list of two textures emits two `SurfaceTexture.to_dict()` entries and registers two frames.

## Validation

```bash
uv run pytest py/tests/viz/test_surface_frames.py -q
uv run ruff check py/pytanga/viz/scene.py py/pytanga/viz/visualizer.py
uv run ty check
```

## Notes

- `encode_image_frame` already auto-selects JPEG for `uint8` 1/3-channel and zlib
  otherwise when `codec=None`; the texture carries `codec`/`jpeg_quality` through
  the wrapped `ImageData` (no JSON codec field — it lives in the binary header).
- Non-tiled only: surface `ImageData`s should be created with
  `tile_max_dim=None, tile_max_bytes=None` (document in the example).
