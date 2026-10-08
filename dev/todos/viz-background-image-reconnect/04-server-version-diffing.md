# Phase 4 — `_image_meta` `version` + `set_layout` uuid-diffing

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — "Image
> background" and "Granular updates").  No new seam; only an additive metadata
> field and server-side caching.

## Goal

Emit the `ImageData.version` uuid in the background metadata and make `set_layout`
re-encode/re-send a background frame only when its version changed (or it is new),
pruning ids that disappeared.

## Files

- Edit: `py/pytanga/viz/views/_helpers.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/tests/viz/test_image_background.py`

## Steps

- [x] **4.1 — Emit `version` in `_image_meta`.**
  - In `views/_helpers.py::_image_meta`, add `"version": image.version` to the
    `data`/`url` branch dict (tiled already emits `version` via `tiled_meta`).

- [x] **4.2 — Track versions and diff in `set_layout`.**
  - Add `self._background_versions: dict[str, str] = {}` to `LayoutHost.__init__`
    (next to `_background_frames`).
  - Change `_collect_background_frames(root)` (only called from `set_layout`) to
    build a `changed: dict[str, bytes]`: for each `data` background, if
    `self._background_versions.get(image.id) != image.version`, encode and add to
    `changed`, then store `_background_frames[id] = frame` and
    `_background_versions[id] = image.version`; otherwise skip (no encode).
  - Prune ids present in `_background_frames`/`_background_versions` but absent
    from the new layout (so a reconnect won't re-send a removed image), and return
    `changed`.
  - In `set_layout`, replace the blanket send with
    `for frame in self._collect_background_frames(root).values(): self._transport.send_bytes(frame)`.

- [x] **4.3 — Record version in `push_background_image`.**
  - In `_layout.py::push_background_image`, alongside
    `self._background_frames[image.id] = frame`, also set
    `self._background_versions[image.id] = image.version`.

- [x] **4.4 — Tests.**
  - `set_layout` twice with the **same** `ImageData` instance → exactly one binary
    frame total.
  - `image.update(data=...)` then `set_layout` again → a second frame is sent and
    `_background_versions[id]` changed.
  - A **new** `ImageData` instance (new uuid) → a new frame is sent.
  - `set_layout` with the background **removed** → `id` pruned from both
    `_background_frames` and `_background_versions`.

## Validation

`uv run pytest py/tests/viz/test_image_background.py -q`

## Notes

- This is only safe because Phase 2 makes the client keep the previous texture
  when no frame arrives; keep the phases in order.
