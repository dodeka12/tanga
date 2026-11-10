# Phase 3 — Serialize frame application (frame pump)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Stop overlapping reconciliations.  Today `_figAnimate` schedules the next
`requestAnimationFrame` **before** `await _playFrame(...)`, so a slow frame
build overlaps the next one and the oldest target wins on completion (frames
get applied out of order, and two reconciliations can mutate the same
`figMeshMap` concurrently).  Fix: one pure frame pump — at most one apply in
flight, newest target wins, no double-queue.

## Files

- New: `py/pytanga/viz/templates/frame-pump.js`
- New: `js/dev/tests/frame-pump.test.mjs`
- Edit: `py/pytanga/viz/export/_bootstrap/_html.py` (`_SHARED_JS_FILES`)
- Edit: `py/pytanga/viz/export/_bootstrap/_scene.py` (`_TANGA_BRIDGE_SYMBOLS`)
- Edit: `py/pytanga/viz/export/_bootstrap/_animation.py` (`js_frame_pump`,
  `js_animated_render_loop`, `_CONTROLS_JS`)
- Edit: `py/pytanga/viz/export/_animated_figure.py` (two assembly sites:
  emit `js_frame_pump()` right after `js_reconcile_frame(...)`, lines ~363 and
  ~505)
- New: `py/tests/viz/test_export_animation_frame_pump.py`

## Steps

- [x] **3.1 — Pure module `templates/frame-pump.js`**
  - No `import` lines, no DOM, no `three` (the export pipeline strips `import`
    and `export`, so a self-contained module is required by
    `py/tests/viz/test_export_renderers.py`).
  - API is the README contract; implementation shape:
    ```js
    // Frame pump — serialize frame application: one apply in flight, newest wins.
    export function createFramePump(apply, onError = (err) => console.error(err)) {
        let running = false;
        let pending = null;
        let waiters = [];

        function settle() {
            running = false;
            const w = waiters;
            waiters = [];
            for (const resolve of w) resolve();
        }

        async function drain() {
            running = true;
            try {
                while (pending !== null) {
                    const n = pending;
                    pending = null;
                    try {
                        await apply(n);
                    } catch (err) {
                        pending = null;     // drop the stale target
                        onError(err);       // never rethrow: rAF loop must survive
                        break;
                    }
                }
            } finally {
                settle();
            }
        }

        function whenIdle() {
            if (!running) return Promise.resolve();
            return new Promise((resolve) => waiters.push(resolve));
        }

        return {
            request(n) {
                pending = n;                // newest target wins (coalesced)
                if (!running) drain();      // fire-and-forget
                return whenIdle();
            },
            get busy() { return running; },
            idle() { return whenIdle(); },
        };
    }
    ```
  - Guard against unbounded recursion by construction: `drain()` is only ever
    started when `!running`, and a `request()` issued from inside `apply` just
    sets `pending` (the loop picks it up).
  - JSDoc the contract (one apply in flight, newest wins, `onError` receives a
    rejection instead of it escaping into `requestAnimationFrame`).

- [x] **3.2 — `js/dev/tests/frame-pump.test.mjs`**
  - Import from `'../../../py/pytanga/viz/templates/frame-pump.js'`
    (`npm test` runs `node --test tests/*.test.mjs`, so no config change).
  - Cases (all with a controllable `apply` that records calls and resolves on a
    deferred promise):
    1. idle `request(3)` → exactly one `apply(3)`; `busy` true during, false
       after `await pump.idle()`; the returned promise resolves.
    2. burst while busy — `request(1)`, then `request(2)`, `request(3)` before
       releasing the first → applies `[1, 3]` (middle target coalesced away).
    3. re-entrant request from inside `apply` → queued, applied next, and
       `apply` never runs nested (assert a depth counter never exceeds 1).
    4. rejecting `apply` → `onError` receives the error, `busy === false`
       afterwards, and a following `request` still applies.
    5. `idle()` on a fresh pump resolves immediately; `idle()` during a run
       resolves only after the last apply.
    6. `request()` while busy returns a promise that resolves when the pump is
       next idle (the `_onScrub` contract).

- [x] **3.3 — Register the module (bundle + bridge)**
  - `_html.py::_SHARED_JS_FILES`: add `_TEMPLATES_DIR / "frame-pump.js",` (next
    to `scene-builder.js` / `image-frames.js`) and extend the list's comment
    with one line: "``frame-pump.js`` serializes animated-export frame
    application (one apply in flight, newest target wins)."
  - `_scene.py::_TANGA_BRIDGE_SYMBOLS`: add `createFramePump` (immediately
    before `updateEntityMesh`).  Both `js_tanga_bridge()` and
    `js_tanga_destructure()` derive from that string, so the bootstrap can reach
    the factory — same reason `updateEntityMesh` is listed.
  - No change needed for the *live* viewer bundle: `frame-pump.js` is only
    referenced by the export bootstrap; listing it in `_SHARED_JS_FILES` is
    enough (it has no imports, so `_strip_imports` is a no-op).

