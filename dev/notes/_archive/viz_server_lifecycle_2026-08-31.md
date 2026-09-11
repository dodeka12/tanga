# Viz Server Lifecycle — Event-Loop & Signal-Handler Corruption

**Repo to fix:** `tanga` (the library). This repo (`tanga-tutorial`) only *consumes*
`pytanga.viz`; the bug is in the library's server lifecycle code.

**Scope:** `Visualizer` / `VisualizerApp` / `SdfVisualizer` in
`py/pytanga/viz/` (and `py/pytanga/viz/sdf/`).

---

## Summary

`Visualizer.start_server()` (and the identical `SdfVisualizer` path) mutates
**process-global interpreter state** when it boots the viewer server, and
`stop_server()` never restores it:

1. It installs a fresh event loop as the *current* loop of the calling thread via
   `asyncio.set_event_loop(self._loop)` — and never puts the previous loop back.
2. It overwrites the `SIGINT` / `SIGTERM` handlers with its own `_on_sigint` — and
   never restores the previous handlers.
3. When the server fails to bind (e.g. the default port `8765` is already in
   use), the failure is swallowed inside a background `_boot()` task, so the
   caller sees a misleading `RuntimeError("Server failed to start within 5s")`
   instead of the real `"Port 8765 is already in use"` error.

The practical consequence: after a live-viewer cell runs and is stopped in a
Jupyter/ipykernel kernel, the kernel's event loop is left replaced by a stopped
loop, and a process can be left holding port `8765` in `LISTEN` state that only a
`kill -9` clears. This is what made the visualization Quick Tour's interaction
cell feel "not active", and what makes the next `start_server()` fail with a
confusing timeout.

---

## Root cause

### 1. Global event loop replaced and never restored

`Visualizer._ensure_server_running()`
(`py/pytanga/viz/visualizer.py:1450-1523`) creates a dedicated loop for the
server's background thread, but also **sets it as the calling thread's current
event loop**:

```python
# visualizer.py:1480-1486
self._loop = asyncio.new_event_loop()
asyncio.set_event_loop(self._loop)          # <-- mutates the caller's thread state

self._loop.create_task(_boot())

self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
self._thread.start()
```

`stop_server()` (`visualizer.py:1672-1713`) stops the loop, joins the thread and
nulls the fields, but never restores whatever loop was current before:

```python
# visualizer.py:1700-1712
if self._loop is not None and self._loop.is_running():
    fut = asyncio.run_coroutine_threadsafe(_stop(), self._loop)
    try:
        fut.result(timeout=timeout)
    except Exception:
        pass
    self._loop.call_soon_threadsafe(self._loop.stop)
    if self._thread is not None:
        self._thread.join(timeout=3.0)

self._server = None
self._loop = None        # <-- dereferenced, but the *previous* loop is not restored
self._thread = None
```

`stop_server()` also has an early-return guard (`if self._server is None: return`,
line 1674) which means if `start_server()` **failed** (see §3), the already-applied
`set_event_loop` / signal mutations are never undone at all.

Nothing in the codebase saves or restores the prior loop/handlers — a search for
`get_event_loop` / `signal.getsignal` / `_original` / `_saved` returns only the
mutating calls, no restoration.

### 2. `SIGINT` / `SIGTERM` handlers replaced and never restored

```python
# visualizer.py:1511-1520
self._shutdown_requested = threading.Event()

def _on_sigint(signum: int, frame: object) -> None:
    logger.info("Ctrl+C received - requesting shutdown")
    self._shutdown_requested.set()
    for event in self._interrupt_events.values():
        event.set()

signal.signal(signal.SIGINT, _on_sigint)
signal.signal(signal.SIGTERM, _on_sigint)
```

This replaces the process's default `KeyboardInterrupt` behaviour (and, in a
notebook kernel, the kernel's own interrupt handling) with one that only sets a
threading event. `stop_server()` does not restore the prior handlers.

### 3. Boot failure is swallowed → misleading timeout

Server startup runs inside a background task and the result is only signalled
via a `threading.Event`:

```python
# visualizer.py:1460-1489
_boot_done = threading.Event()

async def _boot() -> None:
    await self._server.start(...)   # <-- may raise (e.g. EADDRINUSE)
    _boot_done.set()

...
self._loop.create_task(_boot())
...
if not _boot_done.wait(timeout=5.0):
    raise RuntimeError("Server failed to start within 5s")
```

`VizServer.start()` already turns an in-use port into a clear error
(`py/pytanga/viz/server.py:277-287`):

```python
except OSError as e:
    if (getattr(e, "errno", 0) == 98
            or "address already in use" in str(e).lower()):
        raise RuntimeError(
            f"Port {self._port} is already in use. "
            f"Close the other process or use Visualizer(port=...) "
            f"to choose a different port.") from e
    raise
```

…but that exception is raised *inside* the `_boot` task, where nothing awaits it.
`_boot_done` is therefore never set, the 5 s wait times out, and the caller sees
the generic `RuntimeError("Server failed to start within 5s")`. The real cause is
hidden (only later surfaced as "Task exception was never retrieved" at GC, if at
all).

### 4. `SdfVisualizer` has the identical bug

`py/pytanga/viz/sdf/visualizer.py` duplicates the pattern:

- `asyncio.set_event_loop(self._loop)` — line 411
- `_boot_done.wait(timeout=5.0)` → `RuntimeError("SDF server failed to start within 5s")` — lines 416-417
- `signal.signal(SIGINT, …)` / `signal.signal(SIGTERM, …)` — lines 433-434

…with the same missing restore on stop.

### 5. `VisualizerApp.run()` compounds it

