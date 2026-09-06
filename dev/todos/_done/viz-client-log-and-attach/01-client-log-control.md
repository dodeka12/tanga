# Phase 1 — Backend `ClientLog` control model

## Goal

Add the backend-only `ClientLogRecord` + `ClientLog(Control)` classes and the
default sink, so later phases have a concrete control to route log events into.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- New: `py/tests/viz/test_client_log.py`

## Steps

- [x] **1.1 — `CLIENT_LOG_ID` constant + `ClientLogRecord`**
  - In `_controls.py`, add `CLIENT_LOG_ID = "client_log"`.
  - Add `@dataclass ClientLogRecord` with `level: str`, `message: str`,
    `source: str | None = None`, `data: dict[str, Any] | None = None`,
    `browser_id: str | None = None`.

- [x] **1.2 — `_default_client_log_sink(record, event)`**
  - Module-level `async def` that maps `record.level` → the
    `logging.getLogger("tanga.viz.client")` method per the README level mapping
    (unknown → `logger.warning`), and logs `message` with `source`, `browser_id`,
    and `data` as context.

- [x] **1.3 — `ClientLog(Control)`**
  - `kind: str = "client_log"`, `on_log: Handler = _default_client_log_sink`.
  - Override `handle_event(self, event, payload) -> Dispatch` to parse
    `level/message/source/data/browser_id` into a `ClientLogRecord` and return
    `Dispatch("log", record)`.
  - Do **not** add a new `id` field — inherit the required `id` from `Control`
    (the `Visualizer` will pass `CLIENT_LOG_ID`). Do **not** override
    `register_handlers`; the inherited version maps `on_log` → `("id", "log")`.
  - Add a one-line class docstring: backend-only, never serialized.

- [x] **1.4 — Unit tests (`test_client_log.py`)**
  - `handle_event("log", payload)` returns `Dispatch("log", record)` with
    `record.level/message/source/data/browser_id` populated (and defaults when
    omitted).
  - `register_handlers` registers a callable under `(CLIENT_LOG_ID, "log")`.
  - `_default_client_log_sink` logs at the mapped level (assert via `caplog`):
    `debug/info/warn/error` and one unknown level → `warning`.

## Validation

`uv run pytest py/tests/viz/test_client_log.py -q`

## Notes

- Import `ClientLogRecord`, `ClientLog`, `CLIENT_LOG_ID` from `_controls` in the
  test. Reuse `ControlHandlerRegistry` (or a minimal fake transport with a
  `register`/`get` pair) to assert handler registration without a server.
