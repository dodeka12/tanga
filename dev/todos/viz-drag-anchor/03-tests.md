# Phase 3 — Tests

## Goal

Lock in the hook, the ray parsing, the coalescing, and the `DRAG_START` anchor
reply with unit tests.

## Files

- Edit: `py/tests/viz/test_active.py`
- Edit: `py/tests/viz/test_interaction_config.py`

## Steps

- [x] **3.1 — `ActPoint.drag_anchor` returns the centre**
  - In `test_active.py`, add a test that builds an `ActPoint(Point(0, 2, 0))`
    (initialised via a `_FakeSceneHandle`) and asserts
    `ap.drag_anchor(Point(9, 9, 9), Direction(1, 0, 0)) == Point(0, 2, 0)` —
    i.e. the ray is ignored.
  - Extend `test_active.py`'s `from pytanga.geometry import Point` import to
    also import `Direction`.

- [x] **3.2 — `_parse_event` reads `ray_origin` / `ray_direction`**
  - In `test_interaction_config.py`, extend a drag parse test (or add one) with
    `ray_origin`/`ray_direction` in the payload and assert the parsed
    `DragEvent` carries them; also assert the defaults are `Point(0, 0, 0)` /
    `Direction(0, 0, 0)` when the keys are absent.
  - Add `from pytanga.geometry import Direction, Point` to
    `test_interaction_config.py` (it currently imports only `_interaction`
    symbols); the same import serves step 3.3.

- [x] **3.3 — `_coalesce_drag_events` preserves the ray**
  - Assert the coalesced event keeps `first.ray_origin` / `first.ray_direction`.

- [x] **3.4 — `_dispatch_interaction_event` sends the anchor**
  - In `test_active.py` (which already imports `Visualizer`), build a
    `Visualizer(add_default_axes=False, add_default_grid=False)`, set
    `viz._server` to a stub exposing an async
    `push_raw_to_browser(browser_id, data)` that records calls, seed
    `viz._act_objects["pt1"] = ActPoint(Point(0, 2, 0))` (initialised via a
    `_FakeSceneHandle`), and
    `await viz._dispatch_interaction_event("interaction:drag_start", {...})`
    with a `drag_start` payload that carries a ray and a `browser_id`.
    Assert exactly one `interaction:drag_anchor` message is sent to that
    `browser_id`, carrying the point's centre `[0, 2, 0]`.

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- Follow the existing fakes in `test_active.py` (`_FakeSceneHandle`) rather than
  spinning up a real server.
- `test_interaction_config.py` already imports `_parse_event` and the event
  dataclasses; extend rather than duplicate.  Both test files need a small
  geometry-import addition (`Direction` in `test_active.py`;
  `Direction`/`Point` in `test_interaction_config.py`).
- The frontend rebase (pixel buffering + `setDragAnchor`) is JavaScript; Phase 3
  covers only the Python side.  It is gated by `node --check` in Phase 2 (there
  is no DOM/Three.js unit harness in the repo today).  If coverage is wanted
  later, `_pixelToWorldDelta` is the pure function to extract and unit-test.
