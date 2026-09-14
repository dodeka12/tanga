# Phase 10 — End-to-end example(s)

## Goal

A runnable example that exercises the whole feature: display a numpy image,
adjust brightness/contrast with the mouse, and draw an overlay box in pixel
coordinates.

## Files

- New: `py/examples/viz/image/image_canvas.py`
- (optional) New: `py/examples/viz/image/pil_image.py`

## Steps

- [x] **10.1 — `image_canvas.py`**
  - Build or load a `uint8` (and, in a second canvas, a `float32`) image; create
    an `ImageCanvas`, add an overlay box/point path in pixel coordinates, and
    register a ctrl+left-drag handler that maps drag → `set_uniform`
    (brightness/contrast).

- [x] **10.2 — docstring**
  - Module docstring with a `<name>.py — …` description, a `Run with:  uv run
    python py/examples/viz/image/image_canvas.py` line, and a trailing
    `Keywords:` line (per `dev/workflows/example-docs.md`).

- [ ] **10.3 — (optional) `pil_image.py`**
  - Demonstrate `pil_to_numpy` with the lazy PIL import and a `uint16`/`float32`
    conversion.

- [x] **10.4 — smoke**
  - Run the example (`uv run python py/examples/viz/image/image_canvas.py`) and
    confirm the viewer serves the dedicated image scene and the handler fires.

## Validation

`uv run python py/examples/viz/image/image_canvas.py` (manual smoke — server
starts and the image renders; Ctrl+C to exit)

## Notes

- Follow `dev/workflows/example-docs.md` for the description + `Keywords:` header
  (and `tools/generate-example-docs.py` if the example is registered there).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
