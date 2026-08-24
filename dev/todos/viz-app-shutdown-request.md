# VisualizerApp shutdown: opt-in Ctrl+Q and handler-triggered stop

**Created:** 2026-08-24 | **Status:** Done

## Goal

`VisualizerApp` (the managed-lifecycle base class) is missing the two shutdown
paths that already exist on the lower-level `Visualizer` API:

1. The **opt-in browser Ctrl+Q** binding (`enable_server_stop_key`) is not
   exposed, so an app cannot be ended from the visualization.
2. There is no way for an **event handler** (e.g. a "Quit" button's `on_click`)
   to end the app programmatically.

As a consequence, a `VisualizerApp`-based program currently cannot be stopped
at all: neither terminal **Ctrl+C** nor browser **Ctrl+Q** ends it. This plan
makes `run()` terminate cleanly (running `cleanup()` and stopping the server)
via terminal Ctrl+C, browser Ctrl+Q (when opted in), or an explicit
`request_shutdown()` call from any handler.

## Background / root cause

Two independent pieces of machinery already exist and are correct:

| Signal | Set by | Effect |
|---|---|---|
| `Visualizer._shutdown_requested` (global `threading.Event`) | terminal Ctrl+C/SIGTERM **or** browser Ctrl+Q (`scope:"server"`) | `wait()` returns **and** every `animate()` loop ends (via `interrupted()`) |
| `Visualizer._interrupt_events[scene]` (per-scene event) | browser `q` stop key | only that scene's `animate()` loop |

The gap is entirely in `py/pytanga/viz/_app.py`:

1. `VisualizerApp.__init__` does **not** forward `enable_server_stop_key` to the
   wrapped `Visualizer`, so Ctrl+Q can never be enabled for the main scene.
2. `Visualizer._ensure_server_running()` installs a custom `SIGINT`/`SIGTERM`
   handler that only **sets** `_shutdown_requested` — it never raises
   `KeyboardInterrupt`. (`visualizer.py:1301-1312`.)
3. But `VisualizerApp._app_main()` blocks with
   `while True: await asyncio.sleep(3600)` and only exits on
   `asyncio.CancelledError`. It never polls `_shutdown_requested`, so neither
   the terminal signal handler nor the browser Ctrl+Q handler can reach it.
   `run()`'s `except KeyboardInterrupt` therefore never fires.

`Visualizer.wait()` / `wait_for_shutdown()` already poll `_shutdown_requested`;
the app runner just needs to do the same.

## Design decisions

### 1. Reuse the global `_shutdown_requested` event (no teardown from the handler)

Shutdown is a *request*: setting the global event is enough to unblock the app
runner and to stop every running `animate()` loop (because `interrupted()`
reads the global event). Actual teardown stays in the existing path —
`_app_main()` runs `cleanup()`, then `run()`'s `finally` calls
`stop_server()`. A handler or keypress never stops the server directly,
mirroring `_on_browser_animation_stop(..., scope="server")` and the SIGINT
handler.

### 2. Poll the **global** event, not `interrupted()`

`_app_main()` observes only `_shutdown_requested` (plus the app's own flag), so
a per-scene browser `q` (which sets `_interrupt_events[scene]` only) ends an
`animate()` loop but does **not** tear down the whole app. Only the global
signal (Ctrl+C, Ctrl+Q, or `request_shutdown()`) ends the app.

### 3. A dedicated `_stop_requested` flag on the app

`request_shutdown()` may be called before the server has started (e.g. from
`init()`, or programmatically before `run()`), at which point
`Visualizer._shutdown_requested` does not yet exist. The app therefore keeps its
own `threading.Event` (`_stop_requested`) that is always available, and also
sets the viz's global event when it exists. `_app_main()` polls the OR of both.

### 4. `request_shutdown()` is synchronous and thread-safe

It only calls `threading.Event.set()`, so it is safe to call from an async
control/interaction handler (which runs on the server's event loop, a different
thread than the app's `asyncio.run` loop) without any `await`.

### 5. Naming

The public method is `request_shutdown()` — consistent with the existing
`_shutdown_requested` / "requesting shutdown" vocabulary, and it signals that
the call only *requests* shutdown (teardown still happens in `run()`).

## Files

- Modify: `py/pytanga/viz/_app.py` — constructor forward, `request_shutdown()`,
  `_is_stop_requested()` predicate, rewritten `_app_main()` block, `run()`
  docstring.
- Create: `py/tests/viz/test_app.py` — unit tests (no live server needed).
- Modify: `docs/py/viz/visualizerapp/app.md` — "Stopping the app" section +
  lifecycle step 3 wording.
- Modify: `docs/py/viz/visualizerapp/handlers.md` — constructor table +
  `request_shutdown()` documentation.
- Modify: `py/examples/viz/two_spheres_interact.py` — add a "Quit" button and
  `on_quit` handler calling `self.request_shutdown()`.
- Modify: `docs/changelog/2026-08-24_fix-dual-pga.md` — append a
  `## New Features` bullet (branch `fix/dual-pga`).

## Steps

### Phase 1 — `py/pytanga/viz/_app.py`

- [x] 1.1 Add `import threading` at the top of the module.
- [x] 1.2 Add `enable_server_stop_key: bool = False` to `__init__` and forward it
      to the `Visualizer(...)` constructor call.
- [x] 1.3 In `__init__`, after creating `self.viz`, create
      `self._stop_requested = threading.Event()`.
- [x] 1.4 Add the public shutdown method:

      ```python
      def request_shutdown(self) -> None:
          """Request that the app shut down.

          Callable from any context — including an async control/interaction
          handler (e.g. a "Quit" button) — to end :meth:`run`.  The event loop
          unblocks, :meth:`cleanup` runs, and the server stops.  Also sets the
          underlying :class:`~pytanga.viz.Visualizer` shutdown event so any
          running :meth:`~pytanga.viz.Visualizer.animate` loop ends as well.
          """
          self._stop_requested.set()
          shutdown = getattr(self.viz, "_shutdown_requested", None)
          if shutdown is not None:
              shutdown.set()
      ```

- [x] 1.5 Add the private predicate:

      ```python
      def _is_stop_requested(self) -> bool:
          """True once shutdown has been requested.

          True when :meth:`request_shutdown` was called, or when the underlying
          visualizer's global shutdown event is set (terminal Ctrl+C/SIGTERM,
          or the browser Ctrl+Q server-stop key).
          """
          if self._stop_requested.is_set():
              return True
          shutdown = getattr(self.viz, "_shutdown_requested", None)
          return shutdown is not None and shutdown.is_set()
      ```

- [x] 1.6 Replace the `_app_main()` blocking section

      ```python
      # 2. Block until Ctrl+C cancels the task
      try:
          while True:
              await asyncio.sleep(3600)
      except asyncio.CancelledError:
          pass
      ```

      with a poll of the shutdown predicate (keep the `CancelledError` net for
      Ctrl+C that arrives before the server's signal handler is installed):

      ```python
      # 2. Block until shutdown is requested (Ctrl+C, Ctrl+Q, or
      #    request_shutdown()), or the task is cancelled.
      try:
          while not self._is_stop_requested():
              await asyncio.sleep(0.05)
      except asyncio.CancelledError:
          pass
      ```

- [x] 1.7 Update the `run()` docstring: it now blocks until Ctrl+C, the browser
      Ctrl+Q (when `enable_server_stop_key=True`), or `request_shutdown()`.


### Phase 2 — Tests (`py/tests/viz/test_app.py`)

- [x] 2.1 Constructor forwards the flag:
      `VisualizerApp(enable_server_stop_key=True)` populates
      `app.viz._server_stop_configs[""]` with
      `{"enabled": True, "key": "q", "modifiers": ["ctrl"]}`.
- [x] 2.2 Default does not enable: `VisualizerApp()` leaves
      `"" not in app.viz._server_stop_configs`.
- [x] 2.3 `request_shutdown()` sets both `app._stop_requested` and, when present,
      `app.viz._shutdown_requested` (assign a fresh `threading.Event()` first).
- [x] 2.4 `request_shutdown()` is safe before the server has started (only sets
      `app._stop_requested`; no `AttributeError`).
- [x] 2.5 `_is_stop_requested()` returns `False` initially, `True` after
      `request_shutdown()`, and `True` when only `app.viz._shutdown_requested`
      is set.
- [x] 2.6 `asyncio.run(app._app_main())` runs `init()` and `cleanup()` and
      returns when `_stop_requested` is pre-set (recording subclass).
- [x] 2.7 `asyncio.run(app._app_main())` also returns when only
      `app.viz._shutdown_requested` is pre-set.

### Phase 3 — Docs & example

- [x] 3.1 `docs/py/viz/visualizerapp/app.md`: change lifecycle step 3 to mention
      Ctrl+C / Ctrl+Q / `request_shutdown()`; add a "Stopping the app" section
      with (a) `VisualizerApp(enable_server_stop_key=True)` for Ctrl+Q and
      (b) a Quit button calling `self.request_shutdown()`.
- [x] 3.2 `docs/py/viz/visualizerapp/handlers.md`: add `enable_server_stop_key`
      to the constructor parameter list/table; document `request_shutdown()`
      as the way an event handler ends the app.
- [x] 3.3 `py/examples/viz/two_spheres_interact.py`: add `on_quit` handler
      (`self.request_shutdown()`), a `quit` button, and include it in the
      `viewport_controls` group.

### Phase 4 — Changelog

- [x] 4.1 Append a `## New Features` bullet to
      `docs/changelog/2026-08-24_fix-dual-pga.md` (wrap ~80 columns,
      self-contained), e.g.:

      ```markdown
      - **`VisualizerApp` shutdown from the browser or a handler** —
        `VisualizerApp` now forwards `enable_server_stop_key` (opt-in Ctrl+Q),
        its `run()` blocks on the global shutdown event (so terminal Ctrl+C and
        browser Ctrl+Q both work), and a new `request_shutdown()` method lets an
        event handler (e.g. a "Quit" button) end the app cleanly.
      ```

## Verification

- [x] `uv run pytest py/tests/viz/test_app.py -q`
- [x] `uv run pytest py/tests/viz -q` (regression guard for the viz suite)
- [x] `uv run ruff check py/pytanga/viz/_app.py py/tests/viz/test_app.py py/examples/viz/two_spheres_interact.py`
- [ ] Manual: `uv run python py/examples/viz/two_spheres_interact.py` then
      press the **Quit** button → app exits and prints "Visualizer shut down.";
      re-run with `enable_server_stop_key=True` and press **Ctrl+Q** in the
      browser → app exits; terminal **Ctrl+C** also exits.

## Notes / edge cases

- **Opt-in only.** Ctrl+Q stays disabled by default (`enable_server_stop_key`
  defaults to `False`), matching `Visualizer`, so a stray Ctrl+Q cannot
  terminate existing scripts. The flag enables the **main scene** binding only;
  named scenes still opt in explicitly via `viz.scene(name, ...)`.
- **No teardown from the handler.** `request_shutdown()` only sets events;
  `_app_main()` → `cleanup()` → `run()`'s `finally` → `stop_server()` performs
  the actual stop. This keeps shutdown idempotent and matches the existing
  SIGINT/browser-stop paths.
- **`_shutdown_requested` availability.** It is created in
  `_ensure_server_running()`, which `run()` always reaches (via `show()`)
  before `_app_main()`. The `getattr(..., None)` guards and the app's own
  `_stop_requested` flag cover the pre-server case (`request_shutdown()` from
  `init()` or before `run()`).
- **Poll interval.** `0.05s` keeps button/keypress latency negligible without
  busy-spinning; the app loop is otherwise idle.
- **Per-scene `q` is unaffected.** Because the app polls the global event, the
  per-scene browser `q` still stops only that scene's `animate()` loop, never
  the whole app.

