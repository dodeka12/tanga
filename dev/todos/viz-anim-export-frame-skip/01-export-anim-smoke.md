# Phase 1 — Animated-export smoke harness (baseline)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Stand up a repeatable measurement of per-frame entity churn in an **exported**
animated HTML before touching any code, so phases 2–5 can prove (and then keep
guarding) that unchanged entities are no longer rebuilt.  Two new files under
`js/dev/tests/`:

- `serve-anim-export-smoke.py` — builds a representative scene, records it,
  exports it with `delivery="inline"` into a temp dir, serves that dir and
  prints the URL (no browser is opened; `Visualizer(...)` alone is enough — the
  recording reads `Scene.full_state()` directly, verified).
- `anim-export-smoke.mjs` — Playwright harness that wraps the export's
  `window.__tanga` bridge with counters, plays the animation once to the end
  and asserts the rebuild budget.

## Files

- New: `js/dev/tests/serve-anim-export-smoke.py`
- New: `js/dev/tests/anim-export-smoke.mjs`

## Steps

- [x] **1.1 — Generator script (`serve-anim-export-smoke.py`)**
  - Module docstring in repo style (`serve-smoke.py` shape): what it builds,
    the two-terminal invocation, `Run with:  uv run python
    js/dev/tests/serve-anim-export-smoke.py`.  SPDX + copyright header first.
  - Scene (`Visualizer(title="Tanga — animated export smoke",
    add_default_axes=False, add_default_grid=False)`, no `show()`):
    - **static** entities (must never be touched after frame 0):
      `Axes2D((0, 0), range_u=(-5, 5), range_v=(-5, 5))`;
      `Grid(dir_u=(1, 0, 0), dir_v=(0, 1, 0), range_u=(-5, 5), range_v=(-5, 5))`;
      two `Axis(...)` with `major_interval=1.0` and a `label=`;
      two `PointPath(max_points=64)` filled once with a 64-point curve;
      four `Point`s, two of them with `label="…"` (each label = one *overlay*
      entity);
    - **changing** entities (must update in place, never rebuild):
      one `Point` mover via `handle.entity = Point(...)`;
      one `Line` moved via its group/`set_transform(...)`;
      one changing `Axis` (`end` grows per frame);
      one changing `Grid` with a **constant** segment count
      (`range_u=(-5 + t, 5 + t)`) and one with a **changing** count
      (`range_u=(-5, -5 + t)`);
      one growing `PointPath` (`path.add(...)` per frame).
  - Record 100 frames at `fps=30`: `recording =
    viz.start_animation_recording()`, then per frame mutate → `viz.flush()` →
    `recording.capture_frame()`.  No `sleep_ms` (the recording is not
    wall-clock-driven).
  - Export: `viz.export_snapshot(<tmp>/smoke.html, overwrite=True,
    animation=recording, anim_style=AnimStyle(fps=30, loop=False,
    compress=True), delivery="inline")` — **`loop=False`** so playback stops at
    the last frame and the harness can wait for a deterministic end state.
  - Serve: `http.server.ThreadingHTTPServer(("127.0.0.1", 0), …)` rooted at the
    temp dir, print `ANIM_SMOKE_URL=http://127.0.0.1:<port>/smoke.html`, then
    `serve_forever()` (Ctrl+C to stop).  Print the file size and entity counts
    so a regression in the generator is visible.
  - Cleanup on exit: `viz.stop_server()` is *not* needed (no server started);
    leave the temp dir in place and print its path.

