# Phase 1 — `drag_anchor` hook + backend anchor reply (Python)

## Goal

Add the per-type `drag_anchor` hook, parse the picking ray from `drag_start`,
and make the backend compute and send the ideal anchor back to the originating
browser on `DRAG_START`.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/pytanga/viz/_interaction.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/server.py`

## Steps

- [x] **1.1 — Add the `drag_anchor` hook**
  - In `_active.py`, extend the top import from
    `from pytanga.geometry import Point` to
    `from pytanga.geometry import Direction, Point`.
  - Add to `ActSceneObject` (next to `_move_to`):
    ```python
    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Return the nearest point on the ideal geometry to the picking ray."""
        raise NotImplementedError
    ```
  - In `ActPoint`, override `drag_anchor` to `return self._point`.

- [x] **1.2 — Add ray fields to `DragEvent` and parse them**
  - In `_interaction.py` `DragEvent`, add
    `ray_origin: Point = field(default_factory=Point)` and
    `ray_direction: Direction = field(default_factory=Direction)`.
  - In `_parse_event`'s drag branch, parse
    `ray_origin = data.get("ray_origin", [0.0, 0.0, 0.0])` and
    `ray_direction = data.get("ray_direction", [0.0, 0.0, 0.0])` into
    `Point(...)` / `Direction(...)` and pass them to the `DragEvent(...)` call.
  - In `_coalesce_drag_events`, add `ray_origin=first.ray_origin,
    ray_direction=first.ray_direction` to the returned `DragEvent(...)`.

- [x] **1.3 — Track `ActSceneObject` instances on the visualizer**
  - In `visualizer.py` `__init__` (next to `self._interaction_registry`), add
    `self._act_objects: dict[str, Any] = {}`.
  - In `_add_to_scene()`'s `ActSceneObject` branch (the path used by
    `add()` / `new()` / `__call__`), after `obj._init(...)` add
    `self._act_objects[eid] = obj`.

- [x] **1.4 — Add a targeted raw send to the server**
  - In `server.py`, add (next to `push_raw`):
    ```python
    async def push_raw_to_browser(self, browser_id: str, data: str) -> None:
        """Send an arbitrary JSON string to a single browser session."""
        session = self._browser_sessions.get(browser_id)
        if session is None:
            return
        try:
            await session.ws.send_str(data)
        except (ConnectionError, Exception):
            pass
    ```
  - Mirror `push_raw`'s `_ws_msg_brief` logging if desired.

- [x] **1.5 — Compute and send the anchor on `DRAG_START`**
  - In `visualizer.py`, add a helper `async def _send_drag_anchor(self, event)`:
    - Import `DragEvent` and `InteractionEventType` lazily (alongside the
      existing `from ._interaction import _parse_event`); use the module-level
      `json` import already present.
    - Guard: only for a `DragEvent` with
      `event.event_type is InteractionEventType.DRAG_START` and a truthy
      `event.browser_id`.
    - `act = self._act_objects.get(event.object_id)`; if `None`, return.
    - `try: anchor = act.drag_anchor(event.ray_origin, event.ray_direction)`
      `except NotImplementedError: return`.
    - If `self._server` is not None, `await
      self._server.push_raw_to_browser(event.browser_id,
      json.dumps({"type": "interaction:drag_anchor",
      "object_id": event.object_id,
      "world_position": [anchor.x, anchor.y, anchor.z]}))`.
  - In `_dispatch_interaction_event`, call `await self._send_drag_anchor(event)`
    before `await self._interaction_registry.dispatch(event)`.

## Validation

`uv run ruff check py/pytanga/viz/ && uv run pytest py/tests/viz -q`

## Notes

- The anchor reply uses `world_position`, not `world_delta`; it is an absolute
  position the frontend rebases onto.
- The base `drag_anchor` raising `NotImplementedError` keeps unknown subclasses
  on today's behaviour (no anchor reply → the frontend keeps its mesh-surface
  anchor).
- The `drag_start` `world_position` is still the mesh hit point (the anchor
  arrives one round-trip later); a user `on_drag_start` handler sees that
  pre-anchor value, which is the documented, best-effort behaviour.
