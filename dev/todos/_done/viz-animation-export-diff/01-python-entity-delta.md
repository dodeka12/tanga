# Phase 1 — Python entity-level delta encoding

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the export / asset-store section) and
> `py/pytanga/viz/export/_animation_recording.py`.  This phase only adds a
> serialization helper; it does not change the wire/architecture (the export
> bootstrap already embeds `window.__TANGA_ANIMATION__`).

## Goal

Add a pure `diff_entity_frames(frames)` helper and an
`AnimationRecording.to_diff_dict()` that reduce full per-frame snapshots to
`initial` + `deltas` (the fixed contract in the README).

## Files

- **Edit** `py/pytanga/viz/export/_animation_recording.py`
- **New** `py/tests/viz/test_animation_export_diff.py`

## Steps

- [x] **1.1 — Add `diff_entity_frames(frames)`**
  - Pure module-level function; `frames` is `list[list[dict]]` (the in-memory
    `AnimationRecording._frames`).
  - Return `(initial, deltas)`:
    - `initial = frames[0]` (empty list when there are no frames).
    - For each consecutive pair `(prev, curr)`, build an id-keyed index of `prev`,
      then emit `{"set": [...], "remove": [...]}`:
      - `remove` = ids present in `prev` but absent in `curr`.
      - `set` = full dicts of entities in `curr` whose dict `!=` the `prev` dict
        (added or changed), in `curr`'s order.
  - Exact dict equality keyed by `id`; no epsilon.  Empty `frames` → `([], [])`.

- [x] **1.2 — Add `AnimationRecording.to_diff_dict()`**
  - Return the fixed-contract dict:
    `{"initial", "deltas", "frame_count", "cameras", "assets", "frame_assets"}`
    using `diff_entity_frames(self._frames)` plus the existing fields.
  - Do **not** include a `frames` key (that is the point); leave `to_dict()`
    unchanged.

- [x] **1.3 — Add `py/tests/viz/test_animation_export_diff.py`**
  - Static entity: appears in `initial` only, never in any `deltas[n]["set"]`.
  - Moving entity: appears in later `deltas[n]["set"]` with the changed dict.
  - Added entity: appears in the `deltas[n]["set"]` of the frame where it first
    appears.
  - Removed entity: appears in `deltas[n]["remove"]`.
  - Round-trip: a local `expand(initial, deltas)` reference reproduces the original
    `frames` exactly.
  - Empty recording → `initial == []`, `deltas == []`, `frame_count == 0`.

## Validation

```bash
uv run pytest py/tests/viz/test_animation_export_diff.py -q
```

## Notes

- Keep `to_dict()` unchanged so existing callers/tests keep passing.
- Write the test's `expand()` reference as the Python mirror of the JS
  `_expandFrames()` added in Phase 2, so the two stay trivially comparable.
