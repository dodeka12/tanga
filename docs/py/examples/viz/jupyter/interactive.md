# Interactive Visualizer

**Keywords:** interactive · visualizer · context manager · show · display · notebook · re-run · singleton

The simplest way to show a scene in a notebook is the context manager — it clears the scene on entry and calls `show()` (which renders inline) on exit. `viz(...)` is shorthand for `viz.new(...)`.

Under Jupyter, `Visualizer()` is a **singleton**: re-running a cell that re-creates it reuses the same instance (one server, one scene host) and clears the default scene, so every cell below is safe to re-run.

## Source

[`viz/jupyter/interactive.ipynb`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/jupyter/interactive.ipynb)

## Code

````python
from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import SphereStyle, Visualizer


with Visualizer() as viz:  # clear + show on entry, flush on exit
    viz(Point(1, 2, 3), color="#ff4444")
    viz(Sphere(Point(0, 0, 0), radius=2.5))
    viz(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.25)


# Re-running this cell resets the default scene instead of accumulating.
viz = Visualizer()
viz.add(Point(1, 0, 1), color="#888888")
viz.show()


viz(Point(4, 5, 6), color="#44ff44")
viz.show()  # no new viewer — just flushes the update


# Re-running this cell clears "staging" first, then re-adds its content.
staging = viz.scene("staging")
staging.add(Sphere(Point(1, 0, 0), radius=1), opacity=0.8)
staging.show()


overview = viz.scene("overview")
detail = viz.scene("detail")

overview.add(Sphere(Point(0, 0, 0), radius=3), opacity=0.2)
detail.add(Sphere(Point(2, 1, 0), radius=1), opacity=0.8)

# Label each pane so it can be addressed individually later.
viz.display_row((overview, "left"), (detail, "right"), height=400)



# Later: switch only the "left" pane to the detail scene.
viz.navigate_to("detail", target="viewer:left")


viz.stop_server()
````
