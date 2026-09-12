# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Base interfaces for the entity classes."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Refinable(Protocol):
    """Protocol for entities that can be refined to a specific entity.

    Implemented by ``Conic`` and ``Quadric3D`` (in ``pytanga.quadric``), whose
    ``refine()`` returns the specific geometric entity (ellipse, hyperbola,
    ellipsoid, …).  ``pytanga.geometry.refine`` probes for this protocol to
    decide whether an entity is refinable.
    """

    def refine(self):
        """Refine this raw entity into its specific geometric entity."""
        ...
