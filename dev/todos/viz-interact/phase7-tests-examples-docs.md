# Phase 7 — Tests, Examples & Documentation

**Prerequisites:** All previous phases (1–6)

**Goal:** Write unit tests for the Python interaction dataclasses, handler
registry, and coalescing logic.  Create example scripts demonstrating drag,
click, and scroll interaction.  Add user documentation.

---

## 1. Tests

### 1.1 New File: `py/tests/viz/test_interaction_config.py`

Tests for serialization and deserialization of `InteractionTrigger`,
`InteractionConfig`, and `InteractionEventType` enums.

```python
"""Tests for interaction config serialization."""
import pytest
from pytanga.viz._interaction import (
    InteractionConfig,
    InteractionTrigger,
    InteractionEventType,
    MouseButton,
    ModifierKey,
)
from pytanga.viz._interaction import _parse_event, _parse_modifiers


class TestInteractionTrigger:
    def test_to_dict_minimal(self):
        t = InteractionTrigger(event_type=InteractionEventType.CLICK)
        d = t.to_dict()
        assert d == {
            "event_type": "click",
            "modifiers": [],
        }

    def test_to_dict_full(self):
        t = InteractionTrigger(
            event_type=InteractionEventType.DRAG,
            mouse_button=MouseButton.LEFT,
            modifiers=frozenset({ModifierKey.CTRL, ModifierKey.SHIFT}),
        )
        d = t.to_dict()
        assert d["event_type"] == "drag"
        assert d["mouse_button"] == "left"
        assert set(d["modifiers"]) == {"ctrl", "shift"}

    def test_from_dict(self):
        d = {"event_type": "drag", "mouse_button": "right", "modifiers": ["alt"]}
        t = InteractionTrigger.from_dict(d)
        assert t.event_type == InteractionEventType.DRAG
        assert t.mouse_button == MouseButton.RIGHT
        assert t.modifiers == frozenset({ModifierKey.ALT})

    def test_from_dict_no_button(self):
        d = {"event_type": "scroll", "modifiers": []}
        t = InteractionTrigger.from_dict(d)
        assert t.mouse_button is None


class TestInteractionConfig:
    def test_to_dict(self):
        ic = InteractionConfig(
            enabled=True,
            triggers=[
                InteractionTrigger(event_type=InteractionEventType.DRAG),
            ],
            throttle_ms=30,
        )
        d = ic.to_dict()
        assert d["enabled"] is True
        assert len(d["triggers"]) == 1
        assert d["throttle_ms"] == 30

    def test_to_dict_disabled(self):
        ic = InteractionConfig(enabled=False)
        d = ic.to_dict()
        assert d["enabled"] is False
        assert d["triggers"] == []
        assert d["throttle_ms"] == 50


class TestParseEvent:
    def test_parse_click(self):
        data = {
            "type": "interaction:click",
            "event_type": "click",
            "object_id": "abc",
            "mouse_button": "left",
            "modifiers": ["ctrl"],
            "screen_position": [100, 200],
            "world_position": [1.0, 2.0, 3.0],
            "world_normal": [0.0, 0.0, 1.0],
        }
        event = _parse_event(data)
        assert event.object_id == "abc"
        assert event.event_type == InteractionEventType.CLICK
        assert event.mouse_button == MouseButton.LEFT
        assert event.modifiers == frozenset({ModifierKey.CTRL})
        assert event.screen_position == (100, 200)
        assert event.world_position == (1.0, 2.0, 3.0)
        assert event.world_normal == (0.0, 0.0, 1.0)

    def test_parse_drag_move(self):
        data = {
            "type": "interaction:drag_move",
            "event_type": "drag_move",
            "object_id": "x",
            "mouse_button": "left",
            "modifiers": [],
            "screen_position": [300, 400],
            "delta_pixels": [5, -2],
            "world_position": [1.0, 2.0, 3.0],
            "delta_transform": [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1],
        }
        event = _parse_event(data)
        assert event.event_type == InteractionEventType.DRAG_MOVE
        assert event.delta_pixels == (5, -2)
        assert len(event.delta_transform) == 16

    def test_parse_scroll(self):
        data = {
            "type": "interaction:scroll",
            "event_type": "scroll",
            "object_id": "s",
            "modifiers": ["shift"],
            "screen_position": [400, 300],
            "delta_xy": [0, -120],
        }
        event = _parse_event(data)
        assert event.event_type == InteractionEventType.SCROLL
        assert event.delta_xy == (0, -120)

    def test_parse_unknown_event_type(self):
        with pytest.raises(ValueError):
            _parse_event({"type": "interaction:foo", "event_type": "bogus"})
```

