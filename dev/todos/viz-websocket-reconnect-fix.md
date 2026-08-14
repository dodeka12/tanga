# Fix: WebSocket Reconnect Logic — Exponential Backoff, Thread Safety, and Interactive Wait

## Problem

When a Tanga backend script ends and a new one starts:

1. The old browser tab's JS reconnect loop (`setTimeout(connectWebSocket, 800)` — viewer.js:181)
   never backs off. After extended idle time, browsers throttle `setTimeout` in background
   tabs to run as infrequently as once per 60 seconds.
2. The new server waits **only 5 seconds** for an existing browser to reconnect — and if the
   throttled reconnect timer hasn't fired yet, it opens a **new tab**.
3. Both old and new tabs eventually connect. The `_push_full_state` to both tabs is actually
   safe (asyncio is single-threaded within the event loop). The real **hang** comes from a
   **thread-safety bug**: `_any_ws_ready.clear()` (visualizer.py:764, 769, 1006, 1010) is
   called from the **main thread** on an `asyncio.Event` object. This is undefined behavior
   and can corrupt the event loop state — exactly the "everything hangs" symptom.
4. There is no user-visible "Reconnect" button — the user has to manually refresh the page.
5. The fixed 5-second wait is too rigid: if the old browser tab takes 6 seconds to reconnect,
   the user gets a duplicate tab with no recourse.

## Desired Behavior

1. **Exponential backoff** in the JS reconnect loop: start at ~1s, cap at ~30s, with jitter.
   No fixed 800ms.
2. **Visibility wake-up**: when the browser tab becomes visible again, cancel any pending
   reconnect timer and try to reconnect **immediately**.
3. **Reconnect button** in the top-right status area, visible when disconnected.
   Clicking it resets the backoff and triggers an immediate reconnect.
   After 3 consecutive failed clicks, shows a "↻ Reload" button instead.
4. **Interactive wait on the backend**: instead of a fixed 5s timeout, the backend prints:
   > Press Enter to open a new browser tab, or click "Reconnect" in an open tab…
   and waits **indefinitely** until either:
   - A browser reconnects (→ continue, no new tab), **OR**
   - The user presses Enter (→ open new tab and wait for it to connect).
   Ctrl+C cancels the wait cleanly.
5. **Thread-safe event clearing** — use `loop.call_soon_threadsafe()` instead of direct
   `.clear()` calls on `asyncio.Event` objects. Use a companion `threading.Event` so the
   main thread can reliably check whether a browser has connected.
6. **No "superseded" or "shutdown" close codes** — the server should NOT prevent tabs from
   reconnecting. When a new script starts, the old tab reconnecting is the **primary**
   desired workflow. If a second tab happens to be open, both get `clear_all` + fresh state.
7. **Enhanced logging** throughout so the reconnect flow is traceable.

---

## Implementation Plan

### File 1: `py/pytanga/viz/templates/viewer.js`

#### Change 1.1: Replace fixed reconnect delay with exponential backoff

At the top of the WebSocket client section (around line 133), add:

```javascript
// Reconnect backoff
const _RECONNECT_BASE_MS = 1000;
const _RECONNECT_MAX_MS = 30000;
let _reconnectDelay = _RECONNECT_BASE_MS;
```

In `connectWebSocket` → `onopen`, reset the delay (around line 159):

```javascript
_reconnectDelay = _RECONNECT_BASE_MS;
```

In `connectWebSocket` → `onclose`, use exponential backoff (around line 177):

```javascript
ws.onclose = (event) => {
    console.warn('[tanga] WS closed (code=' + event.code + '), reason=' + (event.reason || 'none'));
    setStatus('disconnected');
    updateStatusIndicator('disconnected');
    document.title = 'Disconnected — ' + _savedTitle;

    const jitter = 0.8 + Math.random() * 0.4;  // ±20%
    const delay = Math.round(Math.min(_reconnectDelay * jitter, _RECONNECT_MAX_MS));
    _reconnectDelay = Math.min(_reconnectDelay * 2, _RECONNECT_MAX_MS);
    console.log('[tanga] Reconnecting in ' + delay + 'ms (backoff=' + _reconnectDelay + 'ms)');
    reconnectTimer = setTimeout(connectWebSocket, delay);
};
```

