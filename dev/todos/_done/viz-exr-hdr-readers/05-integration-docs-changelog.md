# Phase 5 — Integration + docs + changelog

## Goal

Wire the readers into the example and document them; record the feature in the
branch changelog.

## Files

- Edit: `py/examples/viz/image/load_image_from_disk.py`
- Edit: `docs/py/viz/image/` (image docs) and `docs/dev/architecture/viz-architecture.md` (one line)
- Edit: `docs/changelog/2026/09/25_fix-image-display.md`

## Steps

- [x] **5.1 — Example dispatch**
  - In `_load`, dispatch by suffix: `.exr` → `read_exr`, `.hdr`/`.pic` →
    `read_hdr`, else PIL.  Log a note that HDR values `> 1` need `u_value_max`
    (or a custom shader) for display.
- [x] **5.2 — Docs**
  - Add a short "HDR images" page/section (`exr` + `hdr`, linear values, no
    tone mapping) and cross-link from `custom-shaders.md`/`image-transport.md`.
  - Add one line to `viz-architecture.md` (image IO: `_image_io.py`).
  - Regenerate example docs (`tools/generate-example-docs.py`).
- [x] **5.3 — Changelog**
  - Add a `## New Features` bullet for the EXR/HDR readers (no new runtime
    deps).

## Validation

```
uv run ruff check py/pytanga/viz/_image_io.py py/examples/viz/image/load_image_from_disk.py \
  && uv run ty check \
  && uv run python tools/generate-example-docs.py --check \
  && uv run pytest py/tests/viz/ -q \
  && uv run mkdocs build --strict
```

## Notes

- Per `dev/workflows/changelog.md`, keep the `# Changes since version 2.11.0`
  title and rename to the hash form only at PR time.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
