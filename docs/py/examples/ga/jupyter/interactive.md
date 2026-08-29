# Interactive Visualizer

**Keywords:** interactive · visualizer · context manager · show · display · notebook

The simplest way to show a scene in a notebook is the context manager — it clears the scene on entry and calls `show()` (which renders inline) on exit. `viz(...)` is shorthand for `viz.new(...)`.

## Source

[`ga/jupyter/interactive.ipynb`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/jupyter/interactive.ipynb)

## Code

````python
from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import Visualizer

viz = Visualizer()


with viz:  # clear + show on entry, flush on exit
    viz(Point(1, 2, 3), color="#ff4444")
    viz(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.3)
    viz(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.25)


viz(Point(4, 5, 6), color="#44ff44")
viz.show()  # no new viewer — just flushes the update


overview = viz.scene("overview")
detail = viz.scene("detail")

overview.add(Sphere(Point(0, 0, 0), radius=3), opacity=0.2)
detail.add(Sphere(Point(2, 1, 0), radius=1), opacity=0.8)

viz.display_row((overview, None), (detail, None), height=400)


viz.stop_server()
````
