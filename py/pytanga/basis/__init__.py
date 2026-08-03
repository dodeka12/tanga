# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.basis — predefined basis classes for standard geometries."""

from .e2 import BasisE2
from .e3 import BasisE3
from .n2 import BasisN2
from .n3 import BasisN3
from .p2 import BasisP2
from .p3 import BasisP3
from .pga2 import BasisPGA2
from .pga3 import BasisPGA3

_CLASS_MAP = {
    "E2": BasisE2,
    "E3": BasisE3,
    "N2": BasisN2,
    "N3": BasisN3,
    "P2": BasisP2,
    "P3": BasisP3,
    "PGA2": BasisPGA2,
    "PGA3": BasisPGA3,
}

__all__ = [
    "BasisE2",
    "BasisE3",
    "BasisN2",
    "BasisN3",
    "BasisP2",
    "BasisP3",
    "BasisPGA2",
    "BasisPGA3",
]