#### Change 1.2: Add visibility change listener

Insert after `updateStatusIndicator` function (around line 219):

```javascript
// ── Visibility wake-up ────────────────────────────────────────
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && ws === null) {
        console.log('[tanga] Tab became visible — triggering immediate reconnect');
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        _reconnectDelay = _RECONNECT_BASE_MS;
        connectWebSocket();
    }
});
```

#### Change 1.3: Add reconnect button

Add after the visibility listener:

```javascript
// ── Reconnect Button ──────────────────────────────────────────
let _reconnectButtonEl = null;
let _reconnectClickCount = 0;

function showReconnectButton(mode) {
    // mode: 'reconnect' (normal reconnect) or 'page-reload' (full refresh)
    if (_reconnectButtonEl) {
        _reconnectButtonEl.remove();
        _reconnectButtonEl = null;
    }

    _reconnectButtonEl = document.createElement('button');
    _reconnectButtonEl.id = 'tanga-reconnect-btn';
    _reconnectButtonEl.style.position = 'fixed';
    _reconnectButtonEl.style.top = '6px';
    _reconnectButtonEl.style.right = '28px';
    _reconnectButtonEl.style.padding = '2px 8px';
    _reconnectButtonEl.style.fontSize = '11px';
    _reconnectButtonEl.style.fontFamily = 'sans-serif';
    _reconnectButtonEl.style.color = '#fff';
    _reconnectButtonEl.style.background = 'rgba(255,255,255,0.15)';
    _reconnectButtonEl.style.border = '1px solid rgba(255,255,255,0.3)';
    _reconnectButtonEl.style.borderRadius = '3px';
    _reconnectButtonEl.style.cursor = 'pointer';
    _reconnectButtonEl.style.zIndex = '11';
    _reconnectButtonEl.style.transition = 'background 0.2s';

    _reconnectButtonEl.addEventListener('mouseenter', () => {
        _reconnectButtonEl.style.background = 'rgba(255,255,255,0.25)';
    });
    _reconnectButtonEl.addEventListener('mouseleave', () => {
        _reconnectButtonEl.style.background = 'rgba(255,255,255,0.15)';
    });

    if (mode === 'page-reload') {
        _reconnectButtonEl.textContent = '↻ Reload';
        _reconnectButtonEl.title = 'Reconnect failed — reload page';
        _reconnectButtonEl.addEventListener('click', () => {
            window.location.reload();
        });
    } else {
        _reconnectButtonEl.textContent = 'Reconnect';
        _reconnectButtonEl.title = 'Click to reconnect immediately';
        _reconnectButtonEl.addEventListener('click', () => {
            _reconnectClickCount++;
            if (_reconnectClickCount >= 3) {
                console.log('[tanga] 3 reconnect attempts without success — offering page reload');
                showReconnectButton('page-reload');
                return;
            }
            console.log('[tanga] Manual reconnect requested (click ' + _reconnectClickCount + ')');
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
            _reconnectDelay = _RECONNECT_BASE_MS;
            connectWebSocket();
        });
    }

    document.body.appendChild(_reconnectButtonEl);
}

function hideReconnectButton() {
    if (_reconnectButtonEl) {
        _reconnectButtonEl.remove();
        _reconnectButtonEl = null;
    }
    _reconnectClickCount = 0;
}
```

#### Change 1.4: Wire reconnect button into `updateStatusIndicator`

Update `updateStatusIndicator` (around line 194):

