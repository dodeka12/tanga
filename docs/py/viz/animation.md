# Animation

Two complementary animation strategies are available. See the example scripts
[`demo_animation_orbit.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_animation_orbit.py) and
[`demo_animation_timeline.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_animation_timeline.py)
for runnable demonstrations.

## Frame Streaming (Python-Driven)

Push per-frame entity positions from Python. The browser applies in-place mesh
updates — no per-frame remove/recreate overhead.

```python
import math
from pytanga.viz import Visualizer
from pytanga.geometry import Point

viz = Visualizer()
viz.start()

point_id = viz.add(Point(3, 0, 0), color="#ff4444")
viz.flush()

angle = 0.0
for dt in viz.animate(fps=60):   # runs until Ctrl+C
    angle += 3.0 * dt
    viz.update_entity(point_id, Point(3 * math.cos(angle), 3 * math.sin(angle), 0))
    viz.flush()
```

`animate()` is the recommended way to drive a frame loop. It yields once per
frame (the elapsed wall-clock time in seconds), paces the loop to `fps`, and
stops the server cleanly when you press Ctrl+C — or whenever the loop ends.

### `animate()` reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fps` | `float` | `60.0` | Target frames per second. `0` disables pacing so the loop body can call `sleep_ms()` itself. |

- `start()` remains the non-blocking entry point; `animate()` starts the server
  automatically if it isn't running yet.
- Use `update_entity()` to replace geometry and `flush()` to push changed state.
  Only entities marked dirty by the scene manager are serialized — stationary
  entities cost nothing.

### Custom and nested loops

`animate()` drives a single flat loop. For sweeps over multiple variables, run
your own loops and check for Ctrl+C with `interrupted()` / `sleep_ms()`:

```python
viz.show()
try:
    for a in range(10):
        for b in range(20):
            # ... update entities ...
            viz.flush()
            if not viz.sleep_ms(16):   # False == interrupted
                break
        if viz.interrupted():          # True == interrupted
            break
finally:
    viz.stop_server()
```

- `interrupted()` returns `True` once Ctrl+C / SIGTERM has been received
  (requires the server to be started so the signal handler is installed).
- `sleep_ms(ms)` sleeps for `ms` milliseconds, returning `False` early if a
  break signal arrives, `True` otherwise. Use its result to pace *and* break
  nested loops without busy-waiting.

## Keyframe Tweening (Browser-Driven)

Smooth transitions without a Python loop:

```python
viz.animate_to(point_id, position=(5, 0, 0), duration=1.5, easing="ease-out")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `entity_id` | `str` | — | Entity ID from `add()` |
| `position` | `(float, float, float)` | `None` | Target world position |
| `rotation` | `(float, float, float)` | `None` | Target Euler rotation in radians |
| `opacity` | `float` | `None` | Target opacity (0–1) |
| `scale` | `(float, float, float)` | `None` | Target scale |
| `duration` | `float` | `1.0` | Duration in seconds |
| `easing` | `str` | `"ease-in-out"` | `"linear"`, `"ease-in"`, `"ease-out"`, `"ease-in-out"` |

Multiple `animate_to()` calls on the same entity replace any ongoing tween.
The browser's `animator.js` captures start state, interpolates in
`requestAnimationFrame`, and applies updates in-place.

## Timeline Sequencer

Orchestrate multiple animations with a fluent builder:

```python
viz.start()

p1 = viz.add(Point(0, 0, 0), color="#ff4444")
p2 = viz.add(Point(5, 0, 0), color="#44ff44")
viz.flush()

viz.timeline() \
    .animate_to(p1, position=(3, 2, 0), duration=1.5) \
    .wait(0.2) \
    .animate_to(p2, position=(0, 3, 0), duration=2.0) \
    .animate_to(p1, opacity=0.3, duration=0.5, parallel=True) \
    .play()

viz.sleep_ms(5000)
viz.stop()
```

- `wait(seconds)` — pause between steps
- `animate_to(..., parallel=True)` — run concurrently with the previous step
- `play()` — send the entire timeline to the browser

### Scene-Aware Timelines

For multi-scene setups, create a :class:`Timeline` targeting a specific scene
via :meth:`VizSceneHandle.timeline`:

```python
detail = viz.scene("detail")
detail.add(Point(0, 0, 0), color="#44ff44", entity_id="detail_point")

detail.timeline() \
    .animate_to("detail_point", position=(3, 2, 0), duration=1.5) \
    .wait(0.5) \
    .animate_to("detail_point", opacity=0.2, duration=1.0) \
    .play()
```

Timelines created through a :class:`VizSceneHandle` are automatically scoped
to that scene — the browser only animates entities within the currently viewed
scene.
