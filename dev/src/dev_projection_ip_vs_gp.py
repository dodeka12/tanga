"""Test: inner product vs geometric product in the join's projection step.

Claim under test: replacing the geometric product ``wX * N^-1`` by the inner
product (contraction) ``wX | N^-1`` in the projection step of ``ProjectUnsafe``
  * changes nothing for non-degenerate blades, and
  * makes the pseudo-inverse usable for degenerate (null) blades.

Run:  uv run python dev/src/dev_projection_ip_vs_gp.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point, Sphere

N3 = BasisN3()
geo = Geometry(N3)


def blade_grade(mv):
    gs = mv.grades
    return gs[0] if len(gs) == 1 else (0 if not gs else gs)


def proj_gp_true(a, n):
    """Project a onto n: geometric product with the true inverse."""
    return (a | n) * n.blade_inverse()


def proj_gp_pseudo(a, n):
    """Project a onto n: geometric product with the pseudo-inverse."""
    return (a | n) * n.blade_pseudo_inverse()


def proj_ip_pseudo(a, n):
    """Project a onto n: inner product (contraction) with the pseudo-inverse."""
    return (a | n) | n.blade_pseudo_inverse()


def join_py(a, b, proj):
    """Mirror of GA::Join with a pluggable projection step."""
    ga = blade_grade(a)
    gb = blade_grade(b)
    if ga == 0 or gb == 0:
        res = b if ga == 0 else a
        return res / res.mag
    J = a if ga >= gb else b
    vec_n = (b if ga >= gb else a).blade_factorize()
    for _ in range(20):
        rejs = [n - proj(n, J) for n in vec_n]
        m2 = [r.mag2 for r in rejs]
        if max(m2) <= 1e-10:
            return J / J.mag
        i = max(range(len(rejs)), key=lambda k: m2[k])
        wV = rejs[i] / rejs[i].mag
        J = J ^ wV
    raise RuntimeError("join did not converge")


def report_join(label, a, b, proj):
    try:
        j = join_py(a, b, proj)
        print(f"  {label}: grades {j.grades}  {j.to_dict()}")
    except Exception as e:  # noqa: BLE001
        print(f"  {label}: raised {type(e).__name__}: {str(e).splitlines()[0]}")


# ---- 1. non-degenerate blade: projection equivalence ----------------------
S = 2 * N3.einf - N3.eo          # IPNS sphere, S^2 = 4
N = N3.e1 ^ S                    # non-degenerate bivector, N^2 = -4
a = N3.e2 + N3.eo + N3.einf

print(f"== non-degenerate blade N = e1 ^ (2 e∞ - e₀),  N² = {(N | N).scalar} ==")
pgp = proj_gp_true(a, N)
pip = proj_ip_pseudo(a, N)
pgp_p = proj_gp_pseudo(a, N)
print("  GP true   :", pgp.to_dict())
print("  IP pseudo :", pip.to_dict())
print("  GP pseudo :", pgp_p.to_dict())
print(f"  |GP true - IP pseudo| = {(pgp - pip).mag:.3g}   (0 would mean 'changes nothing')")

# ---- 2. null blade: projection grades -------------------------------------
N0 = N3.eo ^ N3.e1               # null bivector, N0^2 = 0
print(f"== null blade N0 = e₀ ^ e1,  N0² = {(N0 | N0).scalar} ==")
print("  GP pseudo grades:", proj_gp_pseudo(a, N0).grades, proj_gp_pseudo(a, N0).to_dict())
print("  IP pseudo grades:", proj_ip_pseudo(a, N0).grades, proj_ip_pseudo(a, N0).to_dict())

# ---- 3. join of two IPNS spheres (non-degenerate) -------------------------
s1 = geo(Sphere(Point(0, 0, 0), 2)).dual()
s2 = geo(Sphere(Point(1, 0, 0), 2)).dual()
print("== join of two IPNS spheres (non-degenerate; correct grade = 2) ==")
report_join("GP true  ", s1, s2, proj_gp_true)
report_join("IP pseudo", s1, s2, proj_ip_pseudo)

# ---- 4. join of two conformal points (null) -------------------------------
p1 = geo(Point(0, 0, 0))
p2 = geo(Point(1, 0, 0))
line = p1 ^ p2
print(f"== join of two conformal points (null); correct line = p1^p2, grades {line.grades} ==")
report_join("GP true  ", p1, p2, proj_gp_true)
report_join("IP pseudo", p1, p2, proj_ip_pseudo)