```javascript
function updateStatusIndicator(state, attempts) {
    const el = document.getElementById('status');
    if (!el) return;
    if (state === 'connected') {
        el.className = 'connected';
        hideReconnectButton();
    } else {
        el.className = 'disconnected';
        if (!_reconnectButtonEl) {
            showReconnectButton('reconnect');
        }
    }

    let labelEl = document.getElementById('status-label');
    if (state === 'connecting' && attempts > 0) {
        if (!labelEl) {
            labelEl = document.createElement('span');
            labelEl.id = 'status-label';
            labelEl.style.position = 'fixed';
            labelEl.style.top = '8px';
            labelEl.style.right = '26px';
            labelEl.style.color = '#888';
            labelEl.style.fontFamily = 'sans-serif';
            labelEl.style.fontSize = '11px';
            labelEl.style.pointerEvents = 'none';
            labelEl.style.zIndex = '11';
            document.body.appendChild(labelEl);
        }
        labelEl.textContent = 'attempt ' + attempts;
        labelEl.style.display = '';
    } else if (labelEl) {
        labelEl.style.display = 'none';
    }
}
```

#### Change 1.5: Reset reconnect button on `onopen`

In `connectWebSocket` → `onopen`, also call `hideReconnectButton()`:

```javascript
ws.onopen = () => {
    // ... existing code ...
    _reconnectDelay = _RECONNECT_BASE_MS;
    hideReconnectButton();
    // ... rest of existing onopen ...
};
```

#### Change 1.6: Enhanced console logging

All key points already covered:
- `connectWebSocket()` calls
- `visibilitychange` trigger
- Reconnect button clicks
- WS close with code/reason
- Backoff delay calculation

---

### File 2: `py/pytanga/viz/server.py`

#### Change 2.1: Add `_any_ws_ready_thread` threading.Event mirror

In `__init__`, add alongside `_any_ws_ready` (after line 79):

```python
import threading
self._any_ws_ready_thread: threading.Event = threading.Event()
```

#### Change 2.2: Mirror set/clear on `_any_ws_ready_thread`

In `_ws_handler`, when `_any_ws_ready.set()` is called (around line 442), also set the
threading mirror:

```python
self._any_ws_ready.set()
self._any_ws_ready_thread.set()  # thread-safe mirror for the main thread
```

Add a helper method to clear both events safely (called from the event loop):

```python
def _clear_ws_ready_events(self) -> None:
    """Clear both the asyncio.Event and its threading mirror.

    Must be called from the event loop.
    """
    self._any_ws_ready.clear()
    self._any_ws_ready_thread.clear()
    self._ws_error_event.clear()
```

#### Change 2.3: Enhanced logging in `_ws_handler`

In the `ready` message handler (around line 388), enhance logging:

```python
if msg_type == "ready":
    scene_name = data.get("scene", "")
    page_token = data.get("page_token")
    if page_token:
        self._pending_page_tokens.pop(page_token, None)
    logger.info(
        "WS ready: id=%s token=%s viewer=%s scene=%s remote=%s sessions=%d",
        msg_browser_id,
        page_token or "reconnect",
        data.get("viewer_name") or "none",
        scene_name,
        remote_addr,
        len(self._browser_sessions),
    )
    # ... rest of ready handling ...
```

In the `finally` block of `_ws_handler`, enhance disconnect logging:

```python
logger.info(
    "WS disconnect from %s (id=%s, sessions_remaining=%d)",
    remote_addr,
    browser_id,
    len(self._browser_sessions) - 1,
)
```

---

### File 3: `py/pytanga/viz/visualizer.py`

#### Change 3.1: Replace `wait_for_browser()` with interactive wait

The `wait_for_browser()` method (around line 838) is replaced with an interactive version
that prompts the user rather than using a fixed 5-second timeout:

