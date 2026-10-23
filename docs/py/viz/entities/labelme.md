# labelme

`pytanga.viz.labelme` loads/stores the
[labelme](https://github.com/wkentaro/labelme) JSON annotation format and maps
every shape type to a constant geometry entity or an active composite.

## Data model

```python
@dataclass
class LabelShape:
    label: str
    points: list[tuple[float, float]]   # image coords (y-down pixels)
    shape_type: str                     # rectangle|circle|ellipse|polygon|line|linestrip|point
    group_id: int | None = None
    description: str = ""
    flags: dict[str, Any] = field(default_factory=dict)
    radius_u: float | None = None       # ellipse scalar params (new form)
    radius_v: float | None = None
    angle: float | None = None

@dataclass
class LabelMeDocument:
    shapes: list[LabelShape]
    image_path: str = ""
    image_height: int | None = None
    image_width: int | None = None
    image_data: str | None = None
    version: str = "5.0.1"
    flags: dict[str, Any] = field(default_factory=dict)
```

## Store

```python
from pytanga.viz import LabelMeStore

store = LabelMeStore(allow_extensions=True)   # allow the non-standard `ellipse` type
doc = store.load("labels.json")               # or store.loads(text)
store.save(doc, "labels.json")                # or store.dumps(doc)

objs = store.add_shapes(handle, doc, active=True)      # add as act composites
pairs = store.iter_objects(doc, active=False)          # (entity, label) without adding
shapes = store.shapes_from_objects([(act, "car"), ...])  # inverse (save direction)
```

## Shape-type mapping

| shape_type | entity (`active=False`) | active (`active=True`) | points |
|---|---|---|---|
| `rectangle` | `Rectangle2D` | `ActRectangle2D` | 2 opposite corners |
| `circle` | `Circle` | `ActCircle` | `[center, rim]` |
| `ellipse` *(ext.)* | `Ellipse` | `ActEllipse` | `[center]` + `radius_u`/`radius_v`/`angle` |
| `polygon` | `PointPath` (closed) | `ActPolygon` (closed) | vertex list |
| `linestrip` | `PointPath` (open) | `ActPolygon` (open) | vertex list |
| `line` | `Line` | `ActLine` | 2 points |
| `point` | `Point` | `ActPoint` | 1 point |

labelme `polygon` is closed by definition; open polylines map to `linestrip`
(and two-point open paths to `line`). `allow_extensions=False` maps an ellipse
back to `circle` (equal radii) or a sampled 32-point `polygon`, and never emits
`ellipse`.

An `ellipse` is stored in pytanga's canonical scalar form — `points=[center]`
plus the top-level `radius_u`, `radius_v`, and `angle` (radians, from image
horizontal) keys.  The legacy `[center, rim_u, rim_v]` form is still accepted on
load for backward compatibility, but only the scalar form is written.

Shapes loaded through a mapper round-trip to the same pixels when saved through
the same mapper — including through an interactive act (`LabelMeStore.to_act`).

See the [`image_labeling_app.py`](../../examples/apps/image_labeling_app.md)
example for an end-to-end labeling app that uses the store.
