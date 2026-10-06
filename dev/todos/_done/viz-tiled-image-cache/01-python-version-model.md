# Phase 1 — Python version model

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add a `version` to `ImagePyramid`, emit it from `meta()`, and assign it from a
per-`image_id` counter in `Visualizer._register_pyramid` so every re-registration
of the same id produces a new URL.

## Files

- Edit: `py/pytanga/viz/_image_pyramid.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_image_pyramid.py`

## Steps

- [x] **1.1 — `ImagePyramid.version` + `meta()` (`_image_pyramid.py`)**
  - Add `self.version: int = 0` in `__init__` (after `self.channels`), documented
    as "assigned by the `Visualizer` on registration; `0` for a standalone
    pyramid".
  - In `meta()`, add `"version": self.version` alongside the existing fields.

- [x] **1.2 — Per-id version counter (`visualizer.py`)**
  - Initialize `self._image_versions: dict[str, int] = {}` next to
    `self._image_pyramids` (line ~246).
  - In `_register_pyramid` (line ~1099): compute
    `version = self._image_versions.get(pyramid.image_id, 0) + 1`, store
    `self._image_versions[pyramid.image_id] = version`, set
    `pyramid.version = version`, then store the pyramid and forward to the server
    exactly as today.

- [x] **1.3 — Tests**
  - Extend `TestTiledSerialization` to assert `meta()["version"]` is present
    (`0` on a fresh `ImagePyramid`).
  - Add a test that registering two pyramids under the same id via
    `Visualizer._register_pyramid` (or the public `register_image_pyramid`)
    yields strictly increasing versions (`p1.version < p2.version`).

## Validation

```bash
uv run pytest py/tests/viz/test_image_pyramid.py -q
```

## Notes

- No new registration call sites are needed: `set_layout`/`add_layout` call
  `_register_background_pyramids`, and `set_background_image`/`ImageCanvas._sync_image`
  call `_register_pyramid`, so every tiled background/image is stamped through
  the same path.
- `VizServer.register_image_pyramid` does not assign versions; the `Visualizer`
  is the single source of truth for the counter.
