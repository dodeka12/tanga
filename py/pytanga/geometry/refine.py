# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Duck-typed refinement dispatcher.

An entity is refinable when it exposes a callable ``refine()`` method (see the
``Refinable`` protocol in :mod:`pytanga.entity.base`).  ``Conic`` and
``Quadric3D`` implement it; the actual quadric math lives in
:mod:`pytanga.quadric.refine`, imported lazily inside the method.
"""

from __future__ import annotations

from typing import Any


def refine(entity: Any):
    """Refine a refinable entity into its specific geometric entity.

    Probes for a callable ``entity.refine()`` method and delegates to it.
    Raises :class:`TypeError` when the entity offers no ``refine`` method.
    """
    fn = getattr(entity, "refine", None)
    if not callable(fn):
        raise TypeError(f"{type(entity).__name__} is not refinable")
    return fn()


def refine_entity(entity: Any):
    """Backward-compatible alias for :func:`refine`."""
    return refine(entity)


__all__ = ["refine", "refine_entity"]
