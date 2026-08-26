# Phase 3 — Offloading compute from a handler to the user loop

## Goal

Let a control/interaction handler (which runs on the server's event loop,
`self._loop`) start an expensive computation **without stalling the
visualization loop** — for the common "show a banner, compute, then update the
scene" flow. In a `VisualizerApp`, the computation runs on the **user loop**
(the loop running `_app_main`), so it happens in the user's program context;
for plain synchronous `Visualizer` scripts (no user loop) the same pattern
falls back to an executor.

## Steps

- [x] **3.1 — Capture the user loop (`_app.py`)**
  - `VisualizerApp.__init__`: `self._user_loop = None`.
  - At the top of `_app_main()`, set
    `self._user_loop = asyncio.get_running_loop()` (the loop `run()` drives
    with `asyncio.run(...)`); reset to `None` in a `finally` after teardown.

- [x] **3.2 — `VisualizerApp.submit_user` (fire-and-forget + one-shot `done`)**
  - `submit_user(coro_factory, *args, done=None, **kwargs) ->
    concurrent.futures.Future`:
    `asyncio.run_coroutine_threadsafe(coro_factory(*args, **kwargs),
    self._user_loop)`. Raise a clear error if the user loop is not running.
  - If `done` is given, register it via `future.add_done_callback(...)` so it
    runs **exactly once** with the coroutine's result after completion (sync
    callable, invoked on the user-loop thread; failures are surfaced via the
    returned future). This is the primitive a handler uses to hand work to the
    user loop without blocking `self._loop` and without holding the handler
    open.

- [x] **3.3 — `VisualizerApp.run_user` (awaitable variant)**
  - `async def run_user(coro_factory, *args, **kwargs)`: `await
    asyncio.wrap_future(self.submit_user(coro_factory, *args, **kwargs))`.
  - Awaiting it from a handler **yields** to `self._loop` (it only polls the
    future's done-callback), so the visualization loop stays responsive while
    the coroutine runs on the user loop. Prefer `submit_user(..., done=...)`
    for background work so the handler returns immediately; use `run_user` only
    when the handler genuinely needs the result inline.

- [x] **3.4 — `VisualizerApp.run_user_sync` (blocking fn on the user loop)**
  - `async def run_user_sync(fn, *args, **kwargs)`: schedule
    `asyncio.to_thread(fn, *args, **kwargs)` on the user loop via `submit_user`,
    then await. Runs `fn` in the default executor *from the user loop* —
    neither loop is blocked.

- [x] **3.5 — `Visualizer.run_blocking` (executor fallback for sync users)**
  - `async def run_blocking(fn, *args, **kwargs)`: `await
    asyncio.get_running_loop().run_in_executor(None, fn, *args, **kwargs)`.
  - For plain `Visualizer` scripts (no user loop), a handler uses this instead
    of `run_user`; the compute runs in a worker thread while `self._loop`
    yields.

- [x] **3.6 — Recommended recipe (documented in Phase 6)**
  ```python
  async def on_slider(self, value, event):
      bid = await self.viz.show_banner_async("Calculating…", dismissable=False)

      async def _work():
          return await asyncio.to_thread(self._heavy, value)

      def _done(result):
          self.viz.update_entity("ent", result)
          self.viz.remove_banner(bid)
          self.viz.flush()

      self.submit_user(_work, done=_done)   # fire-and-forget; _done cleans up once
  ```

- [x] **3.7 — Tests (`py/tests/viz/test_app.py`, extend)**
  - `submit_user` schedules onto the captured loop and returns a future.
  - `submit_user(..., done=cb)` invokes `cb` exactly once with the result (and
    still runs it once on failure, with the exception available on the future).
  - `run_user` / `run_user_sync` return the coroutine/function result.
  - `run_blocking` returns the blocking fn's result from within a running loop.
  - A handler that `await`s `run_user` does not deadlock `self._loop`
    (schedule onto a second loop).

## Validation

`uv run pytest py/tests/viz/test_app.py py/tests/viz/test_flush_async.py -q`
