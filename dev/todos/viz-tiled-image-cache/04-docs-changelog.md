# Phase 4 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Update the documented tile-URL contract to the versioned form and record the fix
in the changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/py/viz/image/tiled-images.md`
- New: `docs/changelog/2026/09/28_fix-viz-tiled-image-cache.md` (filename follows
  `dev/workflows/changelog.md`; adjust the branch/date to the actual branch)

## Steps

- [x] **4.1 — `docs/dev/architecture/viz-architecture.md`**
  - In the `source: "tiled"` bullet (around line 285), update the URL to
    `/image/{id}/{version}/{level}/{x}/{y}` and note that `version` is part of
    the tiled meta (bumped per id on re-registration so swaps never hit stale
    cached tiles).

- [x] **4.2 — `docs/py/viz/image/tiled-images.md`**
  - Update the `/image/{id}/{level}/{x}/{y}` mention (line 6) and add one
    sentence: the URL includes a `version` that changes when the same id is
    re-registered, so a runtime swap is never served stale cached tiles.

- [x] **4.3 — Changelog (per `dev/workflows/changelog.md`)**
  - Run `uv run python tools/last-release.py` for the title; add a `## Bug Fixes`
    bullet: large auto-tiled background images no longer show the previous image
    after a same-id swap (versioned tile URLs + `no-store`).
  - Do **not** hard-code a release version.

## Validation

```bash
uv run mkdocs build --strict
uv run python tools/build-viewer-js.py --check
```

## Notes

- `docs/changelog/index.md` is updated at PR time (after the hash rename), not
  during this phase — see `dev/workflows/changelog.md`.
