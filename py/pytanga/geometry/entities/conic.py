# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Backward-compatible re-export of the conic/quadric entity classes.

``Conic`` / ``Quadric3D`` (and their kind enums) now live in
:mod:`pytanga.quadric.conic`; this module keeps the ``geometry.entities``
import path working.
"""

from pytanga.quadric import Conic, EConicKind, EQuadricKind, Quadric2D, Quadric3D

__all__ = ["Conic", "EConicKind", "EQuadricKind", "Quadric2D", "Quadric3D"]
