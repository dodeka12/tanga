# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Space (pseudoscalar) entity data class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._util import _convert_mv, _is_mv

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV


@dataclass(frozen=True)
class Space:
    """The entire 3D volume (pseudoscalar).

    Attributes:
        scale: The scalar coefficient of the pseudoscalar blade
            (OPNS), or the grade-0 scalar value (IPNS).

    Can also be constructed from a single multivector (converted via
    :func:`~pytanga.geometry.analysis.analyze_space`).
    """

    scale: float = 1.0

    def __init__(self, scale: "float | MV" = 1.0) -> None:
        if _is_mv(scale):
            if scale.is_scalar:
                object.__setattr__(self, "scale", float(scale.scalar))
            else:
                s = _convert_mv("space", scale)
                object.__setattr__(self, "scale", s.scale)
        else:
            object.__setattr__(self, "scale", float(scale))
