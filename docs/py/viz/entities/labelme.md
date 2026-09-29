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
| `ellipse` *(ext.)* | `Ellipse` | `ActEllipse` | `[center, rim_u, rim_v]` |
| `polygon` | `PointPath` (closed) | `ActPolygon` (closed) | vertex list |
| `linestrip` | `PointPath` (open) | `ActPolygon` (open) | vertex list |
| `line` | `Line` | `ActLine` | 2 points |
| `point` | `Point` | `ActPoint` | 1 point |

labelme `polygon` is closed by definition; open polylines map to `linestrip`
(and two-point open paths to `line`). `allow_extensions=False` maps an ellipse
back to `circle` (equal radii) or a sampled 32-point `polygon`, and never emits
`ellipse`.

See the [`image_labeling_app.py`](../../examples/apps/image_labeling_app.md)
example for an end-to-end labeling app that uses the store.
