# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

from typing import TYPE_CHECKING, Union

import numpy as np

from ._algebra import Algebra
from pytanga.blade_mask import BladeMask
from ._mv import MV

if TYPE_CHECKING:
    from ._algebra import Algebra as _Algebra

MVLike = Union["MV", float, int, str]


def _as_mv(alg: "_Algebra", x: MVLike) -> "MV":
    """Coerce a scalar or string to MV; pass MV through unchanged."""
    from ._mv import MV as _MV

    if isinstance(x, _MV):
        return x
    if isinstance(x, (int, float)):
        return alg.multivector({0: x})
    # str — let Algebra.multivector parse the expression
    return alg.multivector(x)


def random_mask(
    alg: Algebra,
    n: int,
    *,
    rng: np.random.Generator | int | None = None,
) -> BladeMask:
    """Return a ``BladeMask`` with *n* randomly selected blade ids.

    Parameters
    ----------
    alg : Algebra
        The algebra to draw blade ids from.
    n : int
        Number of blade ids to include (must be between 1 and 2^dim).
    rng : numpy.random.Generator | int | None
        Random number generator, integer seed, or None (fresh generator).
    """
    if rng is None:
        gen = alg.rng
    else:
        gen = np.random.default_rng(rng)

    all_ids = alg.all_blades()
    if n < 1 or n > len(all_ids):
        raise ValueError(
            f"random_mask: n must be between 1 and {len(all_ids)}, got {n}"
        )
    ids = sorted(gen.choice(all_ids, size=n, replace=False).tolist())
    return BladeMask(alg, ids)


def to_rotor(
    angle: float,
    *,
    vec_pair: tuple[MVLike, MVLike] | None = None,
    bivec: MVLike | None = None,
    algebra: Algebra | None = None,
) -> MV:
    """Return a rotor for a given angle and plane.

    Parameters
    ----------
    angle : float
        The rotation angle in radians.
    vec_pair : tuple[MV, MV] | None
        A pair of vectors that define the plane of rotation.
        If provided, the bivector is computed as the outer product of the two vectors.
    bivec : MV | None
        A bivector that defines the plane of rotation.
        If provided, it is used directly to compute the rotor.
    algebra : Algebra | None
        The algebra in which the rotor is defined. If None, the algebra is inferred from the

    Returns
    -------
    MV
        The rotor corresponding to the specified angle and plane.
    """
    if vec_pair is not None:
        v1, v2 = vec_pair
        if isinstance(v1, MV):
            algebra = v1.algebra
        elif isinstance(v2, MV):
            algebra = v2.algebra
        elif algebra is None:
            raise ValueError(
                "Algebra must be provided if vec_pair contains non-MV types."
            )

        v1 = _as_mv(algebra, v1)
        v2 = _as_mv(algebra, v2)
        if not v1.is_grade(1):
            raise ValueError(
                "The first element of vec_pair must be a vector (grade 1)."
            )
        if not v2.is_grade(1):
            raise ValueError(
                "The second element of vec_pair must be a vector (grade 1)."
            )

        bivec = v1 ^ v2  # Outer product to get bivector

    elif bivec is not None:
        if isinstance(bivec, MV):
            algebra = bivec.algebra
        elif algebra is None:
            raise ValueError("Algebra must be provided if bivec is not an MV instance.")

        bivec = _as_mv(algebra, bivec)

    # Ensure that the bivector only contains elements of grade 2
    if not bivec.is_grade(2):
        raise ValueError("The provided bivector must be of grade 2.")

    # Normalize the bivector to ensure it represents a valid rotation plane
    bivec_normalized = bivec.normalized()

    # Compute the rotor using the exponential map
    rotor = np.cos(angle / 2) + np.sin(angle / 2) * bivec_normalized

    return rotor


def from_rotor(rotor: MV) -> tuple[float, float, MV]:
    """Return the angle and bivector from a given rotor.

    Parameters
    ----------
    rotor : MV
        The rotor from which to extract the angle and bivector.

    Returns
    -------
    tuple[float, float, MV]
        A tuple containing the scale, rotation angle in radians, and the corresponding bivector.
    """
    if rotor.grades != [0, 2]:
        raise ValueError("The provided rotor must be a multivector of grades 0 and 2.")

    # normalize the rotor to ensure it represents a valid rotation
    scale = rotor.mag
    if scale == 0:
        raise ValueError(
            "The provided rotor has zero magnitude and cannot be normalized."
        )

    rotor = rotor / scale

    # Use atan2 to compute the angle from the scalar and bivector parts
    scalar_part = rotor.scalar
    bivector_part = rotor.grade(2)  # Project to grade 2 to get the bivector part

    angle = 2 * np.arctan2(bivector_part.mag, scalar_part)

    return scale, angle, bivector_part  # already unit-magnitude from normalized rotor
