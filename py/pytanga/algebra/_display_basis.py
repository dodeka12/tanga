# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga._util — display-basis formatting utilities for multivectors.

Public API
----------
build_display_basis(generators, algebra, null_swap) → list[(name, blade, dual)]
    Build a complete named display basis from a list of grade-1 generators by
    taking every outer-product subset.  Each entry satisfies
    ``algebra.ip(blade, dual)[0] == 1``.
"""
from __future__ import annotations

import re
from itertools import combinations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._mv import MV
    from ._algebra import Algebra

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


def _scale(mv: "MV", s: float, algebra: "Algebra") -> "MV":
    """Return *s* * *mv* by scaling every coefficient."""
    return algebra.multivector(
        {k: v * s for k, v in _to_int_dict(mv, algebra).items()}
    )


def _op_chain(blades: list["MV"], algebra: "Algebra") -> "MV":
    """Outer product of *blades* in order.  Empty list → scalar 1."""
    if not blades:
        return algebra.multivector({0: 1.0})
    result = blades[0]
    for b in blades[1:]:
        result = algebra.op(result, b)
    return result


def _make_blade_name(subset_names: tuple[str, ...], pseudo_id: int,
                     algebra: "Algebra", blade: "MV") -> str:
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
    null_swap: dict[str, str] | None = None,
) -> list[tuple[str, "MV", "MV"]]:
    """Build a complete named display basis from grade-1 generators.

    Enumerates all 2^n outer-product subsets of *generators* (by grade then by
    natural ordering) and computes, for each resulting blade *B*, a dual blade
    *B'* such that ``algebra.ip(B, B')[0] == 1``.

    For non-null blades (``ip(B, B) ≠ 0``), the dual is ``B / ip(B, B)``.

    For null blades (``ip(B, B) ≈ 0``), the dual is obtained by swapping
    each generator name according to *null_swap* (e.g. ``"einf" ↔ "eo"``)
    and scaling by the cross-inner-product.

    Parameters
    ----------
    generators : ordered ``[(name, mv), ...]`` for the display grade-1 vectors.
    algebra    : Algebra instance (provides ip / op / multivector).
    null_swap  : ``{name: partner_name}`` for cross-dual resolution of null
                 blades.  Example: ``{"einf": "eo", "eo": "einf"}``.

    Returns
    -------
    list of ``(name, blade, dual)`` covering all blades in the span.
    ``dual`` is ``None`` for the scalar entry (grade 0).
    """
    null_swap = null_swap or {}
    gen_map: dict[str, "MV"] = {nm: mv for nm, mv in generators}
    pseudo_id = algebra.pseudoscalar_id
    entries: list[tuple[str, "MV", "MV | None"]] = []

    n = len(generators)
    for k in range(n + 1):
        for idx_tuple in combinations(range(n), k):
            sub_names  = tuple(generators[i][0] for i in idx_tuple)
            sub_blades = [generators[i][1] for i in idx_tuple]
            blade = _op_chain(sub_blades, algebra)

            # skip zero outer products (linearly dependent generators)
            if not any(abs(v) > _ZERO_THRESHOLD
                       for v in _to_int_dict(blade, algebra).values()):
                continue

            name = _make_blade_name(sub_names, pseudo_id, algebra, blade)

            if not idx_tuple:
                # Scalar entry (grade 0).  ip(scalar, scalar) returns {} in the
                # C++ left-contraction implementation (requires grade(right) >
                # grade(left) for non-zero result).  We mark the entry with
                # dual=None; show_str reads mv[0] directly for "s".
                entries.append((name, blade, None))
                continue

            ip_self  = algebra.ip(blade, blade)[0]

            if abs(ip_self) > _ZERO_THRESHOLD:
                # non-null: dual = blade / ip(blade, blade)
                dual = _scale(blade, 1.0 / ip_self, algebra)
            else:
                # null blade: swap generator names and use cross-inner-product
                swapped_names  = tuple(null_swap.get(nm, nm) for nm in sub_names)
                swapped_blades = [gen_map[nm] for nm in swapped_names]
                swapped        = _op_chain(swapped_blades, algebra)
                ip_cross       = algebra.ip(blade, swapped)[0]
                if abs(ip_cross) < _ZERO_THRESHOLD:
                    continue  # degenerate; skip
                dual = _scale(swapped, 1.0 / ip_cross, algebra)

            entries.append((name, blade, dual))

    return entries