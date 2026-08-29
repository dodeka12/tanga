# Animation

**Keywords:** animation · notebook · auto_clear · update in place · animate

Two ways to animate in a notebook: pre-create objects and update them in place (efficient), or add fresh objects each frame with `auto_clear=True`.

## Source

[`ga/jupyter/animation.ipynb`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/jupyter/animation.ipynb)

## Code

````python
import math

from pytanga.geometry import Point
from pytanga.viz import Visualizer

viz = Visualizer()
viz.show()  # start the server and render inline


p = viz(Point(3, 0, 0), color="#ff4444")  # viz(...) == viz.new(...)

angle = 0.0
for dt in viz.animate(fps=30):
    angle += 3.0 * dt
    p.entity = Point(3 * math.cos(angle), 3 * math.sin(angle), 0)
    viz.flush()
    if angle > 2 * math.pi:  # one full orbit
        break


viz(Point(0, 0, 0), color="#ffffff")  # persists across frames

angle = 0.0
for dt in viz.animate(fps=30, auto_clear=True):
    angle += 3.0 * dt
    viz(Point(3 * math.cos(angle), 3 * math.sin(angle), 0), color="#ff4444")
    viz.flush()
    if angle > 2 * math.pi:
        break
````