```python
def wait_for_browser(self, timeout: float = 30.0) -> bool:
    """Block until a browser connects or the user opens one interactively.

    Prints a prompt:
      "Press Enter to open a new browser tab, or click 'Reconnect' in
       an open tab…"

    Returns True if a browser connected, False if cancelled by user
    (Ctrl+C) or on timeout.
    """
    if self._server is None or self._loop is None:
        raise RuntimeError("Server not started. Call start() first.")

    # ── Check if already connected ──
    if self._server._any_ws_ready_thread.is_set():
        logger.info("Browser already connected")
        return True

    # ── Print interactive prompt ──
    try:
        from rich.console import Console
        from rich.text import Text

        console = Console()
        url_text = Text(self._server.url, style="bold cyan")
        console.print(
            Text.assemble(
                "Press ", Text("Enter", style="bold"),
                " to open a new browser tab, or click ",
                Text("'Reconnect'", style="bold"),
                " in an existing tab…",
            )
        )
    except ImportError:
        print(
            f"Press Enter to open a new browser tab at {self._server.url}, "
            f"or click 'Reconnect' in an existing tab…"
        )

    # ── Threading.Event for Enter press ──
    enter_pressed = threading.Event()
    enter_thread: threading.Thread | None = None
    shutdown = getattr(self, '_shutdown_requested', threading.Event())

    def _wait_for_enter() -> None:
        try:
            input()
            enter_pressed.set()
        except (EOFError, KeyboardInterrupt):
            pass

    enter_thread = threading.Thread(target=_wait_for_enter, daemon=True)
    enter_thread.start()

    # ── Poll loop ──
    start_ts = time.monotonic()
    poll_interval = 0.2

    try:
        while time.monotonic() - start_ts < timeout:
            if self._server._any_ws_ready_thread.is_set():
                logger.info("Browser reconnected after %.1fs",
                            time.monotonic() - start_ts)
                return True
            if enter_pressed.is_set():
                logger.info("User pressed Enter — opening new tab")
                break
            if shutdown.is_set():
                logger.info("Shutdown requested during wait")
                return False
            time.sleep(poll_interval)
    finally:
        # Clean up the input thread — it's a daemon, but if the user
        # hasn't pressed Enter yet, the thread will linger until process exit.
        pass

    # ── User chose to open a new tab ──
    page_token = secrets.token_hex(4)
    logger.info("Opening new tab with token=%s", page_token)

    # Thread-safe clear
    if self._loop is not None:
        self._loop.call_soon_threadsafe(self._server._clear_ws_ready_events)

    self._server.open_browser(f"/?token={page_token}")

    # Now wait for the new tab to connect (with fixed timeout)
    logger.info("Waiting up to %.0fs for new tab to connect…", timeout)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if self._server._any_ws_ready_thread.is_set():
            elapsed = time.monotonic() - start_ts
            logger.info("New tab connected after %.1fs", elapsed)
            return True
        if shutdown.is_set():
            logger.info("Shutdown requested during tab wait")
            return False
        time.sleep(poll_interval)

    logger.warning("No browser connected within %.0fs after opening tab", timeout)
    self._print_ws_timeout_note()
    return False
```

#### Change 3.2: Update `start()` — use interactive wait

Replace the `_reuse_existing` / `wait_for_browser` logic in `start()` (around lines 745-775):

```python
if self._open_browser:
    page_token = secrets.token_hex(4)
    if self._reuse_existing:
        logger.info(
            "Server ready at %s — checking for existing browser…",
            self._server.url,
        )
        # Interactive wait: user either clicks Reconnect or presses Enter
        if wait_for_browser:
            connected = self.wait_for_browser(timeout=120.0)
            if not connected:
                return False
        else:
            # Non-blocking: just see if one is already there
            fut = asyncio.run_coroutine_threadsafe(
                self._server.wait_for_ws_ready(timeout=3.0), self._loop
            )
            try:
                reconnected = fut.result(timeout=3.5)
            except (concurrent.futures.TimeoutError, asyncio.TimeoutError):
                reconnected = False
            if not reconnected:
                if self._loop is not None:
                    self._loop.call_soon_threadsafe(
                        self._server._clear_ws_ready_events
                    )
                self._server.open_browser(f"/?token={page_token}")
    else:
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._server._clear_ws_ready_events)
        self._server.open_browser(f"/?token={page_token}")
        if wait_for_browser:
            return self.wait_for_browser(timeout=30.0)
```

