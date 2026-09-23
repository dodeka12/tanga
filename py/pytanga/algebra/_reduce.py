# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Sequence reducers for the named GA products.

The binary products live as :class:`MV` methods (``MV.op`` / ``MV.join`` /
``MV.meet`` / ``MV.gp``); these module-level functions fold them left-to-right
over a sequence of multivectors.
"""

from __future__ import annotations

import functools
from collections.abc import Sequence

from ._mv import MV


def _require_nonempty(mvs: Sequence[MV]) -> None:
    if not mvs:
        raise ValueError("expected at least one multivector")


def gp(mvs: Sequence[MV]) -> MV:
    """Geometric product of a sequence: ``mvs[0] * mvs[1] * …``."""
    _require_nonempty(mvs)
    return functools.reduce(MV.gp, mvs)


def op(mvs: Sequence[MV]) -> MV:
    """Outer (wedge) product of a sequence: ``mvs[0] ^ mvs[1] ^ …``."""
    _require_nonempty(mvs)
    return functools.reduce(MV.op, mvs)


def join(mvs: Sequence[MV]) -> MV:
    """Join of a sequence of blades."""
    _require_nonempty(mvs)
    return functools.reduce(MV.join, mvs)


def meet(mvs: Sequence[MV]) -> MV:
    """Meet of a sequence of blades."""
    _require_nonempty(mvs)
    return functools.reduce(MV.meet, mvs)
