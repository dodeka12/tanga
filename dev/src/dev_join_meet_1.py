"""Diagnostic / regression script for the join of conformal (N3) spheres.

``s1_d`` and ``s2_d`` are the IPNS representation of two spheres, i.e.
grade-1 vectors, so their join can at most be a bivector.

This script mirrors the C++ ``GA::Join`` algorithm (``cpp/Tan.GA/MV_Blade_Ops.h``)
in pure Python using pytanga operations, and verifies that the built-in
``join`` now returns the correct bivector.  The fix was to make
``ProjectUnsafe`` use the true blade inverse for non-degenerate blades instead
of the pseudo-inverse; the pure-python ``join_py`` mirrors the (now fixed)
C++ algorithm and each intermediate step is printed.
"""

import sys

# The Windows console defaults to cp1252; the rich-based ``MV.show()`` emits
# the wedge glyph, so switch stdout to UTF-8 to avoid a UnicodeEncodeError.
sys.stdout.reconfigure(encoding="utf-8")

from pytanga.basis import BasisE3, BasisN3, BasisP3
from pytanga.geometry import Geometry, Line, Point, Sphere

N3 = BasisN3()
geo = Geometry(N3)


def blade_grade(mv):
    """Grade of a pure blade (0 for a scalar)."""
    grades = mv.grades
    if not grades:
        return 0
    if len(grades) != 1:
        raise ValueError(f"expected a pure blade, got grades {grades}")
    return grades[0]


def join_py(a, b, *, precision: float = 1e-10, verbose: bool = True):
    """Pure-python mirror of ``GA::Join(a, b)``.

    Steps (identical to the C++ implementation):

    1. Let ``J`` be the blade of higher grade and factorize the lower-grade
       blade into an orthonormal set ``{n_j}`` via ``blade_factorize()``.
    2. Repeat:
       a. Reject every ``n_j`` from ``J`` (``proj = n_j.project(J)``, then
          ``rej = n_j - proj``).
       b. If the largest rejection magnitude is below *precision*, return
          the normalized ``J``.
       c. Otherwise wedge the normalized largest rejection onto ``J``.
    """
    ga = blade_grade(a)
    gb = blade_grade(b)

    # Scalar input spans the trivial subspace; the join is the other blade.
    if ga == 0 or gb == 0:
        result = b if ga == 0 else a
        return result / result.mag

    if ga >= gb:
        J = a
        vec_n = b.blade_factorize()
    else:
        J = b
        vec_n = a.blade_factorize()

    it = 0
    while True:
        it += 1

        # Reject each factor n_j from the current join blade J, using the
        # existing multivector projection (ProjectUnsafe in C++).
        vec_rej = []
        for n in vec_n:
            proj = n.project(J)
            vec_rej.append(n - proj)

        # Pick the factor with the largest squared coefficient magnitude.
        max_mag2 = 0.0
        max_idx = 0
        for i, rej in enumerate(vec_rej):
            m2 = rej.mag2
            if m2 > max_mag2:
                max_mag2 = m2
                max_idx = i

        if verbose:
            print(
                f"  join_py iter {it}: grade(J)={blade_grade(J)}, "
                f"max|rej|^2={max_mag2:.3g}"
            )

        if max_mag2 <= precision:
            return J / J.mag

        wV = vec_rej[max_idx] / vec_rej[max_idx].mag
        J = J ^ wV


