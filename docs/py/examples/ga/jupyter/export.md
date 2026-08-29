# Export

**Keywords:** export · notebook · HTML · glTF · snapshot · figure

Exports read directly from the in-memory scene — no server required. They work even while the live viewer is running.

## Source

[`ga/jupyter/export.ipynb`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/jupyter/export.ipynb)

## Code

````python
from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import Visualizer

viz = Visualizer()
viz(Point(2, 0, 0), color="#ff4444")
viz(Point(0, 2, 0), color="#44ff44")
viz(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.3)
viz(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.25)


viz.export_snapshot("scene.html")  # self-contained HTML
viz.export_glb("scene.glb")  # glTF binary for Blender / <model-viewer>
viz.export_figure("figure.html")  # embeddable presentation snippet


viz.display_snapshot()
````
