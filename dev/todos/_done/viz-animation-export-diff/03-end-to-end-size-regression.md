# Phase 3 — End-to-end size regression + lossless round-trip

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the export path).  This phase only
> adds tests; it does not change architecture.

## Goal

Prove, end to end, that an exported animated HTML is smaller because static entities
are stored once, and that expanding the stored deltas reproduces the original full
frames losslessly.

## Files

- **Edit** `py/tests/viz/test_animation_export_diff.py`

## Steps

- [x] **3.1 — End-to-end export + decompress**
  - Build a `Scene`/`AnimationRecording` with a static `PointPath`, a moving `Circle`,
    and a radius-changing `Circle` (mirror
    `py/examples/viz/export/animated_circle_transform.py`), capture ≥ 20 frames.
  - `render_export_animated_html(rec.to_diff_dict(), …)` (or `export_snapshot(…,
    animation=rec, anim_style=AnimStyle(compress=True))`) → extract +
    gzip-decompress + base64-decode the `#tanga-anim-data` payload.

- [x] **3.2 — Assert static entity stored once**
  - The decompressed dict has `initial` and `deltas` (no `frames`).
  - The `PointPath` id appears in `initial` exactly once and in **no**
    `deltas[n]["set"]`.

- [x] **3.3 — Assert lossless expansion + size reduction**
  - `expand(initial, deltas)` (the Phase-1 reference) equals `rec.frames`.
  - The diff payload is strictly smaller than the equivalent full `frames` payload
    for the same recording (assert a concrete ratio, e.g. the `PointPath` bytes appear
    once, not `frame_count` times).

## Validation

```bash
uv run pytest py/tests/viz/test_animation_export_diff.py -q
uv run pytest py/tests/viz/test_export_animation_transform.py -q
```

## Notes

- This is the regression gate for the reported "static `PointPath` bloats the file"
  problem; keep the size assertion concrete (not just "smaller").
