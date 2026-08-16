# Fix: Visualizer WebSocket Startup and Browser Connection Flow

## Problem

Sometimes `visualizer.start()` shows "Browser loaded page" but then hangs — the
`ready` WebSocket message never arrives, and Ctrl+C doesn't work. The user sees
"No browser connected after 30s" despite the HTTP page load succeeding.

## Root Causes

1. **`_wait_for_client_quiet` checks raw WebSocket, not `ready` round-trip**
   - An old tab's JS auto-reconnects (viewer.js:176), the raw WS connects
   - But if JS is frozen/crashed, `ready` message never arrives
   - `_wait_for_client_quiet` returns True (thinks a browser is connected)
   - New tab is never opened

2. **Multiple parallel wait mechanisms**
   - `_wait_for_client_quiet` — polls `_ws_clients` (raw WS)
   - `wait_for_browser()` — waits for `_ws_ready_event` (threading.Event)
   - `check_page_tokens()` — independent diagnostic task
   - `run()` uses yet another `asyncio.Event`

3. **`_ws_ready_event` set AFTER push operations** (server.py:394-395)
   - If `_push_full_state` or `_push_controls_cb` throws, `_on_ready` never called
   - `_ws_ready_event` never set → 30s timeout

4. **Ctrl+C not interruptible**
   - `threading.Event.wait(timeout=30)` — signal delivery unreliable in multi-threaded code

5. **No page token correlation for new tabs**
   - `open_browser()` doesn't pass a token
   - New tab gets random server-generated token
   - Visualizer can't distinguish between new tab and stale tab

## Desired Behavior

1. Wait for browser to reconnect (any browser with any token = fine)
2. If no browser reconnects within ~3s, open new tab with a unique token
3. Wait for WS `ready` with our token (or any if reconnected)
4. Single unified wait path (not multiple parallel waits)
5. Ctrl+C must work during wait
6. Stale browser reconnecting after new tab opened must not break things

## Implementation Plan

### File: `py/pytanga/viz/server.py`

#### Change 1: Add `_any_ws_ready` event

After line 74 (`_pending_page_tokens` dict), add:
```python
self._any_ws_ready: asyncio.Event = asyncio.Event()
```

#### Change 2: Read `token` query param in `_catch_all_handler`

In `_catch_all_handler` (around line 296), before generating `page_token`:
```python
# Use token from URL query param if present, otherwise generate random
page_token = request.query.get("token") or uuid4().hex[:8]
```
This makes `open_browser("http://host:port/?token=abc123")` work.

#### Change 3: Set `_any_ws_ready` on any `ready` message

In `_ws_handler`, inside the `if msg_type == "ready":` block (around line 394), before the existing code:
```python
self._any_ws_ready.set()
```

Also move `_on_ready()` call to BEFORE `_push_full_state` and `_push_controls_cb`:
```python
if self._on_ready is not None:
    self._on_ready()
await self._push_full_state(ws, scene_name=scene_name)
if self._push_controls_cb is not None:
    await self._push_controls_cb(scene_name)
```

And wrap push operations in try/except so an exception doesn't prevent `_on_ready`:
```python
if self._on_ready is not None:
    self._on_ready()
try:
    await self._push_full_state(ws, scene_name=scene_name)
except Exception:
    pass
try:
    if self._push_controls_cb is not None:
        await self._push_controls_cb(scene_name)
except Exception:
    pass
```

#### Change 4: Add `wait_for_ws_ready()` method

New method on VizServer:
```python
async def wait_for_ws_ready(self, *, timeout: float = 30.0) -> bool:
    """Wait until at least one browser completes the WebSocket ready round-trip.
    
    Returns True if ready received, False on timeout.
    """
    if self._any_ws_ready.is_set():
        return True
    try:
        await asyncio.wait_for(self._any_ws_ready.wait(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False
```

#### Change 5: Keep `check_page_tokens` but don't call it from `start()`

Remove the call to `check_page_tokens()` from `visualizer.py` `start()`.
Keep the method for standalone diagnostic use.

#### Change 6: Remove `_print_ws_reachability_note` from `open_browser`

Not needed — this is handled by `_print_ws_timeout_note` in the visualizer.

### File: `py/pytanga/viz/visualizer.py`

#### Change 7: Generate page_token in `start()`

