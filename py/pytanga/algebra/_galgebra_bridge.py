# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Bridge between galgebra (sympy‑based) and tanga (numeric) multivectors.

All conversion logic lives in :class:`GalgebraBridge`.  The ``Algebra`` and
``MV`` classes are unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from ._algebra import Algebra
from ._display_basis import build_display_basis
from ._mv import MV

if TYPE_CHECKING:
    from galgebra.ga import Ga as _Ga
    from galgebra.mv import Mv as _Mv

__all__ = ["GalgebraBridge"]


class GalgebraBridge:
    """Bridge between galgebra (sympy) and tanga (numeric) geometric algebras.

    Parameters
    ----------
    metric : ndarray (n, n) or sympy Matrix
        The metric matrix from galgebra's ``Ga.g``.
    ga : galgebra.ga.Ga, optional
        If provided, enables ``to_galgebra()`` without passing *ga* each time.
    dtype : str
        tanga Algebra dtype (``'float64'`` or ``'float32'``).
    precision : float
        Numerical zero tolerance.

    Examples
    --------
    >>> from galgebra.ga import Ga
    >>> ga = Ga('e1 e2 e3', g=[1, 1, 1])
    >>> bridge = GalgebraBridge(np.diag([1, 1, 1]), ga=ga)
    >>> mv_ga = ga.mv([1.5, 2.0, 3.0], 'vector')
    >>> mv_tanga = bridge.from_galgebra(mv_ga)
    >>> bridge.show(mv_tanga, label='v')
    """

    def __init__(
        self,
        metric,
        *,
        ga: _Ga | None = None,
        dtype: str = "float64",
        precision: float = 1e-10,
    ) -> None:
        # ── 1. Convert metric to numpy ────────────────────────────
        try:
            g = np.array(metric, dtype=float).reshape(metric.shape)
        except AttributeError:
            g = np.asarray(metric, dtype=float)
        if g.ndim != 2 or g.shape[0] != g.shape[1]:
            raise ValueError(f"metric must be a square matrix, got shape {g.shape}")
        n = g.shape[0]
        if n < 1 or n > 32:
            raise ValueError(f"dimension {n} out of range [1, 32]")
        self._dim = n
        self._g = g

        # ── 2. Eigendecompose ─────────────────────────────────────
        eigvals, Q = np.linalg.eigh(g)
        self._eigvals = eigvals
        self._Q = Q

        # ── 3. Signature → Algebra ────────────────────────────────
        sig = 0
        for i, lam in enumerate(eigvals):
            if lam < -precision:
                sig |= 1 << i
        self._sig = sig
        self._alg = Algebra(dim=n, sig=sig, dtype=dtype, precision=precision)

        # ── 4. Orthogonal check ───────────────────────────────────
        off_diag = g - np.diag(np.diag(g))
        self._is_ortho = bool(np.all(np.abs(off_diag) < precision))

        # ── 5. Basis vectors (galgebra basis in tanga terms) ──────
        # T_fwd = D·Qᵀ where D = diag(√|λ|) → maps galgebra coords to tanga
        D = np.diag(np.sqrt(np.abs(eigvals)))
        T_fwd = D @ Q.T  # n×n
        self._basis_vecs: list[MV] = []
        for i in range(n):
            mv = self._alg.multivector()
            for j in range(n):
                coeff = T_fwd[j, i]
                if abs(coeff) >= precision:
                    mv = mv + self._alg.scale(
                        self._alg.multivector({1 << j: 1.0}), coeff
                    )
            self._basis_vecs.append(mv)

        # ── 6. Display basis ──────────────────────────────────────
        generators = [(f"e{i + 1}", self._basis_vecs[i]) for i in range(n)]
        self._display_basis = build_display_basis(generators, self._alg)
        object.__setattr__(self._alg, "_display_basis", self._display_basis)

        # ── 7. Build transformation matrices ────────────────────────
        # Use galgebra's blade ordering: ga.blades.flat / ga.indexes.flat
        # and tanga's primitive blade ordering: all_blades(dim)
        from ._blade_names import all_blades

        all_tanga_ids = all_blades(n)
        k = len(all_tanga_ids)  # 2^n

        # Forward map: {galgebra index tuple → tanga coeff dict}
        self._fwd_map: dict[tuple[int, ...], dict[int, float]] = {}
        for name, blade, pinv, _bid in self._display_basis:
            idx_tuple = self._name_to_index_tuple(name)
            self._fwd_map[idx_tuple] = dict(blade._impl.to_dict())

        # Build forward matrix M_fwd[tanga_row][ga_col]
        # where tanga_row follows all_tanga_ids ordering,
        # and ga_col follows display_basis ordering (which matches ga.blades.flat)
        tanga_id_to_row = {bid: i for i, bid in enumerate(all_tanga_ids)}
        M_fwd = np.zeros((k, k), dtype=float)
        all_tuples: list[tuple[int, ...]] = []
        for j, (name, blade, pinv, _bid) in enumerate(self._display_basis):
            idx_tuple = self._name_to_index_tuple(name)
            if idx_tuple not in all_tuples:
                all_tuples.append(idx_tuple)
            d = blade._impl.to_dict()
            for tanga_bid, coeff in d.items():
                if abs(coeff) >= precision:
                    row = tanga_id_to_row.get(tanga_bid)
                    if row is not None:
                        M_fwd[row, j] = coeff

        # Invert
        try:
            M_inv = np.linalg.inv(M_fwd)
        except np.linalg.LinAlgError:
            raise ValueError(
                "Cannot invert transformation matrix; "
                "the galgebra metric may be degenerate."
            )

        self._all_tuples = all_tuples
        self._M_inv = M_inv
        self._tanga_id_to_row = tanga_id_to_row
        self._all_tanga_ids = all_tanga_ids

        # ── 8. Store ga ───────────────────────────────────────────
        self._ga = ga

    # ── Properties ──────────────────────────────────────────────────

    @property
    def algebra(self) -> Algebra:
        """The tanga :class:`Algebra` instance."""
        return self._alg

    @property
    def dim(self) -> int:
        """Vector‑space dimension."""
        return self._dim

    @property
    def is_orthogonal(self) -> bool:
        """True if the galgebra metric was diagonal."""
        return self._is_ortho

    # ── Internal helpers ────────────────────────────────────────────

    def _name_to_index_tuple(self, name: str) -> tuple[int, ...]:
        """Parse display‑basis blade name into 0‑based index tuple."""
        if name == "s":
            return ()
        if name == "I":
            return tuple(range(self._dim))
        if name.startswith("e"):
            tail = name[1:]
            if tail.isdigit():
                return tuple(int(c) - 1 for c in tail)
            if "," in tail:
                return tuple(int(p) - 1 for p in tail.split(","))
        for d_name, d_blade, _pinv, _bid in self._display_basis:
            if d_name == name:
                d = d_blade._impl.to_dict()
                if d:
                    bid = max(d.keys(), key=lambda k: abs(d[k]))
                    return self._index_tuple_from_blade_id(bid)
        raise ValueError(f"Cannot determine index tuple for: {name!r}")

    @staticmethod
    def _index_tuple_from_blade_id(blade_id: int) -> tuple[int, ...]:
        return tuple(i for i in range(32) if blade_id & (1 << i))

    @staticmethod
    def _blade_id_from_index_tuple(idx_tuple: tuple[int, ...]) -> int:
        result = 0
        return result

    # ── Conversion ──────────────────────────────────────────────────

    def from_galgebra(self, mv: "_Mv") -> MV:
        """Convert a galgebra ``Mv`` to a tanga ``MV``.

        The galgebra MV must be numeric (no symbolic variables).
        Raises ``ValueError`` for symbolic coefficients.
        """
        import sympy

        obj = sympy.expand(mv.obj)

        # Check if the entire expression is symbolic (e.g., a bare Symbol)
        if not obj.is_number and obj.is_Atom and not obj.is_Number:
            raise ValueError(
                f"Purely symbolic galgebra MV: {obj!r}. "
                "Call .subs() / .evalf() on the galgebra Mv first."
            )

        coeff_dict = obj.as_coefficients_dict()

        result = self._alg.multivector()
        for blade, idx_tuple in zip(mv.Ga.blades.flat, mv.Ga.indexes.flat):
            coeff = coeff_dict.get(blade, 0)
            if coeff == 0:
                continue
            try:
                coeff_f = float(coeff)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Symbolic coefficient for blade {blade}: {coeff!r}. "
                    "Call .subs() / .evalf() on the galgebra Mv first."
                )
            if abs(coeff_f) < self._alg.precision:
                continue

            # Look up tanga blade coefficients for this galgebra blade
            tanga_blade_coeffs = self._fwd_map.get(idx_tuple, {})
            if tanga_blade_coeffs:
                for tanga_bid, t_coeff in tanga_blade_coeffs.items():
                    result = result + self._alg.scale(
                        self._alg.multivector({tanga_bid: 1.0}), coeff_f * t_coeff
                    )
            else:
                # Fallback: direct blade ID mapping
                bid = self._blade_id_from_index_tuple(idx_tuple)
                result = result + self._alg.scale(
                    self._alg.multivector({bid: 1.0}), coeff_f
                )
        return result

    def to_galgebra(self, mv: MV, ga: "_Ga | None" = None) -> "_Mv":
        """Convert a tanga ``MV`` to a galgebra ``Mv``.

        Requires *ga* passed at init or as argument.
        """
        import sympy

        ga_obj = ga or self._ga
        if ga_obj is None:
            raise ValueError(
                "to_galgebra() requires a galgebra Ga instance; "
                "pass ga= at init or as an argument."
            )

        # Build tanga coefficient vector in primitive blade order
        k = len(self._all_tanga_ids)
        coeffs_t = np.zeros(k, dtype=float)
        tanga_dict = mv._impl.to_dict()
        for tanga_bid, coeff in tanga_dict.items():
            row = self._tanga_id_to_row.get(tanga_bid)
            if row is not None:
                coeffs_t[row] = coeff

        # Solve for galgebra coefficients
        coeffs_ga = self._M_inv @ coeffs_t

        # Build sympy expression
        expr = sympy.S.Zero
        for j, idx_tuple in enumerate(self._all_tuples):
            coeff = coeffs_ga[j]
            if abs(coeff) < self._alg.precision:
                continue
            try:
                blade_sym = ga_obj.indexes_to_blades_dict[idx_tuple]
            except KeyError:
                continue
            expr = expr + sympy.Float(coeff) * blade_sym

        return ga_obj.mv(expr)

    # ── Display ─────────────────────────────────────────────────────

    def show(
        self, mv: MV, label: str = "", fmt: str | None = None, align_col: int = 30
    ) -> None:
        """Show *mv* using the galgebra display basis."""
        self._alg.show(mv, label, fmt=fmt, align_col=align_col)

    def show_str(
        self, mv: MV, label: str = "", fmt: str | None = None, align_col: int = 30
    ) -> str:
        """Return string repr of *mv* using the galgebra display basis."""
        return self._alg.show_str(mv, label, fmt=fmt, align_col=align_col)
