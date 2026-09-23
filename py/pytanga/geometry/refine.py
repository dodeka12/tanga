# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Duck-typed refinement dispatcher.

An entity is refinable when it exposes a callable ``refine()`` method (see the
``Refinable`` protocol in :mod:`pytanga.entity.base`).  ``Conic`` and
``Quadric3D`` implement it; the actual quadric math lives in
:mod:`pytanga.quadric.refine`, imported lazily inside the method.
"""

from __future__ import annotations


def refine(entity: object, *, tol: float | None = None) -> object:
    """Refine a refinable entity into its specific geometric entity.

    Probes for a callable ``entity.refine()`` method and delegates to it,
    forwarding an optional *tol* (used by ``Conic``/``Quadric3D`` to classify
    within a tolerance).  Raises :class:`TypeError` when the entity offers no
    ``refine`` method.
    """
    fn = getattr(entity, "refine", None)
    if not callable(fn):
        raise TypeError(f"{type(entity).__name__} is not refinable")
    if tol is None:
        return fn()
    return fn(tol=tol)


def refine_entity(entity: object) -> object:
    """Backward-compatible alias for :func:`refine`."""
    return refine(entity)


__all__ = ["refine", "refine_entity"]
