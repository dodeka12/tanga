# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga._util — display-basis formatting utilities for multivectors.

Public API
----------
build_display_basis(generators, algebra) → list[(name, blade, pinv, blade_id)]
    Build a complete named display basis from a list of grade-1 generators by
    taking every outer-product subset.  Each entry satisfies
    ``algebra.ip(blade, pinv)[0] == 1``.
"""

from __future__ import annotations

import re
from itertools import combinations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._algebra import Algebra
    from ._mv import MV

_ZERO_THRESHOLD = 1e-10

__all__ = ["build_display_basis"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _to_int_dict(mv: "MV", algebra: "Algebra") -> dict[int, float]:
    """Return the mv coefficient dict with integer blade-ID keys."""
    out: dict[int, float] = {}
    for name, val in mv.to_dict().items():
        bid = 0 if name == "s" else algebra.blade_id(name)
        out[bid] = val
    return out


def _op_chain(blades: list["MV"], algebra: "Algebra") -> "MV":
    """Outer product of *blades* in order.  Empty list → scalar 1."""
    if not blades:
        return algebra.multivector({0: 1.0})
    result = blades[0]
    for b in blades[1:]:
        result = algebra.op(result, b)
    return result


def _simple_blade_id(blade: "MV", algebra: "Algebra") -> int | None:
    """If *blade* is exactly one primitive basis blade with coefficient 1.0,
    return its integer blade ID.  Otherwise return None."""
    raw = _to_int_dict(blade, algebra)
    nz = [(bid, v) for bid, v in raw.items() if abs(v) > _ZERO_THRESHOLD]
    if len(nz) == 1 and abs(nz[0][1] - 1.0) < _ZERO_THRESHOLD:
        return nz[0][0]
    return None


def _make_blade_name(
    subset_names: tuple[str, ...], pseudo_id: int, algebra: "Algebra", blade: "MV"
) -> str:
    """Produce a human-readable name for a subset of display generators.

    Rules
    -----
    - Empty subset                            → "s"
    - Subset whose blade is the pseudoscalar  → "I"
    - Pure ``e{int}`` generators              → "e{i}{j}…" (concatenated)
    - Mix of numeric and named (einf, eo, …) → "e{ij}∧named∧…"
    """
    if not subset_names:
        return "s"

    # Check for pseudoscalar
    d = _to_int_dict(blade, algebra)
    nz = [(k, v) for k, v in d.items() if abs(v) > _ZERO_THRESHOLD]
    if len(nz) == 1 and nz[0][0] == pseudo_id:
        return "I"

    e_num = [n for n in subset_names if re.fullmatch(r"e\d+", n)]
    named = [n for n in subset_names if not re.fullmatch(r"e\d+", n)]
    parts: list[str] = []
    if e_num:
        nums = "".join(re.search(r"\d+", n).group() for n in e_num)
        parts.append(f"e{nums}")
    parts.extend(named)
    return "∧".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_display_basis(
    generators: list[tuple[str, "MV"]],
    algebra: "Algebra",
) -> list[tuple[str, "MV", "MV | None", int | None]]:
    """Build a complete named display basis from grade-1 generators.

    Enumerates all 2^n outer-product subsets of *generators* (by grade then by
    natural ordering) and computes, for each resulting blade *B*, a
    pseudoinverse *B⁺* such that ``algebra.ip(B, B⁺)[0] == 1``.

    For simple blades (exactly one primitive blade with coefficient 1.0), the
    ``blade_id`` is populated so that coefficient extraction can use the fast
    ``mv[blade_id]`` path instead of ``ip(mv, pinv)``.

    Parameters
    ----------
    generators : ordered ``[(name, mv), ...]`` for the display grade-1 vectors.
    algebra    : Algebra instance (provides ip / op / blade_pseudo_inverse).

    Returns
    -------
    list of ``(name, blade, pinv, blade_id)`` covering all blades in the span.
    ``pinv`` and ``blade_id`` are ``None`` only for the scalar entry (grade 0).
    """
    pseudo_id = algebra.pseudoscalar_id
    entries: list[tuple[str, "MV", "MV | None", int | None]] = []

    n = len(generators)
    for k in range(n + 1):
        for idx_tuple in combinations(range(n), k):
            sub_names = tuple(generators[i][0] for i in idx_tuple)
            sub_blades = [generators[i][1] for i in idx_tuple]
            blade = _op_chain(sub_blades, algebra)

            # skip zero outer products (linearly dependent generators)
            if not any(
                abs(v) > _ZERO_THRESHOLD for v in _to_int_dict(blade, algebra).values()
            ):
                continue

            name = _make_blade_name(sub_names, pseudo_id, algebra, blade)

            if not idx_tuple:
                # Scalar entry (grade 0).  ``mv[0]`` gives the scalar.
                entries.append((name, blade, None, 0))
                continue

            pinv = algebra.blade_pseudo_inverse(blade)
            blade_id = _simple_blade_id(blade, algebra)
            entries.append((name, blade, pinv, blade_id))

    return entries
