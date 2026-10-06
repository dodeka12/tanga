# Phase 7 — Example scripts (standard / raw / huge / stream)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add one runnable example script per use-case, so each transport tier is
discoverable.  The **huge image** and **image stream** examples are built from
programmatically generated noise.  Each script follows
`dev/workflows/example-docs.md` (module docstring with a one-line description, a
`Run with:` line, and a trailing `Keywords:` line).

## Files

- New: `py/examples/viz/image/standard_image.py`
- New: `py/examples/viz/image/raw_image.py`
- New: `py/examples/viz/image/huge_image.py`
- New: `py/examples/viz/camera/camera_stream.py`

## Steps

- [x] **7.1 — `standard_image.py` (uint8, default JPEG codec)**
  - An `ImageCanvas`/`ImageView` showing a synthetic uint8 RGB pattern
    (gradient + shapes) via `ImageData("std", data=...)` with the default
    (`auto`) codec — i.e. the in-band JPEG path.

- [x] **7.2 — `raw_image.py` (uint16, lossless)**
  - An `ImageCanvas` showing a uint16 gradient with
    `set_uniform("u_value_min", 0)` / `set_uniform("u_value_max", 65535)`,
    demonstrating the lossless zlib path (or `codec="raw"`) and exact-pixel
    preservation for scientific data.

- [x] **7.3 — `huge_image.py` (noise → tile pyramid)**
  - Generate programmatic noise (e.g.
    `rng.integers(0, 256, size=(4096, 8192, 3), dtype=np.uint8)`), register it
    with `viz.register_image_pyramid("noise", data, tile_size=256)`, and show it
    in a tiled `ImageView`/`SceneView` pane so pan/zoom fetch only the visible
    region.

- [x] **7.4 — `camera_stream.py` (noise → 30 Hz stream)**
  - Generate programmatic noise at 30 Hz, publish via
    `stream = viz.register_camera_stream("cam", fps=30)` /
    `stream.publish(ImageData("cam", data=...))`, and display it in a camera
    pane pointing at `/stream/cam` (mirrors `pinhole_calibrated_streaming.py`
    but over the MJPEG stream URL instead of `set_background_image`).

## Validation

```powershell
uv run ruff check py/examples/viz
uv run ty check py/examples/viz
```

Manual smoke (each opens the interactive viewer; stop with `q`/`Ctrl+C`):

```powershell
uv run python py/examples/viz/image/standard_image.py
uv run python py/examples/viz/image/raw_image.py
uv run python py/examples/viz/image/huge_image.py
uv run python py/examples/viz/camera/camera_stream.py
```

## Notes

- Depends on Phases 1–6 (codec, tiles, and streams must all exist first).
- The four scripts are the source material for the generated example docs in
  Phase 8.
