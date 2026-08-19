from pytanga.basis import BasisE3, BasisN3, BasisP3
from pytanga.geometry import Geometry, Line, Point

E3 = BasisE3()

a = E3("e1+e2")
b = E3("e3")

c = a.join(b)
c.show("c")

N3 = BasisN3()
geo = Geometry(N3)

print(N3.einf | N3.eo)
einf_inv = N3.einf.conj() / (N3.einf | N3.einf.conj())
einf_inv.show("einf_inv")
print(einf_inv | N3.einf)

a = geo(Point(1, 0, 0))
b = geo(Point(0, 1, 0))
print(a | a)
print(a | a.conj())
print(a | a.blade_pseudo_inverse())
print(a * a.blade_pseudo_inverse())

pp = a.op(b)
pp.show("pp")
x = pp | b.blade_pseudo_inverse()
x.show("x")
print(geo(x))
