# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga._parse — multivector string parser (no C++ dependency)."""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Multivector string parser
# ---------------------------------------------------------------------------
# Matches one term in a sum:  [sign]  [coefficient]  [blade-name]
# All three parts are optional, but at least one of coefficient / blade must be
# non-empty (empty matches are skipped by _parse_mv_string).
#
# Examples of valid terms (after stripping surrounding whitespace):
#   "2.3"            → scalar 2.3
#   "+4 e2"          → +4·e2
#   "- e1,2,3"       → -1·e1∧e2∧e3
#   "5 e1,2"         → +5·e12
#   "3*e12"          → +3·e12   (optional * separator)
_TERM_RE = re.compile(
    r"([+-]?)\s*"  # group 1 — sign (optional)
    r"(\d+(?:\.\d*)?|\.\d+)?\s*"  # group 2 — coefficient (optional)
    r"(?:[*]\s*)?"  # optional '*' between coeff and blade
    r"(e[0-9]+(?:,[0-9]+)*|I)?"  # group 3 — blade name or pseudoscalar 'I'
    r"\s*"  # trailing whitespace
)


def _parse_mv_string(
    s: str, dim: int, named_basis: dict[str, dict[int, float]] | None = None
) -> dict[int, float]:
    """Parse a multivector expression string into a ``{blade_id: coefficient}`` dict.

    Accepts a sum of signed terms.  Each term may contain:

    * an optional sign (``+`` / ``-``),
    * an optional numeric coefficient (int or decimal float),
    * an optional blade name: ``e`` followed by comma-separated 1-based
      indices (``e1,2,3``) *or* the compact no-comma form for dim ≤ 9
      (``e12``).

    A bare number with no blade is the scalar part.  A bare blade with no
    coefficient has coefficient ±1.

    *named_basis* is an optional mapping from blade names (e.g. ``"e0"``)
    to their multi-blade expansions ``{blade_id: coefficient}``.  This
    allows composite blades (like the PGA3 null vector ``e0 = ep + em``)
    to be referenced by name in string expressions.

    Examples::

        "2.3 + 4 e2 + 5 e1,2 - e5,11,23"
        "-3 e1 + 2 e12"
        "1"          # scalar 1
        "e1 - e2"    # 1·e1 − 1·e2
    """
    from ._blade_names import blade_id as _to_id

    coeffs: dict[int, float] = {}
    for m in _TERM_RE.finditer(s):
        sign_s, coeff_s, blade_s = m.groups()
        if not coeff_s and not blade_s:
            continue  # empty match — nothing to record
        coeff = (float(coeff_s) if "." in coeff_s else int(coeff_s)) if coeff_s else 1
        if sign_s == "-":
            coeff = -coeff
        if blade_s and named_basis and blade_s in named_basis:
            # Composite blade — merge its expansion dict
            for bid, base_val in named_basis[blade_s].items():
                coeffs[bid] = coeffs.get(bid, 0) + coeff * base_val
        else:
            bid = _to_id(blade_s, dim) if blade_s else 0
            coeffs[bid] = coeffs.get(bid, 0) + coeff
    return coeffs
