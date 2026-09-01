# `ActPoint`'s rendered `entity` and its drag-anchor position can silently desync

## Goal

Programmatically repositioning an `ActPoint` via its `VizObjectRef.entity`
setter should also update whatever position `ActPoint.drag_anchor()` resolves
future drags from, so the point behaves consistently regardless of whether it
was last moved by the user or by application code.

Observed with `tanga-py==1.14.1`.

## User-visible symptom

An application (`src/examples/floating_interactive_v3.py`) has three
draggable `ActPoint`s defining a Sin obstacle path: `start`, `end`, and an
`amplitude` point defined relative to the `start`/`end` baseline (as
`(frac, amplitude)`, i.e. fraction along the baseline + perpendicular
distance). When the user drags `start` or `end`, the app keeps `amplitude`'s
*relative* position fixed by recomputing its absolute position and writing it
back via:

```python
self._obstacle_point_refs[2].entity = new_amplitude_point
```

This renders correctly -- the amplitude point visually follows the baseline
in real time, exactly as intended.

However, the *next* time the user grabs the amplitude point directly (a
fresh, unrelated drag), it instantly jumps to wherever it was rendered
*before* the baseline drag, instead of starting from its current, correctly
carried-along position. From the user's perspective: "when I moved an
endpoint and then want to drag the amplitude control, it suddenly jumps to
somewhere completely different."

## Cause

`viz.new(ActPoint(...))` returns a `VizObjectRef` that wraps the *rendered
scene node*, a separate object from the `ActPoint` instance itself. The
`ActPoint` is stored independently in the visualizer's own
`_act_objects` registry (keyed by entity id):

```python
# pytanga/viz/visualizer.py::_add_to_scene
if isinstance(obj, ActSceneObject):
    ...
    eid = scene.add(obj.entity, entity_id=entity_id, **properties)
    obj._init(VizSceneHandle(self, scene_name), eid)
    self._act_objects[eid] = obj
    ...
```

`VizObjectRef.entity`'s setter only touches the scene node, not the
`ActPoint`:

```python
# pytanga/viz/_object_ref.py
@entity.setter
def entity(self, value: Any) -> None:
    self._scene_node().set_entity(value)
```

Meanwhile `ActPoint` keeps its own private `_point`, which is exactly what a
future `DRAG_START` resolves its anchor from -- the ray is ignored entirely:

```python
# pytanga/viz/_active.py
def _move_to(self, pos: Point) -> None:
    """Set the point position to *pos*."""
    self._point = pos

def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
    """Return the ideal anchor — the point's centre (the ray is ignored)."""
    return self._point
```

`_move_to()` is only ever called from `ActSceneObject._on_drag()` (the
default per-frame handling after a custom `handler=` returns `False`) -- there
is no public API to update an `ActPoint`'s own `_point` from outside a drag on
that same point:

```python
# pytanga/viz/_active.py
async def _on_drag(self, event: DragEvent) -> None:
    if self._handler is not None:
        handled = await self._handler(event, self)
        if handled:
            return
    self._move_to(event.world_position)
    self.update()
    self.flush()
```

And on every `DRAG_START`, the backend overwrites `event.world_position` with
exactly this stale `_point` before the user's own `on_drag_start`/`handler`
ever sees it:

```python
# pytanga/viz/visualizer.py::_send_drag_anchor
act = self._act_objects.get(event.object_id)
...
anchor = act.drag_anchor(event.ray_origin, event.ray_direction)
event.world_position = anchor
```

So: `ref.entity = new_point` updates the rendered mesh (correct visually),
but `ActPoint._point` -- the sole source of truth `drag_anchor()` uses --
stays at whatever it was after the point's *own* last direct drag. The next
direct drag on that point starts from the stale value, producing a visible
jump back to the pre-carry position.

## Proposed fix

Give `ActPoint` (or `ActSceneObject` generally) a public way to update its own
position without going through a live drag, and/or have
`VizObjectRef.entity`'s setter update the backing `ActSceneObject`'s position
too when the node it wraps has one registered in `_act_objects`. Either of:

1. Add a public `ActPoint.set_position(point: Point) -> None` (or a public
   `point` setter) that calls `self._move_to(point)` directly, so application
   code has a supported way to keep `_point` in sync when repositioning a
   point outside of its own drag flow.
2. Have `VizSceneHandle`/`VizObjectRef.entity`'s setter check
   `self._handle._visualizer._act_objects.get(node.id)` and, if present, call
   `_move_to()` on it too -- so the two representations (rendered node vs.
   `ActPoint._point`) can never desync via the officially documented
   `ref.entity = ...` pattern in the first place.

Option 2 seems preferable since it fixes the footgun for *any* `ActSceneObject`
subclass, not just call sites that remember to reach for a new dedicated
setter.

## Regression tests

- [ ] Create an `ActPoint`, add it via `viz.new(...)`, then reposition it via
      `ref.entity = new_point` (not through a drag). A subsequent
      `DRAG_START` event on that same point should resolve its anchor
      (`drag_anchor()`) to `new_point`, not the point's original position.
- [ ] The existing drag-driven path (`_on_drag` → `_move_to` → `update` →
      `flush`) should be unaffected -- `drag_anchor()` after a normal user
      drag should still resolve to wherever the user last dropped the point.

## Downstream workaround (applied)

`floating_interactive_v3.py` now keeps a second list of the actual `ActPoint`
instances alongside their `VizObjectRef`s (`_obstacle_act_points` next to
`_obstacle_point_refs`, both built together in `_rebuild_obstacle_points`).
Whenever the Sin amplitude point is repositioned programmatically
(`_carry_sin_amplitude_point`), the app calls the protected
`act_point._move_to(new_point)` in addition to `ref.entity = new_point`, to
keep both representations in sync. This relies on a private method and
should be replaced with a public API once one exists upstream.

## Acceptance criteria

- Repositioning an `ActPoint` via `VizObjectRef.entity = ...` (or a new
  public setter, once added) leaves the point in a state where a subsequent
  direct drag on it starts from the new position, not a stale one.
- No change in behavior for points that are only ever moved through their own
  drag handler.