At the top of the browser-opening logic in `start()` (around line 663):
```python
import secrets

if self._open_browser:
    page_token = secrets.token_hex(4)  # 8 hex chars
    if self._reuse_existing:
        fut = asyncio.run_coroutine_threadsafe(
            self._server.wait_for_ws_ready(timeout=3.0), self._loop
        )
        try:
            reconnected = fut.result(timeout=3.5)
        except (concurrent.futures.TimeoutError, asyncio.TimeoutError):
            reconnected = False
        if not reconnected:
            print("No existing browser reconnected — opening new tab.")
            self._server.open_browser(f"/?token={page_token}")
    else:
        self._server.open_browser(f"/?token={page_token}")
```

Note: `_server.open_browser()` appends to `self.url`, so we need to modify it or pass a path.

#### Change 8: Modify `open_browser()` in server.py to accept optional path

```python
def open_browser(self, path: str = "") -> None:
    url = self.url + path
    ...
```

#### Change 9: Replace `wait_for_browser()` logic

In `start()`, replace the `wait_for_browser` block (lines 670-673):
```python
if wait_for_browser:
    fut = asyncio.run_coroutine_threadsafe(
        self._server.wait_for_ws_ready(timeout=timeout), self._loop
    )
    try:
        ready = fut.result(timeout=timeout + 1.0)
    except (concurrent.futures.TimeoutError, asyncio.TimeoutError):
        ready = False
    if not ready:
        self._print_ws_timeout_note()
        return False
    return True
```

#### Change 10: Remove `_ws_ready_event`, `_wait_for_client_quiet`, `_print_connect`

- Remove `self._ws_ready_event` from `__init__` (line 143)
- Remove `self._ws_ready_event.clear()` from `start()` (line 625)
- Remove `_wait_for_client_quiet` method entirely (lines 752-768)
- Remove `_print_connect` method (lines 792-801) or wire it up as `_on_connect` callback
- Remove `check_page_tokens()` call from `start()` (line 661)
- Remove `on_ready` lambda from `_boot()` (line 644)

#### Change 11: Update `run()` to use unified wait

Replace the `ws_ready` asyncio.Event logic in `run()` (lines 854-857, 872-880):
```python
async def _run() -> None:
    await self._server.start(
        lambda scene_name: (...),
        self._config.to_dict,
        control_callback=self._dispatch_control_event,
        on_connect=self._on_client_connect,
        scene_config_callback=self._scene_config_for,
        scene_list_callback=self.list_scenes,
    )
    if self._open_browser:
        import secrets
        page_token = secrets.token_hex(4)
        if self._reuse_existing:
            reconnected = await self._server.wait_for_ws_ready(timeout=3.0)
            if not reconnected:
                print("No existing browser reconnected — opening new tab.")
                self._server.open_browser(f"/?token={page_token}")
        else:
            self._server.open_browser(f"/?token={page_token}")
        
        if wait_for_browser:
            try:
                await asyncio.wait_for(
                    self._server.wait_for_ws_ready(), timeout=30.0
                )
            except asyncio.TimeoutError:
                self._print_ws_timeout_note()
                raise RuntimeError(...)
    # ... rest unchanged
```

### File: `py/pytanga/viz/templates/viewer.js`

#### Change 12: Fallback page_token from URL query param

In `connectWebSocket()` (line 160), change:
```javascript
if (window.__tanga_page_token) readyPayload.page_token = window.__tanga_page_token;
```
To:
```javascript
const pageToken = window.__tanga_page_token
    || new URLSearchParams(window.location.search).get('token');
if (pageToken) readyPayload.page_token = pageToken;
```

## Summary of Removals

| Remove | Reason |
|--------|--------|
| `_ws_ready_event` (threading.Event) | Replaced by `server._any_ws_ready` |
| `_wait_for_client_quiet()` | Replaced by `server.wait_for_ws_ready()` |
| `_print_connect()` | Dead code — never called |
| `check_page_tokens()` call in `start()` | No longer part of startup flow |
| `on_ready` lambda in `_boot()` | Server sets `_any_ws_ready` before calling `_on_ready` |

## Summary of Additions

| Add | Purpose |
|-----|---------|
| `VizServer._any_ws_ready` (asyncio.Event) | Single event for "any browser ready" |
| `VizServer.wait_for_ws_ready()` | Unified async wait method |
| `secrets.token_hex(4)` in `start()`/`run()` | Generate token for new tabs |
| Token via `?token=` URL query param | Correlate new tabs with visualizer |
| `viewer.js` URL token fallback | Client reads token from URL |
| try/except around push ops in ready handler | Exception doesn't block `_on_ready` |