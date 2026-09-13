# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Typed views of the vectors the per-algebra bases attach at construction time.

``BasisN2``/``BasisN3`` attach ``einf``/``eo`` (plus ``e1``…``e3``) in their
``__init__``; ``BasisPGA2``/``BasisPGA3`` attach ``e0``/``e0_recip`` (plus
``e1``…``e3``).  The base class :class:`~pytanga.algebra.Algebra` declares none
of them, so a type checker reports the attribute as unresolved — or, inside a
``hasattr`` guard, merely as ``object``.

These protocols describe the attribute sets the geometry helpers rely on, so a
helper can view its basis through the matching protocol (via ``cast``) instead
of suppressing a diagnostic per attribute.  A helper is always called with a
basis that really does carry those attributes: the ``analysis_n3``/``create_n3``
modules only ever see a ``BasisN3``, and so on for the other algebras.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV


class ConformalBasis(Protocol):
    """An N2 (2D) or N3 (3D) conformal basis: the two null vectors plus e₁/e₂."""

    einf: MV
    eo: MV
    e1: MV
    e2: MV


class ConformalBasis3D(ConformalBasis, Protocol):
    """An N3 conformal basis — a :class:`ConformalBasis` that also has ``e3``."""

    e3: MV


class PGABasis2D(Protocol):
    """A PGA2 basis (Gunn/Dorst plane-based 2D)."""

    e0: MV
    e0_recip: MV
    e1: MV
    e2: MV


class PGABasis3D(Protocol):
    """A PGA3 basis (Gunn/Dorst plane-based 3D)."""

    e0: MV
    e0_recip: MV
    e1: MV
    e2: MV
    e3: MV
