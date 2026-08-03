# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Algebra class for TANGA geometric algebra."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from ._mv import MV
from ._parse import _parse_mv_string

if TYPE_CHECKING:
    from ._mv import MV


class Algebra:
    """
    A geometric algebra G(dim, sig) over values of type *dtype*.

    Parameters
    ----------
    dim   : vector-space dimension (1–32)
    sig   : signature bitmask — bit k=1 means basis vector e_{k+1} squares to -1
    dtype : 'float32' | 'float64' | 'int32' | 'int64'

    On first construction for a new (dim, sig, dtype), the C++ binding is
    compiled (~5–20 s). Subsequent constructions load the cached binary (~ms).
    """

    _NAMED_ALGEBRAS: dict[str, tuple[int, int]] = {
        "G2": (2, 0b00),
        "G3": (3, 0b000),
        # PGA2 / PGA3 are modelled via the null‑vector embedding
        # (see docs/py/pga_null_embedding.md). Two extra basis vectors are
        # added: one with +1, one with -1 metric.
        "PGA2": (4, 0b1000),  # dim=4, e4 squares to -1; null vector = e3 + e4
        "PGA3": (5, 0b10000),  # dim=5, e5 squares to -1; null vector = e4 + e5
        "CGA3": (5, 0b10000),  # conformal 3D: e5 squares to -1
        "STA": (4, 0b1110),  # spacetime algebra: e2, e3, e4 square to -1
    }

    # Names that have a dedicated Basis class (checked before _NAMED_ALGEBRAS)
    _BASIS_CLASS_NAMES: frozenset = frozenset(
        {"E2", "E3", "N2", "N3", "P2", "P3", "PGA2", "PGA3"}
    )

    @classmethod
    def from_name(cls, name: str, dtype: str = "float64", **kwargs) -> Algebra:
        """
        Create an Algebra (or Basis) instance from a short name.

        Parameters
        ----------
        name : str
            One of 'E3', 'P3', 'N3', 'PGA3',
            'G2', 'G3', 'PGA2', 'CGA3', 'STA'.
        dtype : str, optional
            Value type to use (default 'float64').
        **kwargs
            Passed through to the constructor, e.g. verbose.

        Returns
        -------
        Algebra or a BasisXxx subclass
        """
        if name in cls._BASIS_CLASS_NAMES:
            from pytanga.basis import _CLASS_MAP

            return _CLASS_MAP[name](dtype=dtype, **kwargs)
        if name not in cls._NAMED_ALGEBRAS:
            known = ", ".join(list(cls._BASIS_CLASS_NAMES) + list(cls._NAMED_ALGEBRAS))
            raise ValueError(f"Unknown algebra name {name!r}. Known: {known}")
        dim, sig = cls._NAMED_ALGEBRAS[name]
        return cls(dim, sig, dtype, **kwargs)

    def __init__(
        self,
        dim: int,
        sig: int | tuple[int, ...] = 0,
        dtype: str = "float64",
        *,
        verbose: bool = False,
        modulus: int | None = None,
        print_fmt: str = ".4g",
        seed: int | None = None,
    ) -> None:
        from pytanga.codegen import get_or_build

        if modulus is not None and dtype not in ("int32", "int64"):
            raise TypeError(
                "modulus can only be used with integer dtypes ('int32', 'int64')"
            )

        # Convert tuple signature to a bitmask.
        # Each element is a 1-based index of a basis vector that squares to -1.
        # e.g. (1, 4, 5) → e1, e4, e5 square to -1 → bitmask = 0b11001 = 25
        if isinstance(sig, tuple):
            bitmask = 0
            for idx in sig:
                if idx == 0:
                    raise ValueError(
                        "Signature index 0 is not valid; indices are 1-based "
                        "(use 1 for e1, 2 for e2, etc.)."
                    )
                if not (1 <= idx <= dim):
                    raise ValueError(
                        f"Signature index {idx} is out of range for dim={dim}; "
                        "each index must be in [1, dim]."
                    )
                bitmask |= 1 << (idx - 1)
            sig = bitmask

        self._dim = dim
        self._sig = sig
        self._dtype = dtype
        self._modulus = modulus
        self._print_fmt = print_fmt
        self._mod = get_or_build(dim, sig, dtype, verbose=verbose)
        self._rng = np.random.default_rng(seed)

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------
    @property
    def dim(self) -> int:
        return self._dim

    @property
    def sig(self) -> int:
        return self._sig

    @property
    def dtype(self) -> str:
        return self._dtype

    @property
    def modulus(self) -> int | None:
        """Modulus stored on this algebra, or None for float algebras."""
        return self._modulus

    @property
    def algebra_dim(self) -> int:
        """2 ** dim — total number of basis blades."""
        return self._mod.ALGEBRA_DIM

    @property
    def pseudoscalar_id(self) -> int:
        return self._mod.PSEUDOSCALAR_ID

    @property
    def rng(self) -> np.random.Generator:
        """NumPy random number generator instance belonging to this algebra."""
        return self._rng

    @property
    def print_fmt(self) -> str:
        """Python format spec for printing coefficients (default '.4g')."""
        return self._print_fmt

    # -----------------------------------------------------------------------
    # Factory
    # -----------------------------------------------------------------------
    def multivector(
        self,
        coeffs: dict | str | None = None,
    ) -> MV:
        """
        Create a multivector.

        *coeffs* may be:

        - ``None`` — zero multivector.
        - **dict with int keys** — raw blade bitmasks:
          ``{1: 1.0, 3: -0.5}`` → 1.0·e1 − 0.5·e12.
        - **dict with string keys** — blade names:
          ``{"e1": 1.0, "e12": -0.5}``.
        - **dict with tuple keys** — 1-based vector-index tuples;
          ``(0,)`` or ``()`` for the scalar:
          ``{(2,): 1, (1, 3, 5): 2}`` → 1·e2 + 2·e1∧e3∧e5.
        - **string expression** — a sum of signed terms:
          ``"2.3 + 4 e2 + 5 e1,2 - e5,11,23"``.
          Blade names use comma-separated 1-based indices or the compact
          form for dim ≤ 9.  A bare number is the scalar coefficient.
        """
        impl = self._mod.DynMV()
        if coeffs is None:
            pass
        elif isinstance(coeffs, str):
            for bid, val in _parse_mv_string(coeffs, self._dim).items():
                impl.set(bid, val)
        else:
            for key, val in coeffs.items():
                bid = self._resolve_key(key)
                impl.set(bid, val)
        return MV(impl, self)

    __call__ = multivector

    # -----------------------------------------------------------------------
    # GA operations
    # -----------------------------------------------------------------------
    def gp(self, a: MV, b: MV) -> MV:
        """Geometric product a * b."""
        if self._modulus is not None:
            return self.gp_mod(a, b, self._modulus)
        return MV(self._mod.gp(a._impl, b._impl), self)

    def op(self, a: MV, b: MV) -> MV:
        """Outer (wedge) product a ^ b."""
        if self._modulus is not None:
            return self.op_mod(a, b, self._modulus)
        return MV(self._mod.op(a._impl, b._impl), self)

    def ip(self, a: MV, b: MV) -> MV:
        """Inner product a | b."""
        if self._modulus is not None:
            return self.ip_mod(a, b, self._modulus)
        return MV(self._mod.ip(a._impl, b._impl), self)

    def gp_mod(self, a: MV, b: MV, modulus: int) -> MV:
        """Geometric product modulo *modulus* (integer dtypes only)."""
        if self._dtype not in ("int32", "int64"):
            raise TypeError("gp_mod() is only available for integer dtypes")
        return MV(self._mod.gp_mod(a._impl, b._impl, modulus), self)

    def op_mod(self, a: MV, b: MV, modulus: int) -> MV:
        """Outer product with modular congruence reduction (integer dtypes only)."""
        if self._dtype not in ("int32", "int64"):
            raise TypeError("op_mod() is only available for integer dtypes")
        return self.reduce(MV(self._mod.op(a._impl, b._impl), self), modulus)

    def ip_mod(self, a: MV, b: MV, modulus: int) -> MV:
        """Inner product with modular congruence reduction (integer dtypes only)."""
        if self._dtype not in ("int32", "int64"):
            raise TypeError("ip_mod() is only available for integer dtypes")
        return self.reduce(MV(self._mod.ip(a._impl, b._impl), self), modulus)

    def inv(self, a: MV, modulus: int | None = None) -> MV:
        """
        Multiplicative inverse.

        *modulus* is required for integer dtypes ('int32', 'int64') and
        ignored for floating-point dtypes.  When the algebra was constructed
        with a ``modulus``, that value is used as the default.
        """
        if self._dtype in ("int32", "int64"):
            mod = modulus if modulus is not None else self._modulus
            if mod is None:
                raise ValueError("modulus is required for integer dtypes")
            return MV(self._mod.inv(a._impl, mod), self)
        return MV(self._mod.inv(a._impl), self)

    def add(self, a: MV, b: MV) -> MV:
        """Component-wise addition a + b."""
        result = MV(self._mod.add(a._impl, b._impl), self)
        if self._modulus is not None:
            return self.reduce(result, self._modulus)
        return result

    def sub(self, a: MV, b: MV) -> MV:
        """Component-wise subtraction a - b."""
        result = MV(self._mod.sub(a._impl, b._impl), self)
        if self._modulus is not None:
            return self.reduce(result, self._modulus)
        return result

    def neg(self, a: MV) -> MV:
        """Unary negation -a."""
        return MV(self._mod.neg(a._impl), self)

    def scale(self, a: MV, s: float) -> MV:
        """Scalar scaling s * a."""
        result = MV(self._mod.scale(a._impl, s), self)
        if self._modulus is not None:
            return self.reduce(result, self._modulus)
        return result

    def rev(self, a: MV) -> MV:
        """Reverse of a multivector.

        Reverses the order of basis vectors in each blade, negating
        blades of grade k where k*(k-1)/2 is odd (grades 2 and 3 mod 4).
        """
        return MV(self._mod.rev(a._impl), self)

    def conj(self, a: MV) -> MV:
        """Clifford conjugate of a multivector.

        For each blade: conj(blade) = rev(blade) * (-1)^r, where r is
        the number of basis vectors in the blade that square to -1.
        Equivalent to applying both the reverse and the grade involution
        simultaneously.  In a Euclidean algebra (all positive metric)
        this reduces to the standard Clifford conjugate.
        """
        return MV(self._mod.conj(a._impl), self)

    def vp(self, versor: MV, b: MV) -> MV:
        """Versor product: versor * b * reverse(versor).

        Used for reflections, rotations and other orthogonal transformations.
        For integer algebras with a stored modulus the result is automatically
        reduced.
        """
        result = MV(self._mod.vp(versor._impl, b._impl), self)
        if self._modulus is not None:
            return self.reduce(result, self._modulus)
        return result

    def nvp(self, versor: MV, b: MV) -> MV:
        """Normalized versor product: versor * b * inverse(versor).

        Unlike vp(), which uses the reverse, nvp() uses the true algebraic
        inverse so the result is independent of the versor's magnitude.
        gp() auto-applies modular reduction for integer algebras.
        """
        inv_versor = self.inv(versor)
        return self.gp(self.gp(versor, b), inv_versor)

    def grade_proj(self, a: MV, grade: int) -> MV:
        """Extract grade-k part ⟨A⟩_k."""
        return MV(self._mod.grade_proj(a._impl, grade), self)

    def scalar(self, a: MV) -> float | int:
        """Return the scalar coefficient of a."""
        return self._mod.scalar(a._impl)

    def complement(self, a: MV) -> MV:
        """Compute the unsigned complement: blade mask is the bitwise complement
        within the algebra; complement(complement(A)) = A for all dimensions and
        signatures.  No sign changes are applied to coefficients.

        This is a purely combinatorial operation, NOT the Clifford dual.
        Use ``dual()`` for the geometrically correct dual ★A = A · I⁻¹."""
        return MV(self._mod.complement(a._impl), self)

    def dual(self, a: MV) -> MV:
        """Compute the signed dual ★A = A · I⁻¹.
        The dual-of-dual may introduce a sign change depending on dimension
        and signature: ★★A = (−1)^(D(D−1)/2 + s) · A.

        In G(3,0): ★(a ∧ b) = a × b  (the vector cross product)."""
        return MV(self._mod.dual(a._impl), self)

    def ldual(self, a: MV) -> MV:
        """Compute the left dual I · A.
        Left-multiplies by the pseudoscalar I without using its inverse.
        In G(3,0): ldual(a ∧ b) = −(a × b) = −dual(a ∧ b).

        This is simpler than the (right) dual for algebras where the
        pseudoscalar is not invertible (e.g. PGA), since it uses I
        directly with no pseudoinverse."""
        return MV(self._mod.ldual(a._impl), self)

    def sp(self, a: MV, b: MV) -> float | int:
        """Scalar product (scalar part of a * b)."""
        return self._mod.sp(a._impl, b._impl)

    def magnitude_sq(self, a: MV) -> float | int:
        """Sum of squared coefficients."""
        return self._mod.magnitude_sq(a._impl)

    def magnitude(self, a: MV) -> float:
        """sqrt(sum of squared coefficients)."""
        return self._mod.magnitude(a._impl)

    def is_zero(self, a: MV) -> bool:
        """True if all coefficients are zero."""
        return self._mod.is_zero(a._impl)

    def is_scalar(self, a: MV) -> bool:
        """True if only the scalar blade is non-zero."""
        return self._mod.is_scalar(a._impl)

    def project_to(self, a: MV, b: MV) -> MV:
        """Restrict a to the blade set of b (retain only blades present in b)."""
        return MV(self._mod.project_to(a._impl, b._impl), self)

    # Phase D: GP/IP/OP with reverse/conjugate flags
    def gp_rev(self, a: MV, b: MV, rev_a: bool = False, rev_b: bool = False) -> MV:
        """Geometric product with optional reverse on operands."""
        return MV(self._mod.gp_rev(a._impl, rev_a, b._impl, rev_b), self)

    def gp_conj(self, a: MV, b: MV, conj_a: bool = False, conj_b: bool = False) -> MV:
        """Geometric product with optional conjugate on operands."""
        return MV(self._mod.gp_conj(a._impl, conj_a, b._impl, conj_b), self)

    def ip_rev(self, a: MV, b: MV, rev_a: bool = False, rev_b: bool = False) -> MV:
        """Inner product with optional reverse on operands."""
        return MV(self._mod.ip_rev(a._impl, rev_a, b._impl, rev_b), self)

    def ip_conj(self, a: MV, b: MV, conj_a: bool = False, conj_b: bool = False) -> MV:
        """Inner product with optional conjugate on operands."""
        return MV(self._mod.ip_conj(a._impl, conj_a, b._impl, conj_b), self)

    def op_rev(self, a: MV, b: MV, rev_a: bool = False, rev_b: bool = False) -> MV:
        """Outer product with optional reverse on operands."""
        return MV(self._mod.op_rev(a._impl, rev_a, b._impl, rev_b), self)

    def op_conj(self, a: MV, b: MV, conj_a: bool = False, conj_b: bool = False) -> MV:
        """Outer product with optional conjugate on operands."""
        return MV(self._mod.op_conj(a._impl, conj_a, b._impl, conj_b), self)

    def reduce(self, a: MV, modulus: int) -> MV:
        """Apply half-space modular reduction: map all coefficients into [-mod/2, mod/2]."""
        if self._dtype not in ("int32", "int64"):
            raise TypeError("reduce() is only available for integer dtypes")
        return MV(self._mod.reduce(a._impl, modulus), self)

    def normalized(self, a: MV) -> MV:
        """Return the normal of a multivector (a / |a|)."""
        return a / self.magnitude(a)

    def grades(self, a: MV) -> list[int]:
        """List of grades present in this multivector (0..dim)."""
        return self._mod.grades(a._impl)

    def is_grade(self, a: MV, grade: int) -> bool:
        """Return True if all non-zero blades are of the given grade."""
        return self._mod.is_grade(a._impl, grade)

    # -----------------------------------------------------------------------
    # Blade operations (Phase E)
    # -----------------------------------------------------------------------
    def blade_inverse(self, blade: MV) -> MV:
        """Compute the proper inverse of a blade (caller must ensure input is a blade)."""
        return MV(self._mod.blade_inverse(blade._impl), self)

    def blade_pseudo_inverse(self, blade: MV) -> MV:
        """Compute the pseudo-inverse of a blade (uses conjugate instead of reverse)."""
        return MV(self._mod.blade_pseudo_inverse(blade._impl), self)

    def blade_factorize(self, blade: MV) -> list[MV]:
        """Factorize a blade into k normalized grade-1 vectors."""
        impls = self._mod.blade_factorize(blade._impl)
        return [MV(impl, self) for impl in impls]

    def blade_join(self, a: MV, b: MV) -> MV:
        """Compute the join of two blades."""
        return MV(self._mod.blade_join(a._impl, b._impl), self)

    def blade_factorize_versor(self, versor: MV) -> tuple[MV, list[MV]]:
        """Factorize a versor into (scale, factor_vectors)."""
        wScale_impl, vecFactors_impl = self._mod.blade_factorize_versor(versor._impl)
        return (MV(wScale_impl, self), [MV(impl, self) for impl in vecFactors_impl])

    def blade_project(self, a: MV, blade: MV) -> MV:
        """Project a multivector onto a blade."""
        return MV(self._mod.blade_project(a._impl, blade._impl), self)

    def blade_project_vec(self, mvs: list[MV], blade: MV) -> list[MV]:
        """Project each multivector in a list onto the same blade."""
        impls_in = [mv._impl for mv in mvs]
        impls_out = self._mod.blade_project_vec(impls_in, blade._impl)
        return [MV(impl, self) for impl in impls_out]

    def blade_reject(self, a: MV, blade: MV) -> MV:
        """Compute the rejection of a multivector from a blade."""
        return MV(self._mod.blade_reject(a._impl, blade._impl), self)

    def blade_reject_vec(self, mvs: list[MV], blade: MV) -> list[MV]:
        """Compute the rejection of each multivector in a list from the same blade."""
        impls_in = [mv._impl for mv in mvs]
        impls_out = self._mod.blade_reject_vec(impls_in, blade._impl)
        return [MV(impl, self) for impl in impls_out]

    # -----------------------------------------------------------------------
    # Blade name helpers
    # -----------------------------------------------------------------------
    def blade_id(self, name: str) -> int:
        from ._blade_names import blade_id

        return blade_id(name, self._dim)

    def blade_name(self, blade_id: int) -> str:
        from ._blade_names import blade_name

        return blade_name(blade_id, self._dim)

    def all_blades(self) -> list[int]:
        from ._blade_names import all_blades

        return all_blades(self._dim)

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------
    def blades(self) -> dict[str, MV]:
        """Return a dict of all named MV attributes on this instance.

        Useful for injecting basis blades into the local/global namespace::

            b = BasisE3()
            globals().update(b.blades())   # script scope
            print(e1 * e2)                 # works without the 'b.' prefix
        """
        return {k: v for k, v in self.__dict__.items() if isinstance(v, MV)}

    def _resolve_key(self, key: str | int | tuple) -> int:
        if isinstance(key, int):
            return key
        if isinstance(key, tuple):
            # (0,) or () → scalar; (i, j, ...) → bitmask with bits i-1, j-1, ...
            if not key or key == (0,):
                return 0
            result = 0
            for i in key:
                if i < 1:
                    raise ValueError(
                        f"Basis-vector index must be ≥ 1 (got {i}); "
                        "use (0,) for the scalar."
                    )
                if i > self._dim:
                    raise ValueError(
                        f"Basis-vector index {i} out of range for dim={self._dim}."
                    )
                result |= 1 << (i - 1)
            return result
        from ._blade_names import blade_id

        return blade_id(key, self._dim)

    def _get_display_basis(self) -> list | None:
        """Return the display basis to use, or None for the default primitive basis.

        Subclasses with a ``_display_basis`` attribute return it here.
        The base class returns None, which makes ``show_str`` fall back to
        primitive blade names via ``mv.to_dict()``.
        """
        return getattr(self, "_display_basis", None)

    @staticmethod
    def _format_coeffs_to_body(terms: list[tuple[float, str]], fmt: str) -> str:
        """Format a sorted list of ``(coeff, blade_name)`` pairs into a string."""
        if not terms:
            return "0"
        parts: list[str] = []
        for i, (c, name) in enumerate(terms):
            is_first = i == 0
            sign = (
                ("-" if is_first else " - ") if c < 0 else ("" if is_first else " + ")
            )
            abs_c = abs(c)
            if name == "s":
                parts.append(f"{sign}{format(abs_c, fmt)}")
            elif abs_c == 1.0:
                parts.append(f"{sign}{name}")
            else:
                parts.append(f"{sign}{format(abs_c, fmt)} {name}")
        return "".join(parts)

    def show_str(
        self,
        mv: MV,
        label: str = "",
        fmt: str | None = None,
        align_col: int = 30,
        display_basis: list | None = None,
    ) -> str:
        """Return *mv* as a human-readable string.

        This is the **single** place where a multivector string representation
        is created.  Basis subclasses pass their ``_display_basis`` to get
        composed blade names (e.g. ``einf``, ``eo`` instead of ``ep``, ``em``).

        Parameters
        ----------
        mv            : multivector to display
        label         : optional label printed left-aligned before the sum
        fmt           : Python format spec for coefficients (default None, uses algebra's print_fmt)
        align_col     : column to align the label (default 30)
        display_basis : optional list of ``(name, blade, dual)`` tuples.
                        When provided, coefficients are extracted via
                        ``ip(mv, dual)``; otherwise the primitive blade
                        basis (``mv.to_dict()``) is used.
        """
        if fmt is None:
            fmt = self.print_fmt

        if display_basis is None:
            display_basis = self._get_display_basis()

        tol = 1e-10
        if display_basis is not None:
            # Coefficient extraction via ip(mv, dual) for each display blade.
            terms: list[tuple[float, str]] = []
            for name, _blade, dual in display_basis:
                coeff = mv[0] if dual is None else self.ip(mv, dual)[0]
                if abs(coeff) < tol:
                    continue
                if abs(coeff - round(coeff)) < tol:
                    coeff = float(int(round(coeff)))
                terms.append((coeff, name))
            body = self._format_coeffs_to_body(terms, fmt)
        else:
            # Fallback: primitive blade basis via mv.to_dict().
            def _sort_key(name: str) -> tuple[int, int]:
                bid = 0 if name == "s" else self.blade_id(name)
                return (bin(bid).count("1"), bid)

            d = mv.to_dict()
            terms: list[tuple[float, str]] = []
            for name in sorted(d, key=_sort_key):
                v = d[name]
                if abs(v) < tol:
                    continue
                if abs(v - round(v)) < tol:
                    v = float(int(round(v)))
                terms.append((v, name))
            body = self._format_coeffs_to_body(terms, fmt)

        if label:
            return f"{label:<{align_col}}: {body}"
        else:
            return body

    def show(
        self, mv: MV, label: str = "", fmt: str | None = None, align_col: int = 30
    ) -> None:
        """Print *mv* as a human-readable sum with colour-coded coefficients.

        Parameters
        ----------
        mv        : multivector to display
        label     : optional label printed left-aligned before the sum
        fmt       : Python format spec for coefficients (default None, uses algebra's print_fmt)
        align_col : column to align the label (default 30)
        """
        if fmt is None:
            fmt = self.print_fmt

        try:
            from rich.console import Console
            from rich.text import Text

            console = Console()
            display_basis = self._get_display_basis()
            terms = self._extract_terms(mv, display_basis)

            rich_body = self._format_rich_body(terms, fmt)

            if label:
                text = Text.assemble(
                    (label, "bold white"),
                    (": ", "dim"),
                    rich_body,
                )
            else:
                text = rich_body
            console.print(text)
        except ImportError:
            print(self.show_str(mv, label=label, fmt=fmt, align_col=align_col))

    def _extract_terms(
        self, mv: MV, display_basis: list | None
    ) -> list[tuple[float, str]]:
        """Extract non-zero (coefficient, blade_name) pairs from *mv*."""
        tol = 1e-10
        if display_basis is not None:
            terms: list[tuple[float, str]] = []
            for name, _blade, dual in display_basis:
                coeff = mv[0] if dual is None else self.ip(mv, dual)[0]
                if abs(coeff) < tol:
                    continue
                if abs(coeff - round(coeff)) < tol:
                    coeff = float(int(round(coeff)))
                terms.append((coeff, name))
            return terms
        else:

            def _sort_key(name: str) -> tuple[int, int]:
                bid = 0 if name == "s" else self.blade_id(name)
                return (bin(bid).count("1"), bid)

            d = mv.to_dict()
            terms: list[tuple[float, str]] = []
            for name in sorted(d, key=_sort_key):
                v = d[name]
                if abs(v) < tol:
                    continue
                if abs(v - round(v)) < tol:
                    v = float(int(round(v)))
                terms.append((v, name))
            return terms

    @staticmethod
    def _format_rich_body(terms: list[tuple[float, str]], fmt: str):
        """Build a colour-coded rich Text from (coefficient, blade_name) pairs."""
        from rich.text import Text

        if not terms:
            return Text("0", style="dim")

        result = Text()
        for i, (c, name) in enumerate(terms):
            is_first = i == 0
            if c < 0:
                sign = "- " if is_first else " - "
            else:
                sign = "" if is_first else " + "

            if sign:
                result.append(sign, style="dim")

            abs_c = abs(c)
            coeff_str = format(abs_c, fmt)
            if name == "s":
                result.append(coeff_str, style="bright_white")
            elif abs_c == 1.0:
                result.append(name, style="cyan")
            else:
                result.append(coeff_str, style="bright_white")
                result.append(" ", style="dim")
                result.append(name, style="cyan")

        return result

    def __repr__(self) -> str:
        return f"Algebra(dim={self._dim}, sig={self._sig:#010b}, dtype={self._dtype!r})"