- [x] **3.4 — Emit the pump in the bootstrap (`_animation.py`)**
  - New generator next to `js_reconcile_frame`:
    ```python
    def js_frame_pump() -> str:
        """Generate the ``_framePump``/``_requestFrame`` declarations. ..."""
        return """// ── Frame pump (one apply in flight; newest target wins) ──
    const _framePump = createFramePump(_playFrame);
    function _requestFrame(n) {
        return _framePump.request(n);
    }"""
    ```
  - Use the **default** `onError` (`console.error`): `sendLog` exists only in the
    library scope and is *not* a bridge symbol, so the bootstrap cannot call it.
    The smoke harness treats `console.error` output as a failure signal, so a
    rejected apply is still loud.
  - Docstring: one apply at most, newest target wins, `_requestFrame` is
    fire-and-forget except for `_onScrub`.
  - `_animated_figure.py`: call `js_frame_pump()` immediately after each
    `js_reconcile_frame(...)` call (two sites, ~line 363 and ~line 505) and
    include it in the assembled bootstrap part list, before the controls JS.

- [x] **3.5 — Route the three call sites through the pump**
  - `js_animated_render_loop` (`_animation.py`): make the loop **non-async**
    (`function _figAnimate(timestamp)`) and replace `await _playFrame(...)` with
    `_requestFrame(targetFrame);` (promise deliberately ignored).  Keep
    `requestAnimationFrame(_figAnimate)` first, the `targetFrame !== currentFrame`
    guard, the end-of-playback branch and `_updateScrubBar()` unchanged; update
    the docstring to say frames are *requested* and applied at most one at a
    time.
  - `_CONTROLS_JS` (`_animation.py`):
    - `_togglePlay` restart branch: `_requestFrame(0);` instead of
      `_playFrame(0);`.
    - `_onScrub`: `await _requestFrame(targetFrame);` instead of
      `await _playFrame(targetFrame);` — the request promise resolves on the
      next idle moment, so scrubbing during playback still hits the newest
      target and never stacks.
    - The `_figAnimate` speed wrapper (`_origFigAnimate`) is untouched: it only
      forwards a timestamp and stays valid because the loop is still a plain
      function.

- [x] **3.6 — Emitted-JS regression test (`test_export_animation_frame_pump.py`)**
  - SPDX + copyright header, docstring: the loop shape is a Python-emitted
    string; behavioural coverage is `js/dev/tests/frame-pump.test.mjs` +
    `anim-export-smoke.mjs`.
  - Assert on `js_animated_render_loop(fps=30, scene_var="figScene")`:
    `"async function _figAnimate" not in js`, `"await _playFrame(" not in js`,
    `"requestAnimationFrame(_figAnimate)" in js` and `"_requestFrame(" in js`.
  - Assert on `js_frame_pump()`: `"createFramePump(_playFrame)" in js` and
    `"function _requestFrame(" in js`.
  - Assert `createFramePump` is a bridge symbol:
    `"createFramePump" in js_tanga_bridge()` and in `js_tanga_destructure()`,
    and that `generate_library_js()` contains `"export function createFramePump"`
    **stripped** (i.e. `"function createFramePump(" in lib`) — this is the
    regression guard for forgetting `_SHARED_JS_FILES`.
  - Assert the module file exists with no `import`/`^export` lines other than the
    function (pattern after `test_export_renderers.py`).

- [x] **3.7 — Harness scrub pass (`anim-export-smoke.mjs`)**
  - After the play-through assertion, exercise the scrub path: sample the
    counters, then for each of `[0, mid, last]` set `#tanga-scrub.value` and
    dispatch `new Event('input', { bubbles: true })`, waiting until
    `#tanga-time` reflects the target (≤ 5 s each).
  - Assert the scrub pass added **no** `removed`/`created` churn (same budget
    as playback) and that `scrub` did apply frames (`updated` grew or the
    applied count advanced) — this is the only automated coverage of
    `_onScrub` → `_requestFrame` serialization.
  - Keep the whole harness one file so both gates stay in sync.

## Validation

```bash
cd js/dev && npm test && npm run check
uv run pytest py/tests/viz -q
node js/dev/tests/anim-export-smoke.mjs <url>     # generator from phase 1
```

Smoke: no `console.error`, playback reaches the last frame, and dragging
`#tanga-scrub` (harness step) applies frames in order — the harness already
asserts the rebuild budget, which must not regress.

## Notes

- **A redundant apply is possible, by design tolerated.**  `currentFrame` is
  only updated *after* a frame is applied, so the rAF loop may request the same
  target twice while it is in flight.  Thanks to phase 2 that second apply is a
  no-op (`_src === ent` for every entity), so no extra state is worth adding
  here.
- The pump must never be re-entered: `_playFrame` may itself await
  `buildSceneObject`; a request issued meanwhile waits its turn instead of
  interleaving.
- `_figAnimate` being synchronous also removes the previous "async loop +
  `requestAnimationFrame` first" overlap: rendering, controls update and frame
  application no longer race.
