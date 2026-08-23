# Operators

Operators are versors (geometric transformations) — rotation, translation,
reflection, inversion, dilation — that you can visualize directly in a scene.
Each operator has a dedicated style class controlling its appearance.

For the underlying data classes and their algebra coverage, see
[Operator Data Classes](../../geometry/operators.md). Runnable example:
[`demo_operators.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_operators.py).

## Quick reference

| Operator | Style class | Style fields |
|---|---|---|
| ReflectionPlane (`Reflection`) | ReflectionPlaneStyle | color, opacity, extent |
| ReflectionLine | ReflectionLineStyle | color, opacity, length, thickness |
| ReflectionPoint | ReflectionPointStyle | color, opacity, extent |
| Inversion | InversionStyle | color, opacity |
| Rotor | RotorStyle | color, opacity, disc_radius |
| Translator | TranslatorStyle | color, opacity, length |
| Dilator | DilatorStyle | color, opacity, ring_count, max_radius |
| Motor | MotorStyle | color, opacity |
| GeneralRotor | GeneralRotorStyle | color, opacity |

!!! note "`ReflectionPointStyle` is not top-level exported"
    `ReflectionPointStyle` is defined in `pytanga.viz._styles` but is **not**
    exported from the top-level `pytanga.viz` namespace. Import it from
    `pytanga.viz._styles` if you need to override point-reflection defaults.

## Example

```python
import math
from pytanga.geometry import Dilator, Direction, Motor, Point, Rotor, Translator
from pytanga.viz import Visualizer

viz = Visualizer(title="Tanga — Operators")

viz.new(Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)), label="Rotor")
viz.new(Translator(vector=Direction(2, 0, 0)), color="#44aaff", label="Translator")
viz.new(
    Motor(
        rotor=Rotor(angle=math.pi * 1.5, axis=Direction(0, 0, 1)),
        translator=Translator(vector=Direction(0, 1, 0)),
    ),
    color="#ff66cc",
    label="Motor",
)
viz.new(Dilator(factor=2.0, origin=Point(0, 0, 0)), color="#ffcc44", label="Dilator")

viz.show()
viz.wait()
```

All operator style fields default to `None` and fall back to the visualizer's
canonical defaults, exactly like entity styles (see
[Style System](../styles/styles.md)).
