# Animation export — entity-level frame diff (Strategy 1) — Overview

**Created:** 2026-10-19 | **Status:** Done | **Branch:** `feat/optimize-anim-recording`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the image export / asset-store and
> export-bootstrap sections) and the bootstrap generators in
> `py/pytanga/viz/export/_bootstrap/`.  This work changes the *serialized*
> animation-data shape (`frames` full snapshots → `initial` + `deltas` expanded at
> load) and therefore updates the developer docs in Phase 4.  It does **not** add
> a new seam/protocol: the data still arrives through `window.__TANGA_ANIMATION__`
> and is gzip-decompressed into `window.__tangaAnimReady` exactly as before.

## Goal

Stop storing the full per-frame entity snapshot in exported animated HTML, which
currently repeats unchanged entities (e.g. a static `PointPath`) once per frame and
bloats the file (~48% of the payload in the repro).  Store **frame 0 as a full
snapshot** and each subsequent frame as **only the entities that changed or were
removed**, then expand those deltas back into full frames in the browser at load.
Playback and scrubbing are unchanged — they keep consuming full `frames[]`.

## Architecture (short)

- **Capture stays full-snapshot.** `AnimationRecording.capture_frame()` keeps
  storing `Scene.full_state()` lists; the live recording path is untouched.
- **Diff at export time.** A new pure helper `diff_entity_frames(frames)` in
  `py/pytanga/viz/export/_animation_recording.py` reduces the in-memory full frames
  to `(initial, deltas)`; `AnimationRecording.to_diff_dict()` returns the compact
  wire dict.  `to_dict()` stays unchanged (full `frames`) for backward compatibility.
- **Expand at load.** `js_expand_frames()` (new generator in
  `_bootstrap/_animation.py`) emits `_expandFrames(animData)`, which returns
  `animData.frames` when present (legacy) or materializes `frames[]` from
  `initial`+`deltas`.  `js_animation_data_init` switches
  `const frames = animData.frames || [];` → `const frames = _expandFrames(animData);`.
- **Playback/scrub untouched.** `_reconcileFrame`, `_playFrame`, `_onScrub`, and the
  render loop still consume full `frames[n]`, so scrubbing behaviour is identical.

## Fixed contract (decided up front — later phases implement against this)

### Wire dict from `AnimationRecording.to_diff_dict()`

```json
{
  "initial":   [ /* full entity dicts for frame 0 */ ],
  "deltas":    [ /* index n == frame n+1 */ { "set": [ /* full entity dicts */ ], "remove": [ /* ids */ ] } ],
  "frame_count": 120,
  "cameras":   [ /* per-frame camera, unchanged */ ],
  "assets":    { /* image asset store, unchanged */ },
  "frame_assets": [ /* per-frame image hydration, unchanged */ ]
}
```

- `deltas[n].set` holds the **full** entity dict for every entity whose dict differs
  from the previous frame (added or changed).
- `deltas[n].remove` holds the ids removed since the previous frame.
- Unchanged entities are omitted.  Equality is exact dict equality keyed by `id`
  (order-independent); field-level/epsilon diffing is out of scope (future).

### Expansion JS (`_expandFrames(animData)`)

```js
function _expandFrames(animData) {
    if (animData.frames) return animData.frames;   // legacy full-snapshot input
    const initial = animData.initial || [];
    const deltas = animData.deltas || [];
    const frames = [initial];
    const state = new Map();
    for (const ent of initial) state.set(ent.id, ent);
    for (const d of deltas) {
        for (const id of (d.remove || [])) state.delete(id);
        for (const ent of (d.set || [])) state.set(ent.id, ent);
        frames.push([...state.values()]);
    }
    return frames;
}
```

## Decisions (confirmed)

- **Strategy 1 (expand-at-load), entity-level diff.** Field-level (aspect) diff and
  keyframe/lazy replay are out of scope (see Non-goals).
- **Diff at export time**, not capture time — capture stays a full snapshot and stays
  independent of the live viewer's dirty-flag tracking.
- **Backward compatible:** `to_dict()` and `render_export_animated_html(frames=…)`
  keep working; `_expandFrames` returns a legacy `frames` array unchanged.
- **Equality is exact dict equality by `id`** (no epsilon) for entity-level diff.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-entity-delta.md](./01-python-entity-delta.md) | `diff_entity_frames()` + `AnimationRecording.to_diff_dict()` + unit tests |
| 2 | [02-bootstrap-expand-and-embed.md](./02-bootstrap-expand-and-embed.md) | `_expandFrames` JS + `js_animation_data_init` wiring + export call sites switch to diff dict |
| 3 | [03-end-to-end-size-regression.md](./03-end-to-end-size-regression.md) | Export → decompress → assert static entity stored once + lossless round-trip |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Developer docs + changelog + supersede the old analysis note |

## Testing as you go

- `uv run pytest py/tests/viz/test_animation_export_diff.py -q` — new diff/round-trip tests (phase 1+).
- `uv run pytest py/tests/viz -q` — viz regression (phase 2, 3).
- `node js/dev/tests/check-syntax.mjs` — JS syntax gate (phase 2; `_bootstrap/*.py` is covered).
- `uv run mkdocs build --strict` — docs gate (phase 4).

## Non-goals

- **No field-level (aspect) delta** — only whole-entity diffs; a transform-only change
  still stores the full entity dict for that entity.
- **No keyframe/lazy replay or runtime memory reduction** — deltas are expanded to full
  `frames[]` at load; browser memory is unchanged.
- **No capture-time diffing** — capture stays a full snapshot.
- **No headless Playwright smoke for animation playback** in this plan (the exported
  scene graph is module-scoped, so a browser smoke can't trivially read world positions;
  correctness is covered by the Python lossless round-trip + the unchanged
  `_reconcileFrame` path).  Can be added later.
- **No change to image asset storage** (`assets`/`frame_assets`) — that's already
  store-once.

