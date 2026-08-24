# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for blade operations exposed from MV_Blade_Ops.h."""

import pytest
import numpy as np
import pytanga
from pytanga.basis import BasisE3, BasisN3


@pytest.fixture(scope="module")
def e3():
    """E3 basis — cached for the whole test module."""
    return BasisE3()


# ---------------------------------------------------------------------------
# InverseBlade tests
# ---------------------------------------------------------------------------
def test_blade_inverse_vector(e3):
    """InverseBlade of a vector e1 should give e1 itself."""
    e1 = e3.e1
    inv = e1.blade_inverse()

    chk = e1 * inv
    assert abs(chk.scalar - 1.0) < 1e-8, "GP(e1, inv(e1)) scalar should be 1"


def test_blade_inverse_bivector(e3):
    """InverseBlade of a bivector e1^e2."""
    e1 = e3.e1
    e2 = e3.e2
    bivec = e1 ^ e2
    inv = bivec.blade_inverse()

    chk = bivec * inv
    assert abs(chk.scalar - 1.0) < 1e-8, "Scalar part of biv * inv(biv) should be 1"


# ---------------------------------------------------------------------------
# PseudoInverseBlade tests
# ---------------------------------------------------------------------------
def test_blade_pseudo_inverse_vector(e3):
    """PseudoInverseBlade of e1 (same as inverse in Euclidean E3)."""
    e1 = e3.e1
    inv = e1.blade_pseudo_inverse()

    chk = e1 * inv
    assert abs(chk.scalar - 1.0) < 1e-8, "Scalar part of e1 * pseudoInv(e1) should be 1"


# ---------------------------------------------------------------------------
# Project tests
# ---------------------------------------------------------------------------
def test_project_vector_onto_bivector(e3):
    """Project e1+e2 onto bivector e1^e2 — should recover full vector."""
    e1 = e3.e1
    e2 = e3.e2
    n_blade = e1 ^ e2
    a = e1 + e2

    proj = a.project(n_blade)
    diff = proj - a
    assert diff.mag < 1e-8, "Project of e1+e2 onto e1^e2 should recover e1+e2"


# ---------------------------------------------------------------------------
# Reject tests
# ---------------------------------------------------------------------------
def test_reject_vector_from_bivector(e3):
    """Reject e1+e2+e3 from e1^e2 — should give e3."""
    e1 = e3.e1
    e2 = e3.e2
    e3v = e3.e3

    n_blade = e1 ^ e2
    a = e1 + e2 + e3v

    rej = a.reject(n_blade)
    diff = rej - e3v
    assert diff.mag < 1e-8, "Reject of e1+e2+e3 from e1^e2 should be e3"


def test_project_reject_reconstruction(e3):
    """Project + Reject should reconstruct the original multivector."""
    e1 = e3.e1
    e2 = e3.e2
    e3v = e3.e3
    a = e1 * 2 + e2 * 3 + e3v * 4
    n_blade = e3v

    proj = a.project(n_blade)
    rej = a.reject(n_blade)
    s = proj + rej
    diff = s - a
    assert diff.mag < 1e-8, "Proj + Rej should reconstruct A"


# ---------------------------------------------------------------------------
# FactorizeBlade tests
# ---------------------------------------------------------------------------
def test_factorize_blade(e3):
    """Factorize bivector e1^e2 into two orthogonal vectors."""
    e1 = e3.e1
    e2 = e3.e2
    bivec = e1 ^ e2

    factors = bivec.blade_factorize()
    assert len(factors) == 2, "Bivector should factor into 2 vectors"

    reconstructed = factors[0] ^ factors[1]
    # IP(reconstructed, reverse(original)) should equal mag(original)*mag(reconstructed)
    ip_val = (reconstructed.ip_rev(bivec, rev_self=False, rev_other=True)).scalar
    expected = bivec.mag * reconstructed.mag
    assert abs(ip_val - expected) < 1e-8, (
        "Factorized vectors should reconstruct original blade (up to scale)"
    )


# ---------------------------------------------------------------------------
# Join tests
# ---------------------------------------------------------------------------
def test_join_adjacent(e3):
    """Join of e1 and e2 should contain both vectors."""
    e1 = e3.e1
    e2 = e3.e2
    j = e1.join(e2)

    rej1 = e1.reject(j)
    assert rej1.mag < 1e-8, "Rejection of e1 from Join(e1, e2) should be zero"

    rej2 = e2.reject(j)
    assert rej2.mag < 1e-8, "Rejection of e2 from Join(e1, e2) should be zero"


def test_join_disjoint(e3):
    """Join of e1 and e3 (disjoint) should contain both."""
    e1 = e3.e1
    e3v = e3.e3
    j = e1.join(e3v)

    rej1 = e1.reject(j)
    assert rej1.mag < 1e-8, "Join(e1, e3) should contain e1"

    rej3 = e3v.reject(j)
    assert rej3.mag < 1e-8, "Join(e1, e3) should contain e3"


