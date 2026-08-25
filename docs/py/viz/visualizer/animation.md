# Animation

Two complementary animation strategies are available. See the example scripts
[`orbit.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/animation/orbit.py) and
[`timeline.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/animation/timeline.py)
for runnable demonstrations.

## Frame Streaming (Python-Driven)

Push per-frame entity positions from Python. The browser applies in-place mesh
updates — no per-frame remove/recreate overhead.

```python
import math
from pytanga.viz import Visualizer
from pytanga.geometry import Point

viz = Visualizer()
viz.show()  # open the viewer (inline in Jupyter, browser tab in a script)
p = viz(Point(3, 0, 0), color="#ff4444")  # viz(...) == viz.new(...)

angle = 0.0
for dt in viz.animate(fps=60):   # runs until Q (browser) or Ctrl+C (terminal)
    angle += 3.0 * dt
    p.entity = Point(3 * math.cos(angle), 3 * math.sin(angle), 0)  # update in place
    viz.flush()
```

`animate()` is the recommended way to drive a frame loop. It yields once per
frame (the elapsed wall-clock time in seconds) and paces the loop to `fps`.
The loop ends when the scene's stop key is pressed in the browser (default
**Q**, no modifiers) or when Ctrl+C / SIGTERM is received in the terminal.
The server is stopped automatically at interpreter exit, not when the loop
ends, so a per-scene interrupt never tears down the server.

### Stopping the whole script from the browser

A second, opt-in binding — default **Ctrl+Q** — sets the global shutdown event
(like a terminal Ctrl+C), so both `wait()` and every `animate()` loop end.
Unlike the per-scene `q` key, it is **disabled by default** to avoid accidental
termination. Enable it per scene with `enable_server_stop_key()`:

```python
from pytanga.viz import KeyModifier, Visualizer

viz = Visualizer()
viz.enable_server_stop_key()  # main scene: Ctrl+Q ends the whole script

# Or on a named scene (only that scene's tab may stop the server):
overview = viz.scene("overview")
overview.enable_server_stop_key(key="x", modifiers=[KeyModifier.CTRL, KeyModifier.SHIFT])
```

The `Visualizer(enable_server_stop_key=True)` constructor flag enables the
default Ctrl+Q binding for the **main scene**. Named scenes can opt in when
created via `viz.scene("name", enable_server_stop_key=True)`, or afterward via
their handle's `enable_server_stop_key()`. A scene without the binding can
still stop its own `animate()` loop (with `q`) but cannot end the script.

### `animate()` reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fps` | `float` | `60.0` | Target frames per second. `0` disables pacing so the loop body can call `sleep_ms()` itself. |
| `stop_key` | `str \| None` | `"q"` | Browser key that ends the loop (matches both `q` and `Q`). `None` disables the browser binding. |
| `stop_modifiers` | `Sequence[KeyModifier \| str] \| None` | `None` | Modifiers required alongside `stop_key` (`ctrl`, `shift`, `alt`, `meta`). |
| `scene_name` | `str` | `""` | Scene the loop (and its stop key) is scoped to. `""` is the main scene. |
| `auto_clear` | `bool` | `False` | When `True`, each frame flushes then removes objects added after the loop began (see below). |

- `animate()` starts the server automatically (headless) if it isn't running
  yet; it never opens the viewer — call `show()` first (or use `with viz:`).
- The browser binding is per scene: pressing `q` (or `Q`) in scene `A` stops only
  scene `A`'s loop; terminal Ctrl+C / SIGTERM is global and stops every scene.
- Use `update_entity()` to replace geometry and `flush()` to push changed state.
  Only entities marked dirty by the scene manager are serialized — stationary
  entities cost nothing.

### Add-per-frame with `auto_clear`

Instead of pre-creating objects, you can `add()` fresh objects every frame and
let `auto_clear=True` remove the previous frame's objects for you. Anything
added *before* the loop persists:

```python
import math
from pytanga.geometry import Point

viz = Visualizer()
viz.show()  # open the viewer
viz(Point(0, 0, 0), color="#ffffff")  # persists across frames

angle = 0.0
for dt in viz.animate(fps=60, auto_clear=True):
    angle += 3.0 * dt
    viz(Point(3 * math.cos(angle), 3 * math.sin(angle), 0), color="#ff4444")
    viz.flush()
```

Each frame flushes first (so the previous frame's additions appear), then
removes every object that was not present on the first frame. Labels created
alongside the added entities are removed too. Pre-creating objects with
`viz(...)` and updating them in place (above) remains the most efficient,
allocation-free loop.

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

- `interrupted()` returns `True` once Ctrl+C / SIGTERM has been received, or
  once the scene's browser stop key (default `q`) has been pressed
  (requires the server to be started so the signal handler is installed).
- `sleep_ms(ms)` sleeps for `ms` milliseconds, returning `False` early if an
  interrupt arrives, `True` otherwise. Use its result to pace *and* break
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
viz.show()

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
viz.stop_server()
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