#### Change 3.3: Update `run()` — interactive wait

Replace the browser-opening logic in `_run()` (around lines 994-1024):

```python
if self._open_browser:
    page_token = secrets.token_hex(4)
    if self._reuse_existing:
        logger.info("Server ready at %s — checking for existing browser…", self._server.url)

        # Async interactive wait: race ws_ready against stdin read
        if wait_for_browser:
            import sys
            enter_task = asyncio.create_task(
                asyncio.to_thread(sys.stdin.readline)
            )
            ws_task = asyncio.create_task(
                self._server.wait_for_ws_ready()
            )

            # Print prompt
            try:
                from rich.console import Console
                from rich.text import Text
                Console().print(
                    Text.assemble(
                        "Press ", Text("Enter", style="bold"),
                        " to open a new browser tab, or click ",
                        Text("'Reconnect'", style="bold"),
                        " in an existing tab…",
                    )
                )
            except ImportError:
                print(
                    f"Press Enter to open a new browser tab at {self._server.url}, "
                    f"or click 'Reconnect' in an existing tab…"
                )

            done, pending = await asyncio.wait(
                [enter_task, ws_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()

            if ws_task in done:
                logger.info("Browser reconnected")
                connected = True
            else:
                logger.info("User pressed Enter — opening new tab")
                self._server._clear_ws_ready_events()
                self._server.open_browser(f"/?token={page_token}")
                try:
                    await asyncio.wait_for(
                        self._server.wait_for_ws_ready(), timeout=30.0
                    )
                    connected = True
                except asyncio.TimeoutError:
                    self._print_ws_timeout_note()
                    raise RuntimeError(
                        "No browser connected within 30s.  "
                        f"Open {self._server.url} manually."
                    )
            # Ensure enter_task is cleaned up
            try:
                await enter_task
            except (asyncio.CancelledError, Exception):
                pass
```

---

### File 4: `py/pytanga/viz/templates/viewer.html`

**No changes required.** The reconnect button is positioned with its own CSS alongside the
existing `#status` dot. The status dot remains `pointer-events: none` so it doesn't
interfere with button clicks.

---

## Summary of Changes

| File | Changes |
|------|---------|
| `viewer.js` | Exponential backoff with jitter, visibility wake-up, reconnect/reload button, enhanced console logging |
| `server.py` | `_any_ws_ready_thread` threading.Event mirror, `_clear_ws_ready_events()` helper, enhanced logging in `_ws_handler` |
| `visualizer.py` | Interactive `wait_for_browser()` (Enter or Reconnect), thread-safe `_clear_ws_ready_events()` in `start()`, async stdin race in `run()` |
| `viewer.html` | No changes needed |

---

## Testing Checklist

- [ ] Start a script, wait for browser, close script → browser shows "Disconnected" + "Reconnect" button
- [ ] Start a new script → prompt appears: "Press Enter to open a new browser tab, or click 'Reconnect' in an existing tab…"
- [ ] Click "Reconnect" in the old browser tab → backend detects connection, continues (no new tab)
- [ ] Press Enter instead → new tab opens with token, connects, backend continues
- [ ] Switch old browser tab to background, wait 30s, switch back → reconnects immediately (visibility wake-up)
- [ ] Click "Reconnect" 3 times without success → button changes to "↻ Reload"
- [ ] Ctrl+C during the interactive wait → clean shutdown, no hang
- [ ] Exponential backoff: console logs show 1s, 2s, 4s, 8s, 16s, 30s, 30s… reconnect intervals
- [ ] Console logs clearly show token, browser_id, reconnect vs new-tab decisions