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


def analyze_entity(mv: MV) -> Entity | None:
    """Determine which geometric entity an MV represents.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.  The MV's ``algebra.opns`` flag
        determines the OPNS/IPNS interpretation.

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
        return analysis_e3.analyze_entity(mv)
    elif alg_type == "p3":
        return analysis_p3.analyze_entity(mv)
    elif alg_type == "pga3":
        return analysis_pga3.analyze_entity(mv)
    elif alg_type == "n3":
        return analysis_n3.analyze_entity(mv)
    elif alg_type == "e2":
        return analysis_e2.analyze_entity(mv)
    elif alg_type == "p2":
        return analysis_p2.analyze_entity(mv)
    elif alg_type == "pga2":
        return analysis_pga2.analyze_entity(mv)
    elif alg_type == "n2":
        return analysis_n2.analyze_entity(mv)


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


# ── typed dispatchers ──────────────────────────────────────────


_ENTITY_ALG_SUPPORT = {
    "point": {"p2", "p3", "n2", "n3", "pga2", "pga3"},
    "direction": {"e2", "e3", "p2", "p3", "n2", "n3", "pga2", "pga3"},
    "line": {"e2", "e3", "p2", "p3", "n2", "n3", "pga2", "pga3"},
    "plane": {"e3", "p3", "n3", "pga3"},
    "circle": {"n2", "n3"},
    "sphere": {"n2", "n3"},
    "point_pair": {"n2", "n3"},
    "hpoint": {"n2", "n3"},
    "hdirection": {"n2", "n3"},
    "space": {"e2", "e3", "p2", "p3", "n2", "n3", "pga2", "pga3"},
}

_MODULES = {
    "e2": analysis_e2,
    "e3": analysis_e3,
    "p2": analysis_p2,
    "p3": analysis_p3,
    "n2": analysis_n2,
    "n3": analysis_n3,
    "pga2": analysis_pga2,
    "pga3": analysis_pga3,
}


def _typed(mv: MV, name: str, display: str) -> Entity:
    """Dispatch a typed analyzer ``analyze_<name>(mv)`` to the right module."""
    alg_type = _detect(mv._alg)
    if alg_type not in _ENTITY_ALG_SUPPORT[name]:
        raise TypeError(f"{display} is not supported in {alg_type}")
    return getattr(_MODULES[alg_type], f"analyze_{name}")(mv)


def analyze_point(mv: MV) -> "Point":
    """Interpret *mv* as a :class:`Point` in its algebra's OPNS/IPNS mode."""
    return _typed(mv, "point", "Point")


def analyze_direction(mv: MV) -> "Direction":
    """Interpret *mv* as a :class:`Direction` in its algebra's OPNS/IPNS mode."""
    return _typed(mv, "direction", "Direction")


def analyze_line(mv: MV) -> "Line":
    """Interpret *mv* as a :class:`Line` in its algebra's OPNS/IPNS mode."""
    return _typed(mv, "line", "Line")


def analyze_plane(mv: MV) -> "Plane":
    """Interpret *mv* as a :class:`Plane` in its algebra's OPNS/IPNS mode."""
    return _typed(mv, "plane", "Plane")


def analyze_circle(mv: MV) -> "Circle":
    """Interpret *mv* as a :class:`Circle` in its algebra's OPNS/IPNS mode."""
    return _typed(mv, "circle", "Circle")


def analyze_sphere(mv: MV) -> "Sphere":
    """Interpret *mv* as a :class:`Sphere` in its algebra's OPNS/IPNS mode."""
    return _typed(mv, "sphere", "Sphere")


def analyze_point_pair(mv: MV) -> "PointPair":
    """Interpret *mv* as a :class:`PointPair` in its algebra's OPNS/IPNS mode."""
    return _typed(mv, "point_pair", "PointPair")


def analyze_hpoint(mv: MV) -> "HPoint":
    """Interpret *mv* as an :class:`HPoint` in its algebra's OPNS/IPNS mode."""
    return _typed(mv, "hpoint", "HPoint")


def analyze_hdirection(mv: MV) -> "HDirection":
    """Interpret *mv* as an :class:`HDirection` in its algebra's OPNS/IPNS mode."""
    return _typed(mv, "hdirection", "HDirection")


def analyze_space(mv: MV) -> "Space":
    """Interpret *mv* as :class:`Space` in its algebra's OPNS/IPNS mode."""
    return _typed(mv, "space", "Space")


# ── combined fallback ───────────────────────────────────────────


def analyze(mv: MV) -> Entity | Operator | None:
    """Try to analyze an MV as either an entity or an operator.

    Tries entity analysis first, then operator analysis.
    Returns the first successful match.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.  The MV's ``algebra.opns`` flag
        determines the OPNS/IPNS interpretation for entity analysis;
        operators are unaffected.

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
        result = analyze_entity(mv)
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