def test_join_non_orthonormal(e3):
    """Join of a non-unit blade (e1+e2) with e3 must terminate and contain both."""
    a = e3.e1 + e3.e2
    b = e3.e3
    j = a.join(b)

    rej_a = a.reject(j)
    assert rej_a.mag < 1e-8, "Join(e1+e2, e3) should contain e1+e2"

    rej_b = b.reject(j)
    assert rej_b.mag < 1e-8, "Join(e1+e2, e3) should contain e3"


def test_meet_planes(e3):
    """Meet of two planes e1^e2 and e1^e3 should be the e1 line."""
    plane1 = e3.e1 ^ e3.e2
    plane2 = e3.e1 ^ e3.e3
    m = plane1.meet(plane2)

    rej = e3.e1.reject(m)
    assert rej.mag < 1e-8, "Meet(e1^e2, e1^e3) should contain e1"

    # The meet is exactly the e1 line: wedging it with e1 gives zero
    assert (m ^ e3.e1).mag < 1e-8, "Meet(e1^e2, e1^e3) should be the e1 line"


def test_meet_with_pseudoscalar(e3):
    """Meet of a bivector with the pseudoscalar should be the bivector.

    Regression: the dual of the pseudoscalar is a scalar (grade 0), which
    cannot be factorized into vectors; Join must short-circuit this case.
    """
    bivec = e3.e1 ^ e3.e2
    pseudoscalar = e3.I

    m = bivec.meet(pseudoscalar)
    assert (m - bivec).mag < 1e-8 or (m + bivec).mag < 1e-8, (
        "Meet(e1^e2, I) should be e1^e2 (up to sign)"
    )

    m = pseudoscalar.meet(bivec)
    assert (m - bivec).mag < 1e-8 or (m + bivec).mag < 1e-8, (
        "Meet(I, e1^e2) should be e1^e2 (up to sign)"
    )

    m = pseudoscalar.meet(pseudoscalar)
    assert (m - pseudoscalar).mag < 1e-8 or (m + pseudoscalar).mag < 1e-8, (
        "Meet(I, I) should be I (up to sign)"
    )


# ---------------------------------------------------------------------------
# FactorizeVersor tests
# ---------------------------------------------------------------------------
def test_factorize_versor(e3):
    """Factorize versor e1 * e2 (geometric product of two vectors)."""
    e1 = e3.e1
    e2 = e3.e2
    versor = e1 * e2  # e1*e2 = e1^e2 since orthogonal

    scale, factors = versor.blade_factorize_versor()
    assert len(factors) >= 2, "Versor e1*e2 should produce at least 2 factors"

    # Reconstruct: factors are extracted right-to-left, so reconstruct in REVERSE order
    reconstructed = scale
    for f in reversed(factors):
        reconstructed = reconstructed * f

    diff = reconstructed - versor
    assert diff.mag < 1e-8, "Reconstructed versor should equal original V"


def test_factorize_versor_g5():
    """Factorize a random versor in G(5)."""
    alg = pytanga.Algebra(5, 0)
    rng = np.random.default_rng(42)

    # Start with scalar 1, then multiply by 4 random vectors (matching C++ test)
    versor = alg.multivector({0: 1.0})

    for _ in range(4):
        vec = alg()
        for bit in range(5):
            val = rng.uniform(-2.0, 2.0)
            if abs(val) > 1e-12:
                vec[1 << bit] = val
        versor = versor * vec

    scale, factors = versor.blade_factorize_versor()

    # Reconstruct in reverse order
    reconstructed = scale
    for f in reversed(factors):
        reconstructed = reconstructed * f

    diff = reconstructed - versor
    assert diff.mag < 1e-4, "G(5) random versor reconstruction should match original"


def _reconstruct_versor(scale, factors):
    """Reconstruct a versor from ``blade_factorize_versor``'s return value.

    ``FactorizeVersor`` peels factors right-to-left, so the versor equals
    ``scale`` times the factors multiplied in reverse order.
    """
    r = scale
    for f in reversed(factors):
        r = r * f
    return r


def _versor_up_to_scale(mv):
    """Normalize a versor by its scalar part for up-to-scale comparison.

    In the degenerate conformal metric a versor with null factors (translator,
    dilator, motor) loses its scalar scale during factorization, so the
    reconstructed versor matches the input only up to a scalar multiple.
    Dividing both sides by the scalar part removes that ambiguity.
    """
    s = mv.scalar
    assert abs(s) > 1e-12, "versor must have a non-zero scalar part"
    return mv / s


