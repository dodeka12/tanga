# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.quadric — projective quadric spaces (conics in 2D, quadrics in 3D).

The public surface is GA-centric: build conics/quadrics with ``geo(...)`` (via
``pytanga.geometry``), analyze/refine with ``analyze_*`` and ``Conic.refine()`` /
``Quadric3D.refine()``, and express construction, fitting, and intersection with
the GA operations (``op``/``join``/``meet``, ``dual``, ``sp``, ``vp``).  The
raw coefficient/matrix/fit/intersection helpers are private (``_``-prefixed) or
removed, and the internal ``create_*`` / ``refine_*`` implementations are not
re-exported here.
"""

from ._analysis import analyze_entity, analyze_operator, analyze_rotor
from ._basis import BasisQ2, BasisQ3
from .conic import Conic, EConicKind, EQuadricKind, Quadric2D, Quadric3D

__all__ = [
    "analyze_entity",
    "analyze_operator",
    "analyze_rotor",
    "BasisQ2",
    "BasisQ3",
    "Conic",
    "EConicKind",
    "EQuadricKind",
    "Quadric2D",
    "Quadric3D",
]