- [x] **1.2 — Counter harness (`anim-export-smoke.mjs`)**
  - Mirror `reconcile-smoke.mjs` structure: URL from `argv[2]` or `SMOKE_URL`,
    `chromium.launch({ headless: true, args: ['--enable-unsafe-swiftshader',
    '--use-angle=swiftshader'] })`, console/pageerror collection, exit code 1 on
    assertion failure with a printed diagnostics block.
  - Install counters **before** the page scripts run, via
    `page.addInitScript`:
    ```js
    window.__smoke = { created: 0, updated: 0, removed: 0 };
    let _tanga;
    Object.defineProperty(window, '__tanga', {
        configurable: true,
        get: () => _tanga,
        set: (v) => {
            const wrap = (name, key) => {
                const fn = v[name];
                v[name] = (...a) => { window.__smoke[key] += 1; return fn(...a); };
            };
            wrap('buildSceneObject', 'created');
            wrap('updateEntityMesh', 'updated');
            wrap('removeEntityMesh', 'removed');
            _tanga = v;
            window.__smoke.ready = true;
        },
    });
    ```
  - Flow: `goto(url)`, wait for `#tanga-play-btn` and `window.__smoke.ready`;
    wait until the first frame is on screen (`#tanga-scrub` `value === "0"` and
    `#tanga-time` shows a non-zero total) plus a 500 ms settle; snapshot
    `before`; `click('#tanga-play-btn')`; poll (≤ 30 s) until the button reads
    `▶ Play` again **or** `scrub.value === scrub.max`; snapshot `after`.
  - Print `JSON.stringify({ applied, before, after })` and assert:
    - `after.removed - before.removed <= Math.max(3, Math.round(applied * 0.05))`
    - `after.created - before.created <= Math.max(6, Math.round(applied * 0.1))`
    - `consoleErrors` empty.
  - Exit non-zero with the measured numbers on any failure.

- [x] **1.3 — Wire the docs entry**
  - Add the pair to `docs/dev/workflows/js-frontend-testing.md` next to the
    existing `serve-smoke.py` / `reconcile-smoke.mjs` block (same fenced
    `bash` + one-line explanation style).  This is the only production-adjacent
    edit in the phase.

- [x] **1.4 — Capture the baseline**
  - Run both terminals against the **unmodified** code and record the measured
    `applied / created / updated / removed` deltas in this file's `## Notes`.
  - Expect `removed ≈ created ≈ applied × (static + changing entities)` — the
    defect.  Write the number down; it is the "before" half of the fix proof.

## Validation

```bash
uv run python js/dev/tests/serve-anim-export-smoke.py        # terminal 1
node js/dev/tests/anim-export-smoke.mjs <printed-url>        # terminal 2
```

The run is expected to **fail** the thresholds at this phase (that is the
baseline).  The phase is complete when the script prints usable numbers and the
harness exits non-zero for the right reason (rebuild budget exceeded, not a
harness error).

## Notes

- `Visualizer(...)` needs no server for build + record + export (verified with
  a scratch script: the exported file is ~330 kB with the library inlined and
  the `three` addons imported from the CDN — the smoke therefore needs network
  access, exactly like any `delivery="inline"` export).
- Verified frame content: `Axes2D`, `Grid`, `Axis`, `PointPath`, `Point` are
  scene entities (`layer: "scene"`) and labels are **overlay** entities
  (`layer: "overlay"`), so the harness counters cover both reconcile branches.
- Verified that mutating `handle.entity` for `Axis` / `Grid` and appending to a
  `PointPath` re-serializes exactly those entities per frame — i.e. the
  "changing" entities of 1.1 really do produce per-frame `deltas`, which is
  what phases 4–5 need to exercise.
- Baseline numbers: `applied=99`, `before={created:16, updated:0, removed:0}`,
  `after={created:1006, updated:1584, removed:990}` → **10 rebuilds per applied
  frame** (`removed`/`created` deltas 990 over 99 frames).  The 10 are the
  scene entities whose updaters return `false` today (`Axes2D` 1 + `Axis` 3 +
  `Grid` 3 + `PointPath` 3); the other scene entities (`Point` ×5, `Line` ×1)
  already update in place.  The harness exits non-zero for the right reason
  (`removed delta 990 exceeds budget 5`), proving the gate works.

