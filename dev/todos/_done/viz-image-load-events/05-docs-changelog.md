# Phase 5 — Docs + example + changelog

## Goal

Document the new `image_status` channel, add a runnable example demonstrating
the handlers, and write the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New: `py/examples/viz/image/image_load_events.py`
- New: `docs/changelog/YYYY/MM/DD_fix-image-loading.md` (branch changelog)
- Regenerate: example docs (`tools/generate-example-docs.py`)

## Steps

- [x] **5.1 — Developer docs (`viz-controls-and-interactions.md`)**
  - Add an "Image load events" subsection after "Client → server logging",
    documenting the reserved `image_status` control, the three event names +
    payloads, and the `viz.on_image_loaded` / `on_image_tile_load` /
    `on_image_tile_loaded` API (mirror the `client_log` write-up).

- [x] **5.2 — Example (`py/examples/viz/image/image_load_events.py`)**
  - Write a minimal example (license header + docstring per
    `dev/workflows/example-docs.md`: one-line `image_load_events.py — …`
    description, `Run with:`, trailing `Keywords:`) that sets a large tiled
    `ImageData`, registers `on_image_loaded` / `on_image_tile_load` /
    `on_image_tile_loaded` with `async def` handlers that call `show_banner` to
    report "loading…" vs "ready", and runs the viewer.
  - Regenerate: `uv run python tools/generate-example-docs.py`.

- [x] **5.3 — Branch changelog (`dev/workflows/changelog.md`)**
  - Determine the since-version: `uv run python tools/last-release.py`.
  - Create `docs/changelog/YYYY/MM/DD_fix-image-loading.md` with a **Bug
    Fixes** bullet (LOD boundary toggle) and **New Features** bullets (the three
    image lifecycle events + `on_image_*` API).

## Validation

```
uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict && uv run pytest py/tests/viz -q
```

## Notes

- This work reuses an existing pattern (backend-only reserved control), so the
  architecture docs are **extended with a subsection**, not restructured.
- The changelog is later renamed to its hash form at PR time per
  `dev/workflows/pull-request.md`; do not predict a release version now.
