# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.basis — predefined basis classes for standard geometries."""

from .e3 import BasisE3
from .p3 import BasisP3
from .n3 import BasisN3
from .pga3 import BasisPGA3

_CLASS_MAP = {
    "E3":   BasisE3,
    "P3":   BasisP3,
    "N3":   BasisN3,
    "PGA3": BasisPGA3,
}

__all__ = ["BasisE3", "BasisP3", "BasisN3", "BasisPGA3"]
