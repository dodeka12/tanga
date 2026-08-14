# Fix: WebSocket Reconnect Hangs on Windows (Stuck CONNECTING Socket)

## Problem

The Tanga viewer reconnects reliably on Linux, but on Windows (observed with
Firefox 140) the reconnect flow degrades badly:

- First browser window for a fresh run: scene displays correctly.
- After waiting a while, opening a new run does **not** reconnect.
- Clicking **Reconnect** several times produces no server reaction.
- The button eventually degrades to **↻ Reload**, but reloading still shows
  nothing.
- Roughly **45s later** the connection is finally registered by the server and
  the scene appears.

Backend log shows the connection only registers after ~46s:

```
INFO:tanga.viz.server:HTTP GET / → serving viewer.html (token=8b075020) → 127.0.0.1
INFO:tanga.viz.server:WS connect from 127.0.0.1
INFO:tanga.viz.server:WS ready: id=9447f020 token=8b075020 ...
INFO:tanga.viz:Browser reconnected after 46.3s
```

The user also reports the timing dependence:

> when I restart the python server quickly after the first run, then reconnect
> works immediately. If I wait longer it does not.

## Root Cause

The JS reconnect button **does** reset the backoff delay
(`_reconnectDelay = _RECONNECT_BASE_MS`) before calling `connectWebSocket()`,
but `connectWebSocket()` overwrites the global `ws` without first closing the
previous socket:

```javascript
ws = new WebSocket(url);   // old `ws` is never closed
```

Why this bites on Windows and not Linux:

1. After script 1 exits, the browser's exponential backoff grows
   `1s → 2s → 4s → … → 30s`. After extended idle the browser is sleeping in a
   30s backoff, so there is no immediate retry — hence "quick restart works,
   slow restart doesn't."

