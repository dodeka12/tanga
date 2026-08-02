# Phase 1 — WebSocket Protocol & Python Data Model

Define the JSON protocol messages for control definition (Python → JS) and
control events (JS → Python), plus the Python data classes that represent
controls and control groups.

References: [Overview](./README.md)

---

## 1.1 WebSocket Protocol Message Formats

### 1.1.1 Python → JS: Control Definition (`controls_define`)

Sent when the Python side registers or re-defines controls. Replaces all
existing controls (not incremental — the JS side discards the old panel and
rebuilds from this message).

```json
{
  "type": "controls_define",
  "controls": [
    {
      "id": "pos_x",
      "kind": "slider",
      "label": "X Position",
      "min": 0.0,
      "max": 5.0,
      "step": 0.1,
      "default": 2.0
    },
    {
      "id": "mode_select",
      "kind": "dropdown",
      "label": "Mode",
      "options": ["Wireframe", "Solid", "Translucent"],
      "default": "Solid"
    },
    {
      "id": "reset_btn",
      "kind": "button",
      "label": "Reset"
    }
  ],
  "groups": [
    {
      "id": "sphere_b_group",
      "title": "Sphere B",
      "controls": ["pos_x", "mode_select", "reset_btn"],
      "position": "bottom-right",
      "collapsed": false,
      "parentId": null
    }
  ],
  "orphanControls": ["__standalone_slider__"]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `controls` | list | All control definitions. Each has `id` (str), `kind` (slider/dropdown/button), `label` (str), and kind-specific fields. |
| `groups` | list | All control groups. Each has `id` (str), `title` (str), `controls` (list of control IDs), `position` (default viewport anchor), `collapsed` (bool), and optional `parentId` (attach to 3D entity). |
| `orphanControls` | list | Control IDs not belonging to any group. Rendered in a default unlabeled panel at the specified anchor. |

**Slider-specific fields:** `min` (float), `max` (float), `step` (float), `default` (float).
**Dropdown-specific fields:** `options` (list of str), `default` (str).
**Button-specific fields:** None beyond `kind`/`id`/`label`.

**Group position anchors:** `"top-left"`, `"top-right"`, `"bottom-left"`, `"bottom-right"`.

**Group attachment via `parentId`:** When set, the group is rendered as a
CSS2DObject attached to the 3D entity with that ID. The group title bar acts
as a label (always visible). The controls expand when the user clicks the
expand button. When `null`, the group is a fixed-position DOM panel.

### 1.1.2 Python → JS: Control Removal (`controls_clear`)

Removes all controls and groups from the frontend.

```json
{
  "type": "controls_clear"
}
```

### 1.1.3 JS → Python: Control Value Change (`control:change`)

Sent whenever a slider value changes or a dropdown selection changes.

```json
{
  "type": "control:change",
  "control_id": "pos_x",
  "value": 2.7
}
```

For sliders, `value` is a float. For dropdowns, `value` is the selected
string. Throttled at ~40 ms for sliders to avoid flooding the server on rapid
drag (the JS fires `input` events but debounces the WebSocket send).

### 1.1.4 JS → Python: Button Click (`control:click`)

Sent when a button is clicked.

```json
{
  "type": "control:click",
  "control_id": "reset_btn"
}
```

### 1.1.5 JS → Python: Group State Change (`control:group_toggle`)

Sent when a group is expanded or collapsed (optional — can also be purely
visual with no Python callback).

```json
{
  "type": "control:group_toggle",
  "group_id": "sphere_b_group",
  "collapsed": true
}
```

Only sent if a Python `on_toggle` callback is registered for the group.

---

## 1.2 Python Data Model (`_controls.py`)

### 1.2.1 `Control` Base + Subtypes

```python
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Optional

Handler = Callable[[Any], Awaitable[None]]  # async handler

@dataclass
class Control:
    id: str
    label: str = ""
    parent_id: Optional[str] = None  # attach to 3D entity

@dataclass
class Slider(Control):
    kind: str = "slider"
    min: float = 0.0
    max: float = 1.0
    step: float = 0.01
    default: float = 0.5
    on_change: Optional[Handler] = None

@dataclass
class Dropdown(Control):
    kind: str = "dropdown"
    options: list[str] = field(default_factory=list)
    default: str = ""
    on_change: Optional[Handler] = None

@dataclass
class Button(Control):
    kind: str = "button"
    on_click: Optional[Handler] = None
```

### 1.2.2 `ControlGroup`

```python
@dataclass
class ControlGroup:
    id: str
    title: str = ""
    controls: list[Control] = field(default_factory=list)
    position: str = "bottom-right"  # top-left, top-right, bottom-left, bottom-right
    collapsed: bool = False
    parent_id: Optional[str] = None  # attach to 3D entity
    on_toggle: Optional[Handler] = None  # called when group is expanded/collapsed
```

When `parent_id` is set, the group's title bar is rendered as a CSS2DObject
attached to the entity. The title serves as a persistent label. The controls
expand/collapse from the title bar.

### 1.2.3 Serialization

```python
def serialize_controls(groups: list[ControlGroup]) -> dict:
    """Build the controls_define JSON message from group definitions."""
    all_controls: dict[str, dict] = {}
    group_list: list[dict] = []
    orphan_ids: list[str] = []

    seen_ids: set[str] = set()
    for group in groups:
        group_control_ids: list[str] = []
        for ctrl in group.controls:
            group_control_ids.append(ctrl.id)
            seen_ids.add(ctrl.id)
            all_controls[ctrl.id] = _serialize_one_control(ctrl)
        group_list.append({
            "id": group.id,
            "title": group.title,
            "controls": group_control_ids,
            "position": group.position,
            "collapsed": group.collapsed,
            "parentId": group.parent_id,
        })

    return {
        "type": "controls_define",
        "controls": list(all_controls.values()),
        "groups": group_list,
        "orphanControls": orphan_ids,
    }
```

---

## 1.3 Asyncio Handler Dispatch Pattern

Handlers are registered by ID in a dict mapping `control_id → async callable`.
When a `control:change` or `control:click` message arrives from the frontend,
the server looks up the handler and schedules it on the event loop.

```python
# In _controls.py or visualizer.py
class ControlHandlerRegistry:
    def __init__(self):
        self._handlers: dict[str, Handler] = {}

    def register(self, control_id: str, handler: Handler) -> None:
        self._handlers[control_id] = handler

    def unregister(self, control_id: str) -> None:
        self._handlers.pop(control_id, None)

    def get(self, control_id: str) -> Optional[Handler]:
        return self._handlers.get(control_id)

    def clear(self) -> None:
        self._handlers.clear()
```

The server's `_ws_handler` dispatches incoming `control:change` and
`control:click` messages by looking up the handler and scheduling
`asyncio.create_task(handler(value))`.

---

## 1.4 Implementation Checklist

- [ ] 1.1 Create `py/pytanga/viz/_controls.py` with `Slider`, `Dropdown`, `Button`, `ControlGroup` dataclasses
- [ ] 1.2 Add `Handler` type alias (`Callable[[Any], Awaitable[None]]`)
- [ ] 1.3 Add `ControlHandlerRegistry` class with `register`, `unregister`, `get`, `clear`
- [ ] 1.4 Add `serialize_controls()` function producing the `controls_define` JSON format
- [ ] 1.5 Add `_serialize_one_control()` helper for individual control serialization
- [ ] 1.6 Write unit tests for serialization round-trip (slider, dropdown, button, group)
- [ ] 1.7 Write unit tests for `ControlHandlerRegistry` (register, dispatch, unregister, clear)
- [ ] 1.8 Verify JSON protocol examples against Python serialization output