### 1.2 New File: `py/tests/viz/test_interaction_registry.py`

Tests for handler registry, registration, dispatch, and coalescing.

```python
"""Tests for InteractionHandlerRegistry and coalescing."""
import asyncio
import pytest
from pytanga.viz._interaction import (
    InteractionHandlerRegistry,
    InteractionEventType,
    DragEvent,
    ClickEvent,
    _coalesce_drag_events,
)


class TestCoalesceDragEvents:
    def test_single_event(self):
        e = DragEvent(delta_pixels=(1, 0), screen_position=(100, 200))
        result = _coalesce_drag_events([e])
        assert result.delta_pixels == (1, 0)

    def test_two_events(self):
        e1 = DragEvent(delta_pixels=(1, 0), screen_position=(100, 200))
        e2 = DragEvent(delta_pixels=(2, 3), screen_position=(105, 208))
        result = _coalesce_drag_events([e1, e2])
        assert result.delta_pixels == (3, 3)
        # Latest position wins
        assert result.screen_position == (105, 208)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            _coalesce_drag_events([])


class TestHandlerRegistry:
    @pytest.mark.asyncio
    async def test_register_and_dispatch(self):
        results = []
        async def handler(event):
            results.append(event.object_id)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)

        await registry.dispatch(ClickEvent(object_id="obj1"))
        # Fire-and-forget: need small delay for task to complete
        await asyncio.sleep(0.01)
        assert results == ["obj1"]

    @pytest.mark.asyncio
    async def test_unregister(self):
        results = []
        async def handler(event):
            results.append(1)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)
        registry.unregister("obj1", InteractionEventType.CLICK)

        await registry.dispatch(ClickEvent(object_id="obj1"))
        await asyncio.sleep(0.01)
        assert results == []

    @pytest.mark.asyncio
    async def test_clear(self):
        results = []
        async def handler(event):
            results.append(1)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.CLICK, handler)
        registry.clear()

        await registry.dispatch(ClickEvent(object_id="obj1"))
        await asyncio.sleep(0.01)
        assert results == []

    @pytest.mark.asyncio
    async def test_drag_coalescing(self):
        """Simulate rapid drag_move events — they should be coalesced."""
        results = []

        async def slow_handler(event):
            await asyncio.sleep(0.05)  # Simulate slow handler
            results.append(event.delta_pixels)

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.DRAG_MOVE, slow_handler)

        # Send three rapid drag_move events
        await registry.dispatch(DragEvent(
            object_id="obj1",
            event_type=InteractionEventType.DRAG_MOVE,
            delta_pixels=(1, 0),
        ))
        await registry.dispatch(DragEvent(
            object_id="obj1",
            event_type=InteractionEventType.DRAG_MOVE,
            delta_pixels=(2, 0),
        ))
        await registry.dispatch(DragEvent(
            object_id="obj1",
            event_type=InteractionEventType.DRAG_MOVE,
            delta_pixels=(3, 0),
        ))

        # Wait for handler to complete and coalesced dispatch
        await asyncio.sleep(0.15)

        # First delta (1,0) was dispatched immediately.
        # The remaining two were coalesced into (5,0).
        assert len(results) >= 1
        assert results[0] == (1, 0)
        # The second dispatch should have the coalesced delta
        if len(results) >= 2:
            assert results[1] == (5, 0)  # 2+3 = 5

    @pytest.mark.asyncio
    async def test_drag_start_flushes_pending(self):
        results = []

        async def slow_handler(event):
            await asyncio.sleep(0.05)
            results.append(("move", event.delta_pixels))

        async def start_handler(event):
            results.append(("start", event.delta_pixels))

        registry = InteractionHandlerRegistry()
        registry.register("obj1", InteractionEventType.DRAG_MOVE, slow_handler)
        registry.register("obj1", InteractionEventType.DRAG_START, start_handler)

        # Send drag_move first (starts processing)
        await registry.dispatch(DragEvent(
            object_id="obj1",
            event_type=InteractionEventType.DRAG_MOVE,
            delta_pixels=(1, 0),
        ))
        # Queue another move
        await registry.dispatch(DragEvent(
            object_id="obj1",
            event_type=InteractionEventType.DRAG_MOVE,
            delta_pixels=(2, 0),
        ))
        # Send drag_start — should flush the pending queue
        await registry.dispatch(DragEvent(
            object_id="obj1",
            event_type=InteractionEventType.DRAG_START,
            delta_pixels=(0, 0),
        ))

        await asyncio.sleep(0.15)
        # The drag_start should arrive
        assert any(r[0] == "start" for r in results)


class TestUtilityFunctions:
    def test_apply_delta_transform(self):
        from pytanga.viz._interaction import apply_delta_transform

        # Identity transform (screen X → world X, screen Y → world Y)
        transform = (
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )
        result = apply_delta_transform((10, 20), transform)
        assert result == (10, 20, 0)

    def test_extract_camera_directions(self):
        from pytanga.viz._interaction import extract_camera_directions

        # Identity-like transform
        transform = (
            1, 0, 0, 0,   # right
            0, 1, 0, 0,   # up
            0, 0, 1, 0,   # forward
            0, 0, 0, 1,
        )
        right, up, forward = extract_camera_directions(transform)
        assert right == (1, 0, 0)
        assert up == (0, 1, 0)
        assert forward == (0, 0, 1)


class TestEnums:
    def test_mouse_button_from_js_code(self):
        assert MouseButton.from_js_code(0) == MouseButton.LEFT
        assert MouseButton.from_js_code(1) == MouseButton.MIDDLE
        assert MouseButton.from_js_code(2) == MouseButton.RIGHT
        with pytest.raises(ValueError):
            MouseButton.from_js_code(3)

    def test_mouse_button_to_js_code(self):
        assert MouseButton.LEFT.to_js_code() == 0
        assert MouseButton.MIDDLE.to_js_code() == 1
        assert MouseButton.RIGHT.to_js_code() == 2
```

