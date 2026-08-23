# Scene Objects

Everything you can place in a scene with `add()` / `new()` (or the `viz(...)`
shorthand): geometric entities, transformation operators, axes/grid, point
paths, and the active (interactive) elements.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Entities](entities.ipynb) | Every geometric entity, its style class and parameters, with a live example |
| [Operators](operators.ipynb) | Versors (rotor, translator, motor, …) and their style classes/parameters |
| [Axes & Grid](axes-grid.md) | `Axes2D`/`Axes3D`, custom `Axis`, and `Grid` |
| [PointPath](point-path.md) | Trail/curve rendering with `PointPath` and `PointPathStyle` |
| [Active Elements](active-elements/index.md) | High-level interactive entities (`ActPoint`) |

## Quick reference

| Entity / Operator | Style class | Documented in |
|-------------------|-------------|---------------|
| Point | PointStyle / CrossHairPointStyle | [Entities](entities.ipynb) |
| Direction | DirectionStyle | [Entities](entities.ipynb) |
| HPoint | HPointStyle | [Entities](entities.ipynb) |
| PointPair / ImagPointPair | PointPairStyle | [Entities](entities.ipynb) |
| Line | LineStyle / CylinderLineStyle | [Entities](entities.ipynb) |
| Plane | PlaneStyle | [Entities](entities.ipynb) |
| Circle / ImagCircle | CircleStyle | [Entities](entities.ipynb) |
| Sphere / ImagSphere | SphereStyle | [Entities](entities.ipynb) |
| Space | SpaceStyle | [Entities](entities.ipynb) |
| ReflectionPlane / ReflectionLine | ReflectionPlaneStyle / ReflectionLineStyle | [Operators](operators.ipynb) |
| ReflectionPoint | ReflectionPointStyle | [Operators](operators.ipynb) |
| Inversion | InversionStyle | [Operators](operators.ipynb) |
| Rotor | RotorStyle | [Operators](operators.ipynb) |
| Translator | TranslatorStyle | [Operators](operators.ipynb) |
| Dilator | DilatorStyle | [Operators](operators.ipynb) |
| Motor | MotorStyle | [Operators](operators.ipynb) |
| GeneralRotor | GeneralRotorStyle | [Operators](operators.ipynb) |
| Axes2D / Axes3D / Axis / Grid | Axes2DStyle / Axes3DStyle / AxisStyle / GridStyle | [Axes & Grid](axes-grid.md) |
| PointPath | PointPathStyle | [PointPath](point-path.md) |

For the underlying geometry data classes, see
[Entity Data Classes](../../geometry/entities.md) and
[Operator Data Classes](../../geometry/operators.md). Runnable examples:
[`demo_all_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_all_entities.py)
and
[`demo_operators.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_operators.py).
