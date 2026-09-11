# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Random geometric entity generators.

This module defines :class:`RndPoint` and :class:`RndDirection` — lazy
generators that produce :class:`~.entities.Point` /
:class:`~.entities.Direction` dataclasses when called with a NumPy random
number generator.  They are consumed by :meth:`~._geometry.Geometry.__call__`,
which materializes the dataclasses and routes them through the algebra's
``create`` dispatcher to produce multivectors.

Coordinate specs accept:

- a :class:`Distribution` instance (e.g. :class:`Uniform`, :class:`Normal`),
- a 2-tuple ``(low, high)``, interpreted as a uniform distribution.

Each generator supports an optional ``count``: when None it yields a single
entity, otherwise it yields a list of that many entities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask

from .entities import Direction, Point

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV


# ── Distributions ──────────────────────────────────────────────


class Distribution:
    """Base class for scalar random distributions.

    Subclasses implement :meth:`__call__`, which samples a single scalar
    from a NumPy random number generator.
    """

    def __call__(
        self, rng: np.random.Generator
    ) -> float:  # pragma: no cover - abstract
        raise NotImplementedError


class Uniform(Distribution):
    """Uniform distribution over the half-open interval ``[low, high)``."""

    def __init__(self, low: float, high: float) -> None:
        self.low = float(low)
        self.high = float(high)

    def __call__(self, rng: np.random.Generator) -> float:
        return float(rng.uniform(self.low, self.high))

    def __repr__(self) -> str:  # pragma: no cover - helper
        return f"Uniform({self.low}, {self.high})"


class Normal(Distribution):
    """Normal distribution with given ``mean`` and ``stddev``."""

    def __init__(self, mean: float = 0.0, stddev: float = 1.0) -> None:
        self.mean = float(mean)
        self.stddev = float(stddev)

    def __call__(self, rng: np.random.Generator) -> float:
        return float(rng.normal(self.mean, self.stddev))

    def __repr__(self) -> str:  # pragma: no cover - helper
        return f"Normal({self.mean}, {self.stddev})"


class Constant(Distribution):
    """A fixed scalar value (ignores the random generator)."""

    def __init__(self, value: float | int) -> None:
        self.value = value

    def __call__(self, rng: np.random.Generator) -> float | int:
        return self.value

    def __repr__(self) -> str:  # pragma: no cover - helper
        return f"Constant({self.value})"


def _as_distribution(spec) -> Distribution:
    """Coerce a coordinate spec into a :class:`Distribution`.

    - ``Distribution`` → passed through.
    - 2-tuple ``(low, high)`` → :class:`Uniform`.
    - scalar ``int``/``float`` → :class:`Constant`.
    """
    if isinstance(spec, Distribution):
        return spec
    if isinstance(spec, tuple) and len(spec) == 2:
        return Uniform(spec[0], spec[1])
    if isinstance(spec, (int, float)) and not isinstance(spec, bool):
        return Constant(spec)
    raise TypeError(
        f"Expected Distribution, (low, high) tuple, or fixed value, "
        f"got {type(spec).__name__}: {spec!r}"
    )


# ── Entity generators ──────────────────────────────────────────


class RndEntity:
    """Common base for random entity generators.

    Subclasses implement :meth:`_generate`, returning either a single entity
    or a list of entities depending on their ``count`` setting.
    """

    def __call__(self, rng: np.random.Generator) -> "Point | Direction | list":
        raise NotImplementedError


class RndPoint(RndEntity):
    """Generator for random :class:`~.entities.Point` instances.

    Parameters
    ----------
    x, y, z : Distribution | tuple[float, float]
        Coordinate distributions; a tuple ``(low, high)`` means uniform.
        Defaults to ``(-1.0, 1.0)``.
    count : int | None
        When None, :meth:`__call__` returns a single :class:`Point`.
        Otherwise it returns a list of ``count`` points.
    """

    def __init__(
        self,
        x: Distribution | tuple[float, float] = (-1.0, 1.0),
        y: Distribution | tuple[float, float] = (-1.0, 1.0),
        z: Distribution | tuple[float, float] = (-1.0, 1.0),
        *,
        count: int | None = None,
    ) -> None:
        self._x = _as_distribution(x)
        self._y = _as_distribution(y)
        self._z = _as_distribution(z)
        self.count = count

    def _sample_one(self, rng: np.random.Generator) -> Point:
        return Point(self._x(rng), self._y(rng), self._z(rng))

    def __call__(self, rng: np.random.Generator) -> Point | list[Point]:
        if self.count is None:
            return self._sample_one(rng)
        return [self._sample_one(rng) for _ in range(self.count)]


class RndDirection(RndEntity):
    """Generator for random :class:`~.entities.Direction` instances.

    Parameters mirror :class:`RndPoint`; a tuple ``(low, high)`` means
    uniform, and ``count=None`` returns a single :class:`Direction`.
    """

    def __init__(
        self,
        x: Distribution | tuple[float, float] = (-1.0, 1.0),
        y: Distribution | tuple[float, float] = (-1.0, 1.0),
        z: Distribution | tuple[float, float] = (-1.0, 1.0),
        *,
        count: int | None = None,
    ) -> None:
        self._x = _as_distribution(x)
        self._y = _as_distribution(y)
        self._z = _as_distribution(z)
        self.count = count

    def _sample_one(self, rng: np.random.Generator) -> Direction:
        return Direction(self._x(rng), self._y(rng), self._z(rng))

    def __call__(self, rng: np.random.Generator) -> Direction | list[Direction]:
        if self.count is None:
            return self._sample_one(rng)
        return [self._sample_one(rng) for _ in range(self.count)]


class RndMV(RndEntity):
    """Generator for random multivectors over a fixed :class:`~pytanga.BladeMask`.

    Parameters
    ----------
    mask : BladeMask
        The blade mask to populate.  Its algebra is used to build the result.
    spec : Sequence
        One entry per blade in ``mask``.  Each entry is a :class:`Distribution`
        instance, a 2-tuple ``(low, high)`` (uniform), or a scalar fixed value.
    count : int | None
        When None, :meth:`__call__` returns a single ``MV``; otherwise it
        returns a list of ``count`` multivectors.
    """

    def __init__(self, mask: BladeMask, spec, *, count: int | None = None) -> None:
        self._mask = mask
        specs = list(spec)
        if len(specs) != len(mask):
            raise ValueError(
                f"RndMV spec has {len(specs)} entries but mask has {len(mask)} blades"
            )
        self._specs = [_as_distribution(s) for s in specs]
        self.count = count

    def _sample_one(self, rng: np.random.Generator) -> "MV":
        alg = self._mask.algebra
        coeffs = {}
        for bid, dist in zip(self._mask.ids, self._specs):
            value = dist(rng)
            coeffs[int(bid)] = (
                int(value) if alg.dtype.startswith("int") else float(value)
            )
        return alg.multivector(coeffs)

    def __call__(self, rng: np.random.Generator) -> "MV | list[MV]":
        if self.count is None:
            return self._sample_one(rng)
        return [self._sample_one(rng) for _ in range(self.count)]


__all__ = [
    "Constant",
    "Distribution",
    "Normal",
    "RndDirection",
    "RndEntity",
    "RndMV",
    "RndPoint",
    "Uniform",
]