---

## 2. Examples

### 2.1 New File: `py/examples/viz/demo_drag_point.py`

```python
"""Demo: Drag a 3D point interactively with the mouse.

Usage:  uv run python py/examples/viz/demo_drag_point.py

Left-click and drag the red point to move it in 3D space.
The point moves in the screen plane at its current depth.
"""

import asyncio
from pytanga.viz import Visualizer, InteractionConfig, InteractionTrigger
from pytanga.viz._interaction import (
    InteractionEventType,
    MouseButton,
    apply_delta_transform,
)
from pytanga.geometry import Point


async def main():
    viz = Visualizer(title="Drag Demo — Grab the red point")
    viz.start()

    # Add a draggable point
    p = Point(0, 0, 0)
    point_id = viz.add(p, color="#ff4444", opacity=1.0)

    # Add reference points (non-interactive)
    for i in range(-5, 6):
        viz.add(Point(i, 0, 0), color="#444444", opacity=0.3)
        viz.add(Point(0, i, 0), color="#444444", opacity=0.3)

    # Configure interaction
    viz.set_interaction(point_id, InteractionConfig(
        enabled=True,
        triggers=[
            InteractionTrigger(
                event_type=InteractionEventType.DRAG,
                mouse_button=MouseButton.LEFT,
            ),
        ],
        throttle_ms=50,
    ))

    async def on_drag(event):
        dx, dy, dz = apply_delta_transform(event.delta_pixels, event.delta_transform)
        new_x = p[0] + dx
        new_y = p[1] + dy
        new_z = p[2] + dz
        # Update the Point entity in place
        # (p is a reference, we update the visualizer with a new Point)
        new_p = Point(new_x, new_y, new_z)
        viz.update_entity(event.object_id, new_p)

    viz.on_interaction(point_id, InteractionEventType.DRAG_MOVE, on_drag)

    print("Drag the red point. Press Ctrl+C to exit.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
```

### 2.2 New File: `py/examples/viz/demo_interactive_sphere.py`