2. When a reconnect does fire (backoff timer or manual click), a new
   `WebSocket` is created. On Windows/Firefox a WebSocket connect to a
   `localhost:8765` that just changed state can hang in `CONNECTING` for ~45s
   instead of failing fast (half-open TCP socket / connect-timeout after the
   previous run's connection was torn down abruptly).

3. Because the old socket is never closed, orphaned sockets accumulate stuck in
   `CONNECTING`. Firefox queues subsequent `new WebSocket()` attempts to the
   same host behind them. Manual clicks (and automatic retries) pile into the
   queue and nothing reaches the server — "click registers, server doesn't
   react."

4. Reloading resets the connection pool, but the first reload can still inherit
   the half-open socket; that's why it takes **two** reloads before the stuck
   socket clears and the WS connects.

The 46.3s delay is **not** a server-side poll delay (`wait_for_browser()` polls
every 0.2s). It is the browser's stuck `CONNECTING` socket timing out.

### Contributing server-side factors

- No WebSocket heartbeat / receive timeout, so dead or half-open connections
  are never proactively torn down.
- Default `host="localhost"` can resolve to `::1` (IPv6) while the display URL
  says `localhost`, and `reuse_address=True` has weaker semantics on Windows
  than on Unix (`SO_REUSEADDR` there permits port hijacking/misdelivery).

## Desired Behavior

1. **Single-flight reconnect** — only one WebSocket connect attempt is ever in
   flight; the previous socket is torn down before starting a new one.
2. **Connect watchdog** — a stuck `CONNECTING` socket is aborted after a short
   timeout and retried, instead of blocking for ~45s.
3. **Stale handler suppression** — `onopen`/`onclose` handlers from superseded
   sockets never run, so they cannot clobber the backoff delay or status.
4. **Manual click truly cancels** the current attempt, clearing the stuck
   socket rather than queueing behind it.
5. **Deterministic localhost binding** — bind to `127.0.0.1` on Windows/Unix to
   avoid IPv4/IPv6 ambiguity, while keeping `localhost` in displayed URLs.
6. **Server detects dead sockets** via a receive heartbeat timeout.
7. **Traceable connection lifecycle** — structured, timestamped console
   logging in the browser and parallel backend logging so reconnect state and
   transitions can be pinpointed after the fact.

---

## Implementation Plan

### Ordering rationale

Steps are ordered so each one touches a disjoint slice of code, and a later
step never has to revise an earlier step's implementation:

1. Introduce the standalone reconnect primitives and the logging helper first
   (no callers touch them yet).
2. Rewrite `connectWebSocket()` once — folding the single-flight guard, the
   connect watchdog, and all of its `_log` call sites into that single pass.
3. Update the two independent event handlers (visibility + manual click).
4. Update `VizServer.start()` once — combining the IPv4 bind and the
   `reuse_address` gating, since both live in the same method.
5. Rewrite `_ws_handler()` once — folding the heartbeat and all
   connection-lifecycle logging into that single pass.
6. Add logging to the independent `_clear_ws_ready_events()` method.

This ordering avoids the trap where "add logging" was a separate later change
that re-touches the function bodies built in earlier steps — logging is now
introduced inline in the same step that builds each function.

---

### [x] Step 1 — `py/pytanga/viz/templates/viewer.js`: reconnect primitives + logging helper

Add after `_reconnectDelay` (~line 135):

```javascript
// Single-flight guard: increment on teardown so stale onopen/onclose
// handlers from superseded sockets are ignored.
let _wsGeneration = 0;
```

Add after `let _reconnectClickCount = 0;` (~line 217):

```javascript
function _log(phase, detail) {
    const parts = ['[tanga:' + phase + ']'];
    if (_browserId) parts.push('id=' + _browserId);
    if (_viewerName) parts.push('viewer=' + _viewerName);
    if (_myScene) parts.push('scene=' + _myScene);
    if (detail) parts.push(detail);
    console.log(parts.join(' '));
}
```

Add before `connectWebSocket`:

```javascript
function closeActiveWs() {
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
        _log('ws-teardown', 'closing readyState=' + ws.readyState);
        _wsGeneration++;                          // invalidate stale handlers
        const old = ws;
        old.onopen = old.onclose = old.onerror = old.onmessage = null;
        try { old.close(); } catch (_) {}
    }
    ws = null;
}
```

### [x] Step 2 — `viewer.js`: single-flight `connectWebSocket` + watchdog + inline logging

Rewrite `connectWebSocket()` once (all `_log` calls and the watchdog are
introduced here, so no later step re-touches this function):

```javascript
function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${location.host}/ws`;

    closeActiveWs();
    const gen = _wsGeneration;

    _reconnectAttempts++;
    updateStatusIndicator('connecting', _reconnectAttempts);
    document.title = 'Connecting… — ' + _savedTitle;
    _log('ws-connect', 'url=' + url + ' attempt=' + _reconnectAttempts);

    ws = new WebSocket(url);

    const connectWatchdog = setTimeout(() => {
        if (ws && ws.readyState === WebSocket.CONNECTING && gen === _wsGeneration) {
            _log('ws-watchdog', 'connect timed out — aborting and retrying');
            _wsGeneration++;               // invalidate this socket's handlers
            try { ws.close(); } catch (_) {}
            ws = null;
            connectWebSocket();            // retry immediately
        }
    }, 5000);

    ws.onopen = () => {
        if (gen !== _wsGeneration) return;
        clearTimeout(connectWatchdog);
        const pageToken = window.__tanga_page_token
            || new URLSearchParams(window.location.search).get('token');
        _log('ws-open', 'attempt=' + _reconnectAttempts
            + ' token=' + (pageToken || 'none'));
        setStatus('connected');
        setWebSocket(ws);
        setInteractionWebSocket(ws);
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        _reconnectAttempts = 0;
        _reconnectDelay = _RECONNECT_BASE_MS;
        hideReconnectButton();
        updateStatusIndicator('connected');
        document.title = _savedTitle;
        const readyPayload = { type: 'ready', scene: _myScene };
        if (_browserId) readyPayload.browser_id = _browserId;
        if (_viewerName) readyPayload.viewer_name = _viewerName;
        if (pageToken) readyPayload.page_token = pageToken;
        ws.send(JSON.stringify(readyPayload));
    };

    ws.onmessage = (event) => {
        let msg;
        try {
            msg = JSON.parse(event.data);
        } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
            return;
        }
        _log('ws-msg', 'type=' + (msg.type || 'unknown'));
        handleMessage(msg);
    };

    ws.onclose = (event) => {
        if (gen !== _wsGeneration) return;
        clearTimeout(connectWatchdog);
        _log('ws-close', 'code=' + event.code
            + ' reason=' + (event.reason || 'none'));
        setStatus('disconnected');
        updateStatusIndicator('disconnected');
        document.title = 'Disconnected — ' + _savedTitle;

        const jitter = 0.8 + Math.random() * 0.4;  // ±20%
        const delay = Math.round(Math.min(_reconnectDelay * jitter, _RECONNECT_MAX_MS));
        _log('ws-reconnect', 'delay=' + delay + 'ms backoff=' + _reconnectDelay + 'ms');
        _reconnectDelay = Math.min(_reconnectDelay * 2, _RECONNECT_MAX_MS);
        reconnectTimer = setTimeout(connectWebSocket, delay);
    };

    ws.onerror = () => { /* onclose will fire next */ };
}
```

(Note: the original `onmessage` parsed inline; exporting the parse to a local
`msg` variable is only needed to emit the `ws-msg` log before `handleMessage`.)

### [x] Step 3 — `viewer.js`: manual click + visibility handlers

In the reconnect button click handler (~line 271), before
`_reconnectDelay = _RECONNECT_BASE_MS; connectWebSocket();` add:

```javascript
closeActiveWs();
_log('ws-manual', 'reconnect click=' + _reconnectClickCount);
```

In the `visibilitychange` handler (~line 203), inside the visible branch,
before `connectWebSocket();` add:

```javascript
_log('ws-visibility', 'tab visible — immediate reconnect');
```

### [x] Step 4 — `py/pytanga/viz/server.py`: `VizServer.start()` IPv4 bind + `reuse_address` gating

Add `import sys` to the module imports. In `start()`, replace the `TCPSite`
construction with a platform-aware bind:

```python
bind_host = "127.0.0.1" if self._host == "localhost" else self._host
reuse_address = sys.platform != "win32"
self._site = web.TCPSite(
    self._runner, bind_host, self._port, reuse_address=reuse_address
)
```

> `SO_REUSEADDR` on Windows allows a second bind to succeed while the first is
> still holding the port with active connections, which can route traffic to the
> wrong process — so it is disabled on Windows. The display URL (`.url`) still
> prints `localhost`, keeping the existing UX.

### [x] Step 5 — `server.py`: `_ws_handler` heartbeat + lifecycle logging

Rewrite the relevant portions of `_ws_handler()` in one pass (the heartbeat and
all connection-lifecycle logging live in this one function):

- After `ws.prepare` and adding to `_ws_clients`:
  ```python
  logger.info(
      "WS connect from %s (total_clients=%d, sessions=%d)",
      remote_addr, len(self._ws_clients), len(self._browser_sessions),
  )
  ```
- After assigning the session id:
  ```python
  logger.debug("WS session assigned id=%s remote=%s", browser_id, remote_addr)
  ```
- Define a heartbeat helper (module-level or nested):
  ```python
  async def _heartbeat(ws, interval=15.0):
      try:
          while not ws.closed:
              await asyncio.sleep(interval)
              await ws.ping()
      except (ConnectionError, Exception):
          pass
  ```
  Start it after the session is assigned, and store the task:
  ```python
  heartbeat_task = asyncio.create_task(_heartbeat(ws))
  logger.debug("WS heartbeat started id=%s", browser_id)
  ```
- Inside the `TEXT` branch, add a per-message trace:
  ```python
  logger.debug(
      "WS msg: %s from %s (id=%s)", msg_type, remote_addr, msg_browser_id
  )
  ```
- On `ready`, extend the existing summary (and note the ready signal):
  ```python
  logger.info(
      "WS ready: id=%s token=%s viewer=%s scene=%s remote=%s "
      "sessions=%d pending_tokens=%d — signalling ready",
      msg_browser_id, page_token or "reconnect",
      data.get("viewer_name") or "none", scene_name, remote_addr,
      len(self._browser_sessions), len(self._pending_page_tokens),
  )
  ```
- In the `finally` block, cancel the heartbeat and enrich disconnect logging:
  ```python
  heartbeat_task.cancel()
  logger.debug("WS heartbeat stopped id=%s", browser_id)
  logger.info(
      "WS disconnect from %s (id=%s, sessions_remaining=%d)",
      remote_addr, browser_id, len(self._browser_sessions) - 1,
  )
  ```

### [x] Step 6 — `server.py`: `_clear_ws_ready_events` logging

In `_clear_ws_ready_events()`, log the gate transition:

```python
logger.debug("Clearing WS ready events (was_ready=%s)",
             self._any_ws_ready.is_set())
```

---

## Verification Checklist (Windows)

- [ ] Run script 1 to completion, wait 30+ seconds, start script 2 → old tab
      reconnects within ~5-10s.
- [ ] During reconnect, browser console shows at most one in-flight WebSocket.
- [ ] Clicking **Reconnect** once immediately reconnects (no double reload).
- [ ] Browser console shows a connect-timeout abort and retry if a socket
      hangs in `CONNECTING`.
- [ ] No stale `onopen`/`onclose` handlers reset the status/backoff after a
      superseded socket closes.
- [ ] Server log shows rapid `WS connect` → `WS ready` once the socket actually
      reaches the server.
- [ ] Browser console shows a structured `[tanga:ws-connect]` →
      `[tanga:ws-open]` (or `[tanga:ws-watchdog]`) transcript for every
      reconnect attempt, with browser/viewer/scene identity.
- [ ] Server log shows `WS connect` (with `total_clients`/`sessions`) →
      `WS msg: ready` → `WS ready` (with `pending_tokens` and the signalling
      note), matching the browser transcript.
- [ ] Server log shows `WS disconnect` with `sessions_remaining` plus heartbeat
      start/stop lines.
- [ ] Linux behavior remains unchanged (no regressions in reconnect timing).