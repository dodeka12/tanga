# Phase 1 — `HostRuntime` + `OverlayHost` base; extract `BannerHost`

## Goal

Introduce the shared host plumbing and move the banner lifecycle out of
`Visualizer`, proving the pattern on the smallest self-contained host.

## Files

- New: `py/pytanga/viz/_hosts.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_banner.py` (add a direct `BannerHost` unit test)

## Steps

- [x] **1.1 — `HostRuntime` + `OverlayHost` (`_hosts.py`)**
  - `@dataclass HostRuntime`: `server`, `loop`,
    `registry: ControlHandlerRegistry`, `on_server_loop(coro_factory) ->
    Awaitable`, and `push_message(dict) -> None` (guarded
    `run_coroutine_threadsafe(push_raw(json.dumps(...)), loop)`).
  - `class OverlayHost` holding `self.runtime`; helper `_push(message: dict)`.

- [x] **1.2 — `BannerHost(OverlayHost)`**
  - Move `_banners`, `_banner_counter`, `_next_banner_id`, `_register_banner`,
    `_unregister_banner`, `show_banner`, `alert`, `confirm`, `remove_banner`,
    `clear_banners`, `_push_banner*`, and the `*_async` variants into it.
  - Add `async _on_close(target, value, event)`: lookup `(target, "close")`,
    unregister, and await it (the `banner_closed`/`close` branch today).

- [x] **1.3 — Wire `Visualizer`**
  - `__init__`: build a `HostRuntime` from `self` and
    `self._banner_host = BannerHost(runtime)`.
  - Replace `show_banner`/`alert`/`confirm`/`remove_banner`/`clear_banners`
    (+ async) bodies with one-line forwarders to `self._banner_host`.
  - Keep `viz._banners` / `_banner_counter` as delegating properties.
  - Route the `banner_closed`/`close` (banner) branch of `_dispatch_control_event`
    to `self._banner_host._on_close(...)`.

- [x] **1.4 — Tests**
  - `test_banner.py` passes unchanged; add a direct `BannerHost` test
    (register → push → close → unregister).

## Validation

`uv run pytest py/tests/viz/test_banner.py py/tests/viz/test_editor.py -q`

## Notes

- `_on_server_loop`, `_server`, `_loop`, and `_handler_registry` stay on
  `Visualizer` and are exposed to hosts through the `HostRuntime`.