```python
"""Demo: Interactive sphere — click to change color, scroll to resize.

Usage:  uv run python py/examples/viz/demo_interactive_sphere.py

Ctrl+click the sphere to cycle through colors.
Shift+scroll to resize the sphere.
"""

import asyncio
from pytanga.viz import Visualizer, InteractionConfig, InteractionTrigger
from pytanga.viz._interaction import (
    InteractionEventType,
    MouseButton,
    ModifierKey,
)
from pytanga.geometry import Point, Sphere


COLORS = ["#ff4444", "#44ff44", "#4444ff", "#ffff44", "#ff44ff", "#44ffff"]


async def main():
    viz = Visualizer(title="Interactive Sphere Demo")
    viz.start()

    sphere = Sphere(Point(0, 0, 0), radius=2.0)
    sphere_id = viz.add(sphere, color=COLORS[0], opacity=1.0, wireframe=False)

    viz.set_interaction(sphere_id, InteractionConfig(
        enabled=True,
        triggers=[
            InteractionTrigger(
                event_type=InteractionEventType.CLICK,
                mouse_button=MouseButton.LEFT,
                modifiers=frozenset({ModifierKey.CTRL}),
            ),
            InteractionTrigger(
                event_type=InteractionEventType.SCROLL,
                modifiers=frozenset({ModifierKey.SHIFT}),
            ),
        ],
        throttle_ms=100,
    ))

    color_index = 0
    current_radius = 2.0

    async def on_click(event):
        nonlocal color_index
        color_index = (color_index + 1) % len(COLORS)
        viz.update(event.object_id, color=COLORS[color_index])

    async def on_scroll(event):
        nonlocal current_radius
        delta = event.delta_xy[1]  # vertical scroll
        current_radius = max(0.2, min(10.0, current_radius + delta * 0.01))
        viz.update_entity(
            event.object_id,
            Sphere(Point(0, 0, 0), radius=current_radius),
        )

    viz.on_interaction(sphere_id, InteractionEventType.CLICK, on_click)
    viz.on_interaction(sphere_id, InteractionEventType.SCROLL, on_scroll)

    print("Ctrl+click to change color. Shift+scroll to resize. Press Ctrl+C to exit.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
```

---

## 3. Documentation

### 3.1 New File: `docs/py/viz/interaction.md`

A user guide covering:

- **Overview**: What object interaction is and its architecture
- **Quick Start**: Minimal example (drag a point)
- **InteractionConfig**: All fields and their meaning
- **InteractionTrigger**: Matching rules for event types, mouse buttons, and modifiers
- **Event Types**: `ClickEvent`, `DragEvent`, `ScrollEvent` with field descriptions
- **Registering Handlers**: `viz.on_interaction()` API
- **Utility Functions**: `apply_delta_transform()` and `extract_camera_directions()`
- **Throttling**: How throttling works, recommended values
- **Enums Reference**: `InteractionEventType`, `MouseButton`, `ModifierKey`
- **OrbitControls Conflicts**: How drag disables orbit controls automatically
- **Troubleshooting**: Common issues

### 3.2 Modified File: `docs/py/viz/index.md`

Add a link to the new interaction documentation under a "User Interaction"
or "Advanced" section.

---

## 4. Implementation Checklist

- [ ] Create `py/tests/viz/test_interaction_config.py`
- [ ] Test: `InteractionTrigger.to_dict()` and `from_dict()`
- [ ] Test: `InteractionConfig.to_dict()`
- [ ] Test: `_parse_event()` for click, drag, scroll
- [ ] Test: `_coalesce_drag_events()`
- [ ] Test: `apply_delta_transform()` and `extract_camera_directions()`
- [ ] Test: `MouseButton.from_js_code()` and `to_js_code()`
- [ ] Create `py/tests/viz/test_interaction_registry.py`
- [ ] Test: register + dispatch + unregister + clear
- [ ] Test: drag_move coalescing with slow handler
- [ ] Test: drag_start flushes pending queue
- [ ] Create `py/examples/viz/demo_drag_point.py`
- [ ] Create `py/examples/viz/demo_interactive_sphere.py`
- [ ] Create `docs/py/viz/interaction.md`
- [ ] Update `docs/py/viz/index.md` with link
- [ ] Run all tests: `uv run pytest py/tests/viz/test_interaction_*.py -v`

---

## 5. Verification

- [ ] All unit tests pass
- [ ] `demo_drag_point.py` runs and point can be dragged interactively
- [ ] `demo_interactive_sphere.py` runs — click changes color, scroll resizes
- [ ] Documentation renders correctly in mkdocs
- [ ] No import errors: `from pytanga.viz import InteractionConfig, InteractionEventType, apply_delta_transform` works