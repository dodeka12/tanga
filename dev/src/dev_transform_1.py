import math

from pytanga.basis import BasisN3
from pytanga.geometry import Direction, Geometry, Line, Motor, Point, Rotor, Translator
from pytanga.viz import LineStyle, PointStyle, Transform, Visualizer, VizGroup

N3 = BasisN3()
geo = Geometry(N3)

angle = math.radians(30)  # 30 degrees in radians
op = Motor(
    Rotor(angle, Direction(0, 0, 1)),
    Translator(Direction(math.sin(angle), math.cos(angle), 0)),
)

trans = Transform.from_operator(op)
print(trans.matrix())
