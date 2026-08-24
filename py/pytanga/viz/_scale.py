# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Scale and tick computation for coordinate-system plotting.

Provides :class:`Scale` subclasses that map data values to (linear) world
coordinates and produce the ``(value, label)`` tick pairs used to place axis
value labels and grid lines.  The world coordinate system itself stays linear;
a scale only describes how data values are placed along an axis.

This module is pure math with no scene dependency, so it can be unit-tested and
used directly (e.g. ``Axis(..., ticks=LogScale().ticks(0.1, 100))``).
"""

from __future__ import annotations

import math

DEFAULT_TICK_FORMAT = ".4g"


class Scale:
    """Base mapping between data values and linear world coordinates.

    Subclasses implement :meth:`to_world` / :meth:`from_world` and
    :meth:`ticks`.  ``is_log`` is ``True`` for logarithmic scales.
    """

    is_log: bool = False

    def to_world(self, value: float) -> float:
        """Map a data value to a linear world coordinate."""
        raise NotImplementedError

    def from_world(self, world: float) -> float:
        """Map a linear world coordinate back to a data value."""
        raise NotImplementedError

    def ticks(self, lo: float, hi: float) -> list[tuple[float, str]]:
        """Return ``(value, label)`` tick pairs covering ``[lo, hi]``, ascending."""
        raise NotImplementedError


class LinearScale(Scale):
    """Identity scale — world coordinate equals the data value.

    Ticks use a "nice" 1/2/5 × 10^k step so labels read as clean numbers.
    """

    is_log = False

    def to_world(self, value: float) -> float:
        return float(value)

    def from_world(self, world: float) -> float:
        return float(world)

    def ticks(self, lo: float, hi: float) -> list[tuple[float, str]]:
        return nice_linear_ticks(lo, hi)


class LogScale(Scale):
    """Logarithmic scale for an arbitrary base (default 10).

    ``to_world(value) = log(value, base)``; the data range must be strictly
    positive.  Ticks are integer powers of ``base`` within the range.
    """

    def __init__(self, base: float = 10.0) -> None:
        base = float(base)
        if not (base > 1.0):
            raise ValueError(f"log scale base must be > 1, got {base}")
        self.base = base
        self.is_log = True

    def to_world(self, value: float) -> float:
        value = float(value)
        if value <= 0.0:
            raise ValueError(f"log scale requires a positive value, got {value}")
        return math.log(value, self.base)

    def from_world(self, world: float) -> float:
        return self.base ** float(world)

    def ticks(self, lo: float, hi: float) -> list[tuple[float, str]]:
        return log_ticks(lo, hi, self.base)


def make_scale(scale: "Scale | str" = "linear", base: float = 10.0) -> Scale:
    """Normalize a scale spec to a :class:`Scale` instance.

    Accepts a :class:`Scale` (returned unchanged), ``"linear"``, or ``"log"``.
    """
    if isinstance(scale, Scale):
        return scale
    if scale == "linear":
        return LinearScale()
    if scale == "log":
        return LogScale(base)
    raise ValueError(
        f"unsupported scale {scale!r}; expected 'linear', 'log', or a Scale instance"
    )


def nice_linear_ticks(
    lo: float,
    hi: float,
    max_ticks: int = 8,
    fmt: str = DEFAULT_TICK_FORMAT,
) -> list[tuple[float, str]]:
    """Return nice 1/2/5 × 10^k ticks covering ``[lo, hi]``.

    Chooses a step so that roughly ``max_ticks`` intervals (or fewer) span the
    range, snapping to the closest "nice" step of the form {1, 2, 5} × 10^k.
    """
    lo, hi = sorted((float(lo), float(hi)))
    if not math.isfinite(lo) or not math.isfinite(hi):
        return []
    span = hi - lo
    if span == 0.0:
        return [(lo, format(lo, fmt))]
    if span < 0.0:
        return []

    raw_step = span / max(1, int(max_ticks))
    magnitude = 10.0 ** math.floor(math.log10(raw_step))
    step = 10.0 * magnitude
    for candidate in (1.0, 2.0, 5.0, 10.0):
        if candidate * magnitude >= raw_step:
            step = candidate * magnitude
            break

    ticks: list[tuple[float, str]] = []
    t = math.ceil(lo / step) * step
    epsilon = step * 1e-9
    while t <= hi + epsilon and len(ticks) < 1000:
        ticks.append((t, format(t, fmt)))
        t += step
    return ticks


def log_ticks(
    lo: float,
    hi: float,
    base: float = 10.0,
    fmt: str = DEFAULT_TICK_FORMAT,
) -> list[tuple[float, str]]:
    """Return integer-power-of-``base`` ticks covering ``[lo, hi]``.

    The range must be strictly positive.  Ticks are ``base**k`` for every
    integer ``k`` such that ``lo <= base**k <= hi``.
    """
    lo, hi = sorted((float(lo), float(hi)))
    if lo <= 0.0:
        raise ValueError(f"log scale range must be strictly positive, got {lo}")
    if not (base > 1.0):
        raise ValueError(f"log scale base must be > 1, got {base}")

    # Small epsilon guards against floating-point error when lo/hi are exact
    # powers of the base (e.g. log10(1000) == 2.9999999999999996).
    eps = 1e-12
    k_start = math.ceil(math.log(lo, base) - eps)
    k_end = math.floor(math.log(hi, base) + eps)

    ticks: list[tuple[float, str]] = []
    for k in range(k_start, k_end + 1):
        value = base**k
        ticks.append((value, format(value, fmt)))
    return ticks
