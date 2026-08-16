from pytanga.basis import BasisN2, BasisN3, BasisPGA3
from pytanga.geometry import Circle, Direction, Geometry, Point, Sphere, Translator

N2 = BasisN2()
geo = Geometry(N2)

circle = geo(Circle(center=Point(0, 0, 0), radius=1))
circle.show("circle")
ana = geo.analyze(circle)
print(ana)

A = geo.create(Point(-1, 0))
B = geo.create(Point(1, 0))
C = geo.create(Point(0, 1))
A.show("A")
B.show("B")
C.show("C")
circle2 = A ^ B ^ C
circle2.show("circle2")
ana2 = geo.analyze(circle2)
print(ana2)

circle2.dual().show("dual")
# print(circle2 * circle2)
# print(circle2.dual() | N2.einf)
# print(circle ^ B)
# print(circle2 ^ A)
