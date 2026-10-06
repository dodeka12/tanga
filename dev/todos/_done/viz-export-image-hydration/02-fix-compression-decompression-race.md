# Phase 2 — Fix the `compress=True` decompression race

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture. If this work introduces or changes architecture, update the
> developer docs.

## Goal

Make the gzip-compressed animation data reliably available before the playback
engine reads it, by async-gating the bootstrap's data initialization on a
decompression promise.

## Files

- Edit: `py/pytanga/viz/export/_bootstrap/_animation.py`
- Edit: `py/tests/viz/test_image_canvas_export.py` (or a new test)

## Steps

- [x] **2.1 — Expose the decompression as a promise**
  - In `_ANIMATION_DECOMPRESS_JS`, assign the async IIFE to
    `window.__tangaAnimReady` (still setting `window.__TANGA_ANIMATION__` and
    `el.remove()` at the end).
- [x] **2.2 — Await the decompression at the top of the bootstrap data init**
  - In `js_animation_data_init`, prepend `await window.__tangaAnimReady;` so the
    bootstrap module's top-level `await` pauses `const animData = _getAnimData()`
    until the decompression resolves. The non-compressed path is a no-op
    (`window.__tangaAnimReady` is `undefined`; `await undefined` resolves
    immediately).
- [x] **2.3 — Regression test**
  - Assert the compressed animated HTML embeds `id="tanga-anim-data"` AND emits
    both `window.__tangaAnimReady` and the `await window.__tangaAnimReady;` gate.

## Validation

```
uv run pytest py/tests/viz/test_image_canvas_export.py -q
node js/dev/tests/check-syntax.mjs
```

## Notes

- No bundle rebuild is needed — this JS is generated at export time (the
  `adapter_js`), not part of `generate_library_js()`.
- Top-level `await` works here because the bootstrap *is* the module that reads
  the data. (It would **not** work in a separate `<script type="module">`, which
  does not block later sibling modules — verified.) The decompress module only
  exposes the promise; the bootstrap awaits it.
- Non-compressed exports are unaffected: `embed_animation_data` emits a classic
  `<script>` that sets `window.__TANGA_ANIMATION__` synchronously, and
  `await window.__tangaAnimReady` on `undefined` resolves immediately.
