# Phase 3 — Custom-enum options route

## Goal

Wire the inbound `enum_options` event to the `Table.enum_options` handler and
reply to the requesting browser with the resolved values.

## Files

- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/tests/viz/test_table_types.py`

## Steps

- [x] **3.1 — Inbound event mapping**
  - In `server.py::_EVENT_MSG_MAP` add `"enum_options": "control:enum_options"`
    (next to the other table entries).

- [x] **3.2 — `LayoutHostImpl.dispatch_control_event` special case**
  - In `_layout.py`, after the control is resolved (`ctrl = self.resolve_control(cid)`),
    handle `msg_type == "control:enum_options"`:
    - Build `TableEnumOptionsRequest` from `payload["value"]`
      (`col` int, `row` int-or-None, `current` str-or-`""`).
    - `values = await ctrl.enum_options_values(request, event)` when `ctrl` has
      the attribute; else `values = []`.
    - `await self._transport.send_to_browser(payload.get("browser_id") or "",
      {"type": "enum_options", "id": cid, "request_id": payload["value"].get("request_id"),
       "values": values})`.
    - `return`.
  - Import `TableEnumOptionsRequest` from `._controls` locally (matches the
    existing local `parse_table_event` import).

- [x] **3.3 — Dispatch test**
  - Add an `@pytest.mark.anyio` test in `test_table_types.py` that:
    - constructs `LayoutHostImpl(None, scene_factory=lambda name: None,
      transport=fake, client_log=None)`,
    - monkeypatches `layout.resolve_control` to return a `Table(...,
      enum_options=handler)`,
    - asserts the fake transport's `send_to_browser` captured
      `{"type": "enum_options", "id": "tbl", "request_id": 7, "values": ["a","b"]}`
      for a payload `{"control_id": "tbl", "browser_id": "b1", "value":
      {"col": 0, "row": 0, "request_id": 7}}`.
  - Extend the fake transport with an async `send_to_browser` that appends
    `(browser_id, message)` (and a no-op `send`/`get` if `dispatch_control_event`
    touches them).

- [x] **3.4 — Thread `enum_options` through `TableView`**
  - In `views.py`, import `EnumOptionsHandler` from `._controls`, add
    `enum_options: EnumOptionsHandler | None = None` to `TableView.__init__` and
    pass it to `Table(...)`, and forward `enum_options=ctrl.enum_options` in
    `control_to_view`.

## Validation

```
uv run pytest py/tests/viz/test_table_types.py -q
```

## Notes

- The reply is browser-targeted, so it must **not** use the broadcast
  `control_update` path — an open editor must be populated without re-rendering
  the whole grid.
- No handler → reply with `values: []` (the frontend falls back to a dropdown
  with only the current value).
