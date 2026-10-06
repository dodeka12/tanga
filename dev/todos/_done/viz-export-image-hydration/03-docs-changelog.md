# Phase 3 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture. If this work introduces or changes architecture, update the
> developer docs.

## Goal

Document the export bridge/hydration contract in the developer docs and record
the two fixes in the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/10/05_fix-html-export-transform.md`

## Steps

- [x] **3.1 — Document the bridge + hydration contract**
  - In `viz-architecture.md` (the "Image canvas" / export section), note that the
    export bootstrap hydrates image pixels via the `window.__tanga` frame-store
    API (`storeImageFrame` / `takeImageFrame` / `hasImageFrame` /
    `registerImageFrameConsumer`), and that `compress=True` animation data is
    decompressed asynchronously and awaited by the bootstrap.
- [x] **3.2 — Branch changelog**
  - Create/append `docs/changelog/2026/10/05_fix-html-export-transform.md` per
    `dev/workflows/changelog.md`. Title from
    `uv run python tools/last-release.py` (currently `2.15.0`). Add `## Bug Fixes`
    entries for (a) the missing image-frame bridge symbols and (b) the
    `compress=True` decompression race.

## Validation

```
uv run mkdocs build --strict
```

## Notes

- Do not touch `docs/changelog/index.md` — that happens at PR time (see
  `dev/workflows/pull-request.md`).
- The changelog filename uses the branch's start date (2026-10-05); if the branch
  predates that, use its actual first-commit date.
