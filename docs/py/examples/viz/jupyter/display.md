# 

**Keywords:** 

## Source

[`viz/jupyter/display.ipynb`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/jupyter/display.ipynb)

## Code

````python
from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import SphereStyle, Visualizer

viz = Visualizer() 
viz(Point(1, 2, 3), color="#ff4444")
viz(Sphere(Point(0, 0, 0), radius=2.5))
viz(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.25)
# viz.show()
viz.display_snapshot()
````