`VisualizerApp.run()` (`py/pytanga/viz/_app.py:134-169`) calls
`self.viz.show(...)` (which triggers `start_server()` and the mutations above),
then `asyncio.run(self._app_main())` on the *same* thread, and finally
`self.viz.stop_server()` — again leaving the mutated global state behind. In
Python ≥ 3.10 `asyncio.set_event_loop` is deprecated and interacts badly with a
host that already owns a running loop (as ipykernel 7 does).

---

## Observed symptoms

Verified while exercising the Quick Tour in
`tutorials/visualization/01_quick_tour/` with a real `ipykernel` (nbclient):

1. **Port left held after stop.** After a run that ended with
   `viewer.stop_server()` (and then a kernel shutdown), `ss -ltnp` still showed
   the `ipykernel_launcher` process `LISTEN`ing on `127.0.0.1:8765` and
   `[::1]:8765`. It had to be cleared with `kill -9`; `SIGTERM` was not enough.
2. **Misleading error on the next start.** With that stale process still holding
   `8765`, the next `start_server()` in a fresh kernel raised
   `RuntimeError: Server failed to start within 5s` — not
   `RuntimeError: Port 8765 is already in use …`.
3. **"Not active" interaction cell.** Because the server can fail to boot (or the
   kernel's loop is left in a broken state), the inline viewer never becomes
   interactive — which matches the reported "the scene does not stay active / I
   cannot click and drag".

---

## Impact by environment

| Environment | Behaviour |
|---|---|
| Plain script (`show()` + `wait()` + Ctrl+C) | Mostly works, but the replaced `SIGINT` handler and the stale `set_event_loop` leak into whatever runs after `stop_server()` in the same process. |
| Jupyter / ipykernel | **Broken.** The kernel owns a running asyncio loop; `set_event_loop` + signal-handler replacement corrupts it, and `stop_server()` doesn't restore it. A stale server can hold `8765` across cell re-runs / kernel restarts. |
| `VisualizerApp.run()` | `asyncio.run(_app_main())` runs on the same thread whose loop was already replaced by `show()`; teardown leaves the mutations behind. |
| `SdfVisualizer` | Same issues as `Visualizer`. |

---

## Reproduction

Minimal repro of the misleading error (after starting *any* viewer on `8765` and
leaving it running):

```python
# terminal 1
from pytanga.geometry import Point
from pytanga.viz import Visualizer
viz = Visualizer()
viz.start_server()            # binds 127.0.0.1:8765 and [::1]:8765
import time; time.sleep(60)   # keep the process alive

# terminal 2
from pytanga.viz import Visualizer
Visualizer().start_server()
# -> RuntimeError: Server failed to start within 5s   (expected: "Port 8765 is already in use")
```

To observe the leaked signal handler / loop:

```python
import asyncio, signal
before_loop = asyncio.get_event_loop()
before_int = signal.getsignal(signal.SIGINT)

viz = Visualizer()
viz.start_server()
viz.stop_server()

assert asyncio.get_event_loop() is before_loop        # fails — loop replaced
assert signal.getsignal(signal.SIGINT) is before_int  # fails — handler replaced
```

(Note: `asyncio.get_event_loop()` semantics changed in 3.10+; in 3.12 it may
raise when no loop is set — the key point is that the *previous* state is not
restored.)

---

## Proposed fix directions

For the `tanga` repo, in order of importance:

1. **Stop mutating the caller's loop.** Don't call `asyncio.set_event_loop()` on
   the calling thread. The server runs `self._loop.run_forever()` in its own
   thread; all cross-thread scheduling already passes `self._loop` explicitly
   (`run_coroutine_threadsafe(coro, self._loop)`, `call_soon_threadsafe`), so the
   global set is unnecessary. If it *is* needed somewhere, save the prior loop
   and restore it in `stop_server()`.

2. **Save and restore signal handlers.** Capture
   `signal.getsignal(SIGINT/SIGTERM)` before installing `_on_sigint`; restore
   them in `stop_server()` (and via the `atexit` hook). Prefer
   `loop.add_signal_handler(...)` (Unix) so the handler is scoped to the server
   loop rather than the whole process.

3. **Surface the real boot error.** In `_ensure_server_running`, keep a reference
   to the `_boot` task; on `_boot_done` timeout, retrieve and re-raise
   `task.exception()` so the caller gets `"Port 8765 is already in use …"` (or
   the underlying `OSError`) instead of the generic 5 s timeout.

4. **Make `stop_server()` idempotent against a failed `start_server()`.**
   Currently the `if self._server is None: return` guard skips restoring
   loop/handlers when `start_server()` raised after mutating global state.

5. **Apply the same fixes to `SdfVisualizer`** (`py/pytanga/viz/sdf/visualizer.py`).

---

## Affected locations (reference)

| File | Symbol | Lines |
|---|---|---|
| `py/pytanga/viz/visualizer.py` | `Visualizer._ensure_server_running` | 1450-1523 |
| | `Visualizer.stop_server` | 1672-1713 |
| | `Visualizer.wait` / `wait_for_shutdown` | 2034 / 1663 |
| `py/pytanga/viz/server.py` | `VizServer.start` (bind + EADDRINUSE re-raise) | 210-287 |
| | `VizServer.stop` | 289-304 |
| `py/pytanga/viz/sdf/visualizer.py` | `_ensure_server_running` (same pattern) | 390-434 |
| `py/pytanga/viz/_app.py` | `VisualizerApp.run` (`show()` → `asyncio.run` → `stop_server()`) | 134-169 |

---

*Workaround currently used by the tutorials:* live cells share a single
`Visualizer` and start the server lazily once, then stop it a single time at the
end — this avoids repeated `start_server()` calls but does **not** fix the
underlying global-state leak.