# ---------------------------------------------------------------------------
# N3 (conformal) regression tests — ProjectUnsafe must use the true inverse
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def n3():
    """N3 basis (conformal model Cl(4,1)) — cached for the whole module."""
    return BasisN3()


def test_join_ipns_spheres_n3_is_bivector(n3):
    """Join of two IPNS sphere vectors must be a bivector.

    Regression: ``ProjectUnsafe`` used the pseudo-inverse
    ``conjugate(N) / IP(N, conjugate(N))``, which differs from the true inverse
    ``reverse(N) / IP(N, reverse(N))`` for a non-degenerate blade in a
    mixed-signature metric.  That made the join grow an extra grade
    (trivector instead of bivector).
    """
    from pytanga.geometry import Geometry, Point, Sphere

    geo = Geometry(n3)
    s1 = geo(Sphere(Point(0, 0, 0), 2)).dual()
    s2 = geo(Sphere(Point(1, 0, 0), 2)).dual()

    assert s1.grades == [1]
    assert s2.grades == [1]

    j = s1.join(s2)
    assert j.grades == [2]

    # The join must contain both input vectors.
    assert s1.reject(j).mag < 1e-8
    assert s2.reject(j).mag < 1e-8


def test_factorize_point_pair_n3_clean_factors(n3):
    """Factorizing a point pair yields two clean grade-1 factors.

    Regression: the basis-projection step inside ``FactorizeBlade`` also used
    the pseudo-inverse, returning a mixed-grade (grade 1 + 3) first factor.
    """
    from pytanga.geometry import Geometry, Point

    geo = Geometry(n3)
    pp = geo(Point(0, 0, 0)) ^ geo(Point(1, 0, 0))

    factors = pp.blade_factorize()
    assert len(factors) == 2
    for f in factors:
        assert f.grades == [1]

    # The factors span the same plane as the original point pair.
    recon = factors[0] ^ factors[1]
    assert pp.reject(recon).mag < 1e-8


def test_join_conformal_points_n3_is_bivector(n3):
    """Join of two conformal points (null vectors) must be a bivector.

    Regression: ``Join`` rejected each factor from ``J`` using projection and
    rejection, which is undefined for a null blade (a conformal point squares
    to zero), so joining two points threw ``PseudoInverseBlade: Blade is not
    pseudo-invertible``.  The join now uses the metric-free wedge test
    ``J ^ n_j == 0``.
    """
    from pytanga.geometry import Geometry, Point

    geo = Geometry(n3)
    p1 = geo(Point(0, 0, 0))
    p2 = geo(Point(1, 0, 0))

    assert p1.grades == [1]
    assert p2.grades == [1]
    assert abs(p1.ip(p1).scalar) < 1e-10  # conformal points are null vectors

    j = p1.join(p2)
    assert j.grades == [2]

    # Both points must be contained in the join (x contained in J iff x ^ J == 0).
    assert (p1 ^ j).mag < 1e-8
    assert (p2 ^ j).mag < 1e-8


def test_join_point_sphere_n3_is_bivector(n3):
    """Join of a null conformal point and a non-null IPNS sphere is a bivector."""
    from pytanga.geometry import Geometry, Point, Sphere

    geo = Geometry(n3)
    p = geo(Point(0, 0, 0))
    s = geo(Sphere(Point(1, 0, 0), 2)).dual()

    assert s.grades == [1]

    j = p.join(s)
    assert j.grades == [2]
    assert (p ^ j).mag < 1e-8
    assert (s ^ j).mag < 1e-8


def test_join_equal_points_n3_is_vector(n3):
    """Join of a conformal point with itself stays grade-1."""
    from pytanga.geometry import Geometry, Point

    geo = Geometry(n3)
    p = geo(Point(1, 2, 3))

    j = p.join(p)
    assert j.grades == [1]
    assert (p ^ j).mag < 1e-8


def test_factorize_null_bivector_n3_clean_factors(n3):
    """Factorizing a null bivector yields clean grade-1 factors.

    Regression: the projection-based factorization used the pseudo-inverse
    for null blades, returning a mixed-grade (grade 1 + 3) first factor and
    failing to reconstruct the blade.  ``FactorizeBlade`` now extracts factors
    metric-free (Option A probe, with a null-space fallback).
    """
    t = 0.5 * n3.e1 + 0.3 * n3.e2 + 0.1 * n3.e3
    b = t ^ n3.einf
    assert abs(b.ip(b).scalar) < 1e-10  # null bivector

    factors = b.blade_factorize()
    assert len(factors) == 2
    for f in factors:
        assert f.grades == [1]

    # The factors span the same subspace as the original null bivector.
    recon = factors[0] ^ factors[1]
    assert (b ^ recon).mag < 1e-8