def join_py_fixed(a, b, *, precision: float = 1e-10, verbose: bool = True):
    """Same join algorithm as :func:`join_py`, using the proper blade inverse directly.

    ``MV.project()`` now uses the true inverse for non-degenerate blades, so
    this is equivalent to :func:`join_py`.  It is kept here to demonstrate the
    equivalence: ``(n | J) * J.blade_inverse()`` vs ``n.project(J)``.
    """
    ga = blade_grade(a)
    gb = blade_grade(b)

    # Scalar input spans the trivial subspace; the join is the other blade.
    if ga == 0 or gb == 0:
        result = b if ga == 0 else a
        return result / result.mag

    if ga >= gb:
        J = a
        vec_n = b.blade_factorize()
    else:
        J = b
        vec_n = a.blade_factorize()

    it = 0
    while True:
        it += 1

        # Reject each factor n_j from J using the proper blade inverse.
        vec_rej = []
        for n in vec_n:
            proj = (n | J) * J.blade_inverse()
            vec_rej.append(n - proj)

        max_mag2 = 0.0
        max_idx = 0
        for i, rej in enumerate(vec_rej):
            m2 = rej.mag2
            if m2 > max_mag2:
                max_mag2 = m2
                max_idx = i

        if verbose:
            print(
                f"  join_py_fixed iter {it}: grade(J)={blade_grade(J)}, "
                f"max|rej|^2={max_mag2:.3g}"
            )

        if max_mag2 <= precision:
            return J / J.mag

        wV = vec_rej[max_idx] / vec_rej[max_idx].mag
        J = J ^ wV


s1 = geo(Sphere(Point(0, 0, 0), 2))
s1.show("s1")
s2 = geo(Sphere(Point(1, 0, 0), 2))
s2.show("s2")

s1_d = s1.dual()
s1_d.show("s1_d")
s2_d = s2.dual()
s2_d.show("s2_d")

print(f"s1_d grades = {s1_d.grades}")
print(f"s2_d grades = {s2_d.grades}")

s1_d_fac = s1_d.blade_factorize()
print("s1_d.blade_factorize() =", [f.grades for f in s1_d_fac], s1_d_fac)
s2_d_fac = s2_d.blade_factorize()
print("s2_d.blade_factorize() =", [f.grades for f in s2_d_fac], s2_d_fac)

# Built-in (C++) join.
s12_d = s1_d.join(s2_d)
s12_d.show("s12_d (built-in)")
print("built-in join grades =", s12_d.grades)

# Pure-python re-implementation of the same algorithm.
print("--- join_py ---")
s12_py = join_py(s1_d, s2_d, precision=N3.precision)
s12_py.show("s12_d (join_py)")
print("join_py grades =", s12_py.grades)

# ---------------------------------------------------------------------------
# The bug (now fixed): ``MV.project()`` (wrapping the C++ ``ProjectUnsafe``)
# used to compute the projection as ``(a | N) * PseudoInverseBlade(N)``, where
# ``PseudoInverseBlade(N) = conjugate(N) / IP(N, conjugate(N))``.  For a
# non-degenerate blade in a mixed-signature metric (N3 = Cl(4,1)) this is NOT
# the true inverse ``reverse(N) / IP(N, reverse(N))``, so projecting a vector
# onto a 1D blade did not land along that blade, which broke the join
# invariant and grew an extra grade.  ``ProjectUnsafe`` now uses the true
# inverse for non-degenerate blades (falling back to the pseudo-inverse only
# for null blades, which have no true inverse).
# ---------------------------------------------------------------------------
n = s2_d.blade_factorize()[0]

proj_builtin = n.project(s1_d)                  # now uses the true inverse
proj_proper = (n | s1_d) * s1_d.blade_inverse()  # explicit true inverse

print("projection of n onto the line s1_d (should be parallel to s1_d):")
print("  via project()       (proj ^ s1_d).mag2 =", f"{(proj_builtin ^ s1_d).mag2:.3g}")
print("  via blade_inverse() (proj ^ s1_d).mag2 =", f"{(proj_proper ^ s1_d).mag2:.3g}")

# With the proper inverse the same join algorithm stops at the bivector.
print("--- join_py_fixed (proper inverse) ---")
s12_fixed = join_py_fixed(s1_d, s2_d, precision=N3.precision)
s12_fixed.show("s12_d (join_py_fixed)")
print("join_py_fixed grades =", s12_fixed.grades)

c1 = s1.meet(s2)
c1.show("c1")
print(geo(c1))
