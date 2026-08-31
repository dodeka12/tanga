# Keep `ActPoint` on the XY plane in 2D visualizers

## Goal

Prevent ordinary `ActPoint` dragging in a 2D visualizer from changing the
point's Z coordinate across scene rebuilds.

Observed with `tanga-py==1.6.0`.

## User-visible symptom

A downstream 2D application rebuilds its scene after every drag and uses the
dropped `ActPoint` position in 3D distance calculations. Repeatedly moving an
obstacle to approximately the same visible XY location changes the calculated
path each time, even though the visible obstacle position appears nearly
unchanged.

Backend traces showed the real input drift:

```text
recompute 2: obs_start.z = 0.2019479599600924
recompute 3: obs_start.z = 0.4216180735775614
recompute 4: obs_start.z = 0.6430673504585274
recompute 5: obs_start.z = 0.7930673564189918
recompute 6: obs_start.z = 0.9430661966762210
recompute 7: obs_start.z = 1.0930638711448326
```

The X/Y coordinates remained near the intended location. As Z increased, the
3D distance from the obstacle to the ego path increased, so the avoidance path
moved closer to the straight line.

This is not accumulating solver state and is not caused by a shared mutable
`Point`. Sequential recomputations with identical control coordinates were
verified to produce identical paths.

## Cause

`ActPoint.interaction_config` uses `_default_drag_triggers()`. Its unmodified
left-button trigger selects `DragMode.VIEW_PLANE`:

```python
InteractionTrigger(
    event_type=InteractionEventType.DRAG,
    mouse_button=MouseButton.LEFT,
    drag_mode=DragMode.VIEW_PLANE,
)
```

Shift-drag selects `DragMode.XY_PLANE`, but users naturally use an unmodified
drag in a 2D application. With a tilted camera, movement on the view plane can
change Z. If the application persists the resulting point and reconstructs the
`ActPoint`, that new Z coordinate becomes the starting position for the next
drag.

The current behavior is internally consistent with `VIEW_PLANE`, but it is a
surprising default for a `VisualizerApp(space_dim=2)` and can silently corrupt
2D model inputs.

## Proposed API

Allow callers to constrain an `ActPoint` to a specific drag mode without
replacing the entire interaction configuration. For example:

```python
point = ActPoint(
    Point(1.0, 2.0, 0.0),
    drag_mode=DragMode.XY_PLANE,
    on_drag_end=on_drag_end,
)
```

When `drag_mode` is provided, create the primary unmodified left-button trigger
with that mode. Modifier-based alternate modes should either be disabled or
remain available according to an explicitly documented policy.

A more automatic option is to make unmodified `ActPoint` dragging use
`XY_PLANE` when the object is initialized in a visualizer whose
`space_dim == 2`. Explicit caller configuration is still useful because it is
predictable and also supports constrained points in 3D scenes.

## Possible implementation

Store an optional drag mode in `ActPoint`:

```python
def __init__(
    self,
    x: float | Point,
    y: float = 0.0,
    z: float = 0.0,
    *,
    drag_mode: DragMode | None = None,
    act_style: ActPointStyle | None = None,
    handler: ActHandler | None = None,
    on_drag_start: ActEventHandler | None = None,
    on_drag_end: ActEventHandler | None = None,
) -> None:
    ...
    self._drag_mode = drag_mode
```

Then build the interaction triggers accordingly:

```python
@property
def interaction_config(self) -> InteractionConfig:
    style = self._resolved_style or ActPointStyle()
    triggers = (
        _default_drag_triggers(MouseButton.LEFT)
        if self._drag_mode is None
        else [
            InteractionTrigger(
                event_type=InteractionEventType.DRAG,
                mouse_button=MouseButton.LEFT,
                drag_mode=self._drag_mode,
            )
        ]
    )
    return InteractionConfig(
        enabled=True,
        triggers=triggers,
        throttle_ms=40,
        hover_emissive=style.hover_emissive,
        hover_scale=style.hover_scale,
    )
```

The default `None` preserves current behavior and compatibility. Downstream 2D
applications can opt into the correct constraint immediately.

## Regression tests

- [ ] Construct `ActPoint(..., drag_mode=DragMode.XY_PLANE)` and assert its
      unmodified drag trigger uses `XY_PLANE`.
- [ ] Assert the constrained configuration does not include unintended view,
      XZ, or YZ drag triggers.
- [ ] Assert `drag_mode=None` retains the existing four default triggers.
- [ ] Add an interaction-level test, if available, confirming an XY-constrained
      drag preserves the point's original Z coordinate.
- [ ] Verify `on_drag_start`, custom `handler`, and `on_drag_end` continue to
      receive events normally.
- [ ] Document the modifier policy when an explicit mode is selected.

## Downstream workaround

Until pytanga exposes a drag constraint, a 2D callback must preserve the model
point's existing Z coordinate and accept only the final X/Y values:

```python
async def on_drag_end(event: DragEvent, _active_point: ActPoint) -> None:
    control.position = Point(
        event.world_position.x,
        event.world_position.y,
        control.position.z,
    )
    recompute()
```

This prevents Z drift in the model, although the active marker may move on the
view plane during the gesture and snap back to its constrained plane when the
scene is rebuilt. A native `ActPoint` constraint would avoid that visual snap
and enforce the invariant throughout the drag.

## Acceptance criteria

- Callers can configure unmodified `ActPoint` dragging to use `XY_PLANE`.
- An XY-constrained point retains its Z coordinate throughout dragging.
- Existing unconstrained `ActPoint` behavior remains backward compatible.
- The supported drag-mode behavior is documented and covered by unit tests.
