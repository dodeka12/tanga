# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.algebra — core GA types: Algebra, MV, enums, and utilities."""

from ._algebra import Algebra
from ._enums import EInv, EProduct
from ._mv import MV
from ._mv_utils import MVLike, _as_mv, from_rotor, random_mask, to_rotor
from ._display_basis import build_display_basis

from ._galgebra_bridge import GalgebraBridge

__all__ = [
    "Algebra",
    "EInv",
    "EProduct",
    "GalgebraBridge",
    "MV",
    "MVLike",
    "_as_mv",
    "build_display_basis",
    "from_rotor",
    "random_mask",
    "to_rotor",
]
