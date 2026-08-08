# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Top-level analysis dispatcher for geometric entities and operators.

Determines the algebra type of a multivector and delegates to the
appropriate algebra-specific analysis module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import (
    analysis_e2,
    analysis_e3,
    analysis_n2,
    analysis_n3,
    analysis_p2,
    analysis_p3,
    analysis_pga2,
    analysis_pga3,
)
from .entities import Entity
from .operators import Operator

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV
    from pytanga.basis.e2 import BasisE2
    from pytanga.basis.e3 import BasisE3
    from pytanga.basis.n2 import BasisN2
    from pytanga.basis.n3 import BasisN3
    from pytanga.basis.p2 import BasisP2
    from pytanga.basis.p3 import BasisP3
    from pytanga.basis.pga2 import BasisPGA2
    from pytanga.basis.pga3 import BasisPGA3


def _detect(alg: Algebra) -> str:
    """Return ``'e2'``, ``'p2'``, ``'pga2'``, ``'n2'``, ``'e3'``, ``'p3'``, ``'pga3'``, or ``'n3'``.

    Uses isinstance checks because ``BasisPGA2``/``BasisPGA3`` (subclass) and
    ``BasisN2``/``BasisN3`` (base class) share the same signatures but are
    different geometric models.  Subclasses are checked **first**.
    3D algebras checked before 2D algebras.
    """
    # Lazy import to avoid circular dependencies at module level
    from pytanga.basis.e2 import BasisE2
    from pytanga.basis.e3 import BasisE3
    from pytanga.basis.n2 import BasisN2
    from pytanga.basis.n3 import BasisN3
    from pytanga.basis.p2 import BasisP2
    from pytanga.basis.p3 import BasisP3
    from pytanga.basis.pga2 import BasisPGA2
    from pytanga.basis.pga3 import BasisPGA3

    # 3D algebras
    if isinstance(alg, BasisPGA3):
        return "pga3"
    elif isinstance(alg, BasisN3):
        return "n3"
    elif isinstance(alg, BasisP3):
        return "p3"
    elif isinstance(alg, BasisE3):
        return "e3"
    # 2D algebras — PGA2 before N2 (inheritance)
    elif isinstance(alg, BasisPGA2):
        return "pga2"
    elif isinstance(alg, BasisN2):
        return "n2"
    elif isinstance(alg, BasisP2):
        return "p2"
    elif isinstance(alg, BasisE2):
        return "e2"
    else:
        raise ValueError(
            f"Unknown algebra type: {type(alg).__name__} "
            f"(dim={alg.dim}, sig={bin(alg.sig)})"
        )


# ── entity analysis ─────────────────────────────────────────────


def analyze_entity(mv: MV, *, opns: bool = True) -> Entity | None:
    """Determine which geometric entity an MV represents.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.
    opns : bool, optional
        *True* → interpret blade in OPNS (default).
        *False* → interpret blade in IPNS (dualizes to OPNS first).

    Returns
    -------
    Entity or None
        A :term:`dataclass` (:class:`~pytanga.geometry.entities.Point`,
        :class:`Line`, :class:`Plane`, :class:`Circle`,
        :class:`Sphere`, …).  Returns ``None`` if the null-space is empty.

    Raises
    ------
    ValueError
        If the MV is malformed (e.g., zero MV, mixed grades).
    """
    alg_type = _detect(mv._alg)
    if alg_type == "e3":
        return analysis_e3.analyze_entity(mv, opns=opns)
    elif alg_type == "p3":
        return analysis_p3.analyze_entity(mv, opns=opns)
    elif alg_type == "pga3":
        return analysis_pga3.analyze_entity(mv, opns=opns)
    elif alg_type == "n3":
        return analysis_n3.analyze_entity(mv, opns=opns)
    elif alg_type == "e2":
        return analysis_e2.analyze_entity(mv, opns=opns)
    elif alg_type == "p2":
        return analysis_p2.analyze_entity(mv, opns=opns)
    elif alg_type == "pga2":
        return analysis_pga2.analyze_entity(mv, opns=opns)
    elif alg_type == "n2":
        return analysis_n2.analyze_entity(mv, opns=opns)


# ── operator analysis ───────────────────────────────────────────


def analyze_operator(mv: MV) -> Operator | None:
    """Determine which versor / operator an MV represents.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.

    Returns
    -------
    Operator or None
        A :term:`dataclass` (:class:`~pytanga.geometry.operators.Rotor`,
        :class:`Translator`, :class:`Motor`, …).
        Returns ``None`` if the MV does not represent a known operator.

    Raises
    ------
    ValueError
        If the MV is malformed (e.g., zero MV).
    """
    alg_type = _detect(mv._alg)
    if alg_type == "e3":
        return analysis_e3.analyze_operator(mv)
    elif alg_type == "p3":
        return analysis_p3.analyze_operator(mv)
    elif alg_type == "pga3":
        return analysis_pga3.analyze_operator(mv)
    elif alg_type == "n3":
        return analysis_n3.analyze_operator(mv)
    elif alg_type == "e2":
        return analysis_e2.analyze_operator(mv)
    elif alg_type == "p2":
        return analysis_p2.analyze_operator(mv)
    elif alg_type == "pga2":
        return analysis_pga2.analyze_operator(mv)
    elif alg_type == "n2":
        return analysis_n2.analyze_operator(mv)


# ── combined fallback ───────────────────────────────────────────


def analyze(mv: MV, *, opns: bool = True) -> Entity | Operator | None:
    """Try to analyze an MV as either an entity or an operator.

    Tries entity analysis first, then operator analysis.
    Returns the first successful match.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.
    opns : bool, optional
        *True* → OPNS (default), *False* → IPNS. Only passed
        to entity analysis; operators are unaffected.

    Returns
    -------
    Entity, Operator, or None
        Either an :class:`Entity` or an :class:`Operator` dataclass.
        Returns ``None`` if the MV cannot be identified as either
        (null-space is empty for both interpretations).

    Raises
    ------
    ValueError
        If the MV is malformed (e.g., zero MV, mixed grades).
    """
    result = None
    try:
        result = analyze_entity(mv, opns=opns)
    except (ValueError, NotImplementedError):
        pass
    if result is not None:
        return result

    result = None
    try:
        result = analyze_operator(mv)
    except (ValueError, NotImplementedError):
        pass
    return result