def test_meet_conformal_points_n3(n3):
    """Meet of two distinct conformal points is a scalar (empty intersection)."""
    from pytanga.geometry import Geometry, Point

    geo = Geometry(n3)
    p1 = geo(Point(0, 0, 0))
    p2 = geo(Point(1, 0, 0))

    m = p1.meet(p2)
    assert m.grades == [0]

    # A point met with itself is the point.
    m_self = p1.meet(p1)
    assert m_self.grades == [1]


def test_meet_spheres_n3_round_trip(n3):
    """Meet of two OPNS spheres round-trips to their intersection circle.

    Two spheres of radius 2, centred at (0,0,0) and (1,0,0), intersect in a
    circle centred at (0.5,0,0) with radius sqrt(2^2 - 0.5^2).
    """
    from pytanga.geometry import Circle, Geometry, Point, Sphere

    geo = Geometry(n3)
    s1 = geo(Sphere(Point(0, 0, 0), 2))
    s2 = geo(Sphere(Point(1, 0, 0), 2))

    m = s1.meet(s2)
    c = geo(m)
    assert isinstance(c, Circle)
    assert abs(c.center.x - 0.5) < 1e-6
    assert abs(c.center.y) < 1e-6
    assert abs(c.center.z) < 1e-6
    assert abs(c.radius - (4 - 0.25) ** 0.5) < 1e-6


def test_factorize_versor_motor_n3(n3):
    """A conformal Motor (grades {0,2,4}) factorizes into 4 grade-1 factors.

    Regression: null factors (from the degenerate conformal metric) used to
    make the versor factorization return the wrong factor count.  The motor
    also round-trips: its factors reconstruct it up to scale.
    """
    from pytanga.geometry.create_n3 import create_motor
    from pytanga.geometry.entities import Direction, Point
    from pytanga.geometry.operators import GeneralRotor, Translator

    # Translation along the rotation axis (z) keeps the grade-4 part non-zero.
    motor = create_motor(
        n3,
        GeneralRotor(angle=0.7, axis=Direction(0, 0, 1), origin=Point(0, 0, 0)),
        Translator(vector=Direction(0, 0, 1)),
    )
    assert sorted(motor.grades) == [0, 2, 4]

    scale, factors = motor.blade_factorize_versor()
    assert len(factors) == 4
    for f in factors:
        assert f.grades == [1]

    # A motor has null factors, so compare the reconstruction up to scale.
    recon = _reconstruct_versor(scale, factors)
    diff = _versor_up_to_scale(recon) - _versor_up_to_scale(motor)
    assert diff.mag < 1e-8


def test_factorize_versor_null_vector_scale_fallback(n3):
    """A null vector versor falls back to a unit scale.

    Regression: ``FactorizeVersor`` peeled the (null) factor via the geometric
    product, yielding scale 0, so a null vector versor (e.g. ``e_inf``) got a
    zero scale.  It now substitutes a unit scale when the computed scale is
    zero, while keeping the exact scale for non-degenerate versors.
    """
    einf = n3.einf
    scale, factors = einf.blade_factorize_versor()
    assert len(factors) == 1
    assert abs(scale.scalar - 1.0) < 1e-8


def test_factorize_versor_translator_n3_round_trip(n3):
    """A translator round-trips through versor factorization up to scale.

    A translator is the geometric product of two parallel reflection planes:
    their absolute positions are irrelevant (only their separation sets the
    displacement), so one plane may pass through the origin.  It therefore
    factorizes into exactly two grade-1 factors.  Because the conformal
    metric is degenerate the scalar scale is lost, so compare the
    reconstruction up to scale.
    """
    from pytanga.geometry.create_n3 import create_translator

    translator = create_translator(n3, 0.5, 0.3, 0.1)
    assert sorted(translator.grades) == [0, 2]

    scale, factors = translator.blade_factorize_versor()
    assert len(factors) == 2
    for f in factors:
        assert f.grades == [1]

    recon = _reconstruct_versor(scale, factors)
    diff = _versor_up_to_scale(recon) - _versor_up_to_scale(translator)
    assert diff.mag < 1e-8


def test_factorize_versor_dilator_n3_round_trip(n3):
    """A dilator round-trips through versor factorization up to scale.

    A dilator about the origin is ``1 + c·(e∞∧e₀)`` (grades {0,2}); like the
    translator it is a two-reflection versor whose scalar scale is lost in the
    degenerate metric, so compare up to scale.
    """
    from pytanga.geometry.create_n3 import create_dilator

    dilator = create_dilator(n3, 2.0)
    assert sorted(dilator.grades) == [0, 2]

    scale, factors = dilator.blade_factorize_versor()
    assert len(factors) == 2
    for f in factors:
        assert f.grades == [1]

    recon = _reconstruct_versor(scale, factors)
    diff = _versor_up_to_scale(recon) - _versor_up_to_scale(dilator)
    assert diff.mag < 1e-8
