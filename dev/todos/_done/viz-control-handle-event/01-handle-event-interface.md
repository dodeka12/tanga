# Phase 1 — `Dispatch` + `Control.handle_event` base interface

## Goal

Add the polymorphic dispatch seam to the control model: a `Dispatch` result
dataclass and a `Control.handle_event` default covering the generic value
controls. No behavior change yet — this phase only adds the interface.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/tests/viz/test_controls.py`

## Steps

- [x] **1.1 — `Dispatch` dataclass (`_controls.py`)**
  - Add `@dataclass class Dispatch` with `event: str | None = None`,
    `value: Any = None`, `push: Any = None`, near the other control dataclasses.
  - Docstring explains the three fields (handler event / handler value /
    `control_update` push value).

- [x] **1.2 — `Control.handle_event` default**
  - Add `def handle_event(self, event: str, payload: dict[str, Any]) -> Dispatch`
    to `Control` per the README contract: `click` → `Dispatch("click", None,
    None)`; `press`/`release` → `Dispatch(event, payload.get("value"), None)`;
    default → `Dispatch("change", payload.get("value"), None)`; `push` always
    `None`.
  - Return a `Dispatch`; never raise for unknown events.

- [x] **1.3 — Unit tests**
  - `Slider(...).handle_event("change", {"value": 0.5})` → `("change", 0.5, None)`.
  - `Button(...).handle_event("click", {})` → `("click", None, None)`.
  - `Slider(...).handle_event("press"/"release", {"value": v})` → pass-through.
  - Unknown event falls through to `"change"`.

## Validation

`uv run pytest py/tests/viz/test_controls.py -q`

## Notes

- Keep the default **non-mutating** — dispatch for generic controls is
  pass-through today; this must stay behavior-preserving.
- `payload` may be `{}` or missing `"value"`; use `.get("value")`.
