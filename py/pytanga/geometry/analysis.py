# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Top-level analysis dispatcher for geometric entities and operators.

Determines the algebra type of a multivector and delegates to the
appropriate algebra-specific analysis module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import analysis_e3, analysis_n3, analysis_p3, analysis_pga3
from .entities import Entity
from .operators import Operator

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV
    from pytanga.basis.e3 import BasisE3
    from pytanga.basis.n3 import BasisN3
    from pytanga.basis.p3 import BasisP3
    from pytanga.basis.pga3 import BasisPGA3


def _detect(alg: Algebra) -> str:
    """Return ``'e3'``, ``'p3'``, ``'pga3'``, or ``'n3'``.

    Uses isinstance checks because ``BasisPGA3`` (subclass) and
    ``BasisN3`` (base class) share the same *(dim=5, sig=0b10000)*
    signature but are different geometric models.  ``BasisPGA3`` is
    checked **first** since it is a subclass of ``BasisN3``.
    """
    # Lazy import to avoid circular dependencies at module level
    from pytanga.basis.e3 import BasisE3
    from pytanga.basis.n3 import BasisN3
    from pytanga.basis.p3 import BasisP3
    from pytanga.basis.pga3 import BasisPGA3

    if isinstance(alg, BasisPGA3):
        return "pga3"
    elif isinstance(alg, BasisN3):
        return "n3"
    elif isinstance(alg, BasisP3):
        return "p3"
    elif isinstance(alg, BasisE3):
        return "e3"
    else:
        raise ValueError(
            f"Unknown algebra type: {type(alg).__name__} "
            f"(dim={alg.dim}, sig={bin(alg.sig)})"
        )


# ── entity analysis ─────────────────────────────────────────────

def analyze_entity(mv: MV, *, opns: bool = True) -> Entity:
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
    Entity
        A :term:`dataclass` (:class:`~pytanga.geometry.entities.Point`,
        :class:`Line`, :class:`Plane`, :class:`Circle`,
        :class:`Sphere`, …).

    Raises
    ------
    ValueError
        If the MV cannot be identified as a known entity type.
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


# ── operator analysis ───────────────────────────────────────────

def analyze_operator(mv: MV) -> Operator:
    """Determine which versor / operator an MV represents.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.

    Returns
    -------
    Operator
        A :term:`dataclass` (:class:`~pytanga.geometry.operators.Rotor`,
        :class:`Translator`, :class:`Motor`, …).

    Raises
    ------
    ValueError
        If the MV cannot be identified as a known operator type.
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


# ── combined fallback ───────────────────────────────────────────

def analyze(mv: MV, *, opns: bool = True) -> Entity | Operator:
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
    Entity or Operator
        Either an :class:`Entity` or an :class:`Operator` dataclass.

    Raises
    ------
    ValueError
        If the MV cannot be identified as either an entity or an operator.
    """
    try:
        return analyze_entity(mv, opns=opns)
    except (ValueError, NotImplementedError):
        pass
    try:
        return analyze_operator(mv)
    except (ValueError, NotImplementedError):
        pass
    raise ValueError(
        f"Could not identify MV as entity or operator "
        f"in algebra {type(mv._alg).__name__}"
    )