# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Multivector wrapper for TANGA geometric algebra."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

if TYPE_CHECKING:
    from ._algebra import Algebra
    from pytanga.blade_mask import BladeMask
    from pytanga.codegen._binding import DynMVBinding


def _expression_dispatch(name: str, a: "MV", b: Any) -> Any:
    """Delegate an MV product method to the expression layer for non-MV operands.

    Kept as a module-level function so the algebra module never imports the
    (higher-level) expression module at import time; the import happens lazily
    on first use.
    """
    import pytanga.expression as _expr

    return getattr(_expr, name)(a, b)


class MV:
    """
    A multivector belonging to a specific Algebra instance.

    Coefficients are stored in the wrapped C++ DynMV object.
    Arithmetic operators delegate to the parent Algebra.
    """

    __slots__ = ("_impl", "_alg")

    def __init__(self, impl: DynMVBinding, alg: "Algebra") -> None:
        self._impl = impl  # C++ DynMV
        self._alg = alg  # parent Algebra — keeps algebra metadata close

    # -----------------------------------------------------------------------
    # Coefficient access — accept both blade names and integer blade ids
    # -----------------------------------------------------------------------
    def __getitem__(self, key: str | int) -> float | int:
        blade_id, sign = self._alg._resolve_key_signed(key)
        return sign * self._impl.get(blade_id)

    def __setitem__(self, key: str | int, value: float | int) -> None:
        blade_id, sign = self._alg._resolve_key_signed(key)
        self._impl.set(blade_id, sign * value)

    # -----------------------------------------------------------------------
    # Arithmetic operators
    # -----------------------------------------------------------------------
    def __neg__(self) -> "MV":
        return self._alg.neg(self)

    def __add__(self, other: "MV | int | float") -> "MV":
        if isinstance(other, (int, float)):
            other = self._alg.multivector({0: other})
        elif not isinstance(other, MV):
            return NotImplemented  # type: ignore[return-value]
        return self._alg._add_impl(self, other)

    def __radd__(self, other: "int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg._add_impl(self._alg.multivector({0: other}), self)
        return NotImplemented  # type: ignore[return-value]

    def __sub__(self, other: "MV | int | float") -> "MV":
        if isinstance(other, (int, float)):
            other = self._alg.multivector({0: other})
        elif not isinstance(other, MV):
            return NotImplemented  # type: ignore[return-value]
        return self._alg._sub_impl(self, other)

    def __rsub__(self, other: "int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg._sub_impl(self._alg.multivector({0: other}), self)
        return NotImplemented  # type: ignore[return-value]

    def __mul__(self, other: "MV | int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg._scale_impl(self, other)
        if isinstance(other, MV):
            return self._alg._gp_impl(self, other)
        return NotImplemented  # type: ignore[return-value]

    def __rmul__(self, other: "int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg._scale_impl(self, other)
        return NotImplemented  # type: ignore[return-value]

    def __truediv__(self, other: "MV | int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg._scale_impl(self, 1.0 / other)
        if isinstance(other, MV):
            return self._alg._gp_impl(self, self._alg.inv(other))
        return NotImplemented  # type: ignore[return-value]

    def __rtruediv__(self, other: "int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg._scale_impl(self._alg.inv(self), other)
        return NotImplemented  # type: ignore[return-value]

    def __xor__(self, other: "MV") -> "MV":
        if not isinstance(other, MV):
            return NotImplemented  # type: ignore[return-value]
        return self._alg._op_impl(self, other)

    def __or__(self, other: "MV") -> "MV":
        if not isinstance(other, MV):
            return NotImplemented  # type: ignore[return-value]
        return self._alg._ip_impl(self, other)

    def __invert__(self) -> "MV":
        return self._alg.rev(self)

    # -----------------------------------------------------------------------
    # Representation
    # -----------------------------------------------------------------------
    def __repr__(self) -> str:
        if self._alg is None:
            return f"<MV (unbound) at {hex(id(self))}>"
        return self._alg.show_str(self)

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------
    @property
    def algebra(self) -> "Algebra":
        """Return the Algebra instance this multivector belongs to."""
        return self._alg

    @property
    def opns(self) -> bool:
        """The OPNS/IPNS interpretation flag inherited from this multivector's algebra."""
        return self._alg.opns

    @property
    def scalar(self) -> float | int:
        """The scalar coefficient."""
        return self._alg.scalar(self)

    @property
    def mag2(self) -> float | int:
        """Sum of squared coefficients."""
        return self._alg.magnitude_sq(self)

    @property
    def mag(self) -> float:
        """sqrt(sum of squared coefficients)."""
        return self._alg.magnitude(self)

    @property
    def is_zero(self) -> bool:
        """True if all coefficients are zero."""
        return self._alg.is_zero(self)

    @property
    def is_scalar(self) -> bool:
        """True if only the scalar blade is non-zero."""
        return self._alg.is_scalar(self)

    @property
    def grades(self) -> list[int]:
        """List of grades present in this multivector (0..dim)."""
        return self._alg.grades(self)

    # -----------------------------------------------------------------------
    # Utility
    # -----------------------------------------------------------------------
    def is_grade(self, k: int) -> bool:
        """True if this multivector is a pure grade-k element."""
        return self._alg.is_grade(self, k)

    def to_dict(self) -> dict[str, float | int]:
        """Return {blade_name: coeff} for all non-zero blades."""
        return {self._alg.blade_name(k): v for k, v in self._impl.to_dict().items()}

    def to_algebra(self, alg: "Algebra", blade_map: dict[int, int] | None = None) -> "MV":
        """Map this MV into another algebra by relabeling its blades.

        *blade_map* maps this MV's blade ids to *alg*'s blade ids.  When omitted,
        :class:`ValueError` is raised directing callers to a known map (e.g.
        ``pytanga.quadric.CONE_BLADE_MAP`` for a Q2→Q3 cone lift).
        """
        if blade_map is None:
            raise ValueError(
                "to_algebra() requires a blade_map "
                "(e.g. pytanga.quadric.CONE_BLADE_MAP for a Q2→Q3 cone lift)"
            )
        return alg.embed(self, blade_map)

    def prune(self, tol: float | int | None = None) -> "MV":
        """Remove coefficients with ``abs(coeff) < algebra.precision`` in-place and return self."""
        if tol is None:
            tol = self._alg._precision
        d = self._impl.to_dict()
        self._impl.reset()
        for blade_id, v in d.items():
            if abs(v) >= tol:
                self._impl.set(blade_id, v)
        return self

    def normalized(self) -> "MV":
        """Return the normalized MV (unit magnitude)."""
        return self._alg.normalized(self)

    # -----------------------------------------------------------------------
    # Named GA operations — delegate to the parent algebra so callers never
    # need to pass the algebra object explicitly.
    # -----------------------------------------------------------------------
    @overload
    def gp(self, other: "MV") -> "MV": ...
    @overload
    def gp(self, other: Any) -> Any: ...
    def gp(self, other: Any) -> Any:
        """Geometric product self * other  (same as ``self * other``)."""
        if not isinstance(other, MV):
            return _expression_dispatch("gp", self, other)
        return self._alg._gp_impl(self, other)

    @overload
    def op(self, other: "MV") -> "MV": ...
    @overload
    def op(self, other: Any) -> Any: ...
    def op(self, other: Any) -> Any:
        """Outer (wedge) product self ∧ other  (same as ``self ^ other``)."""
        if not isinstance(other, MV):
            return _expression_dispatch("op", self, other)
        return self._alg._op_impl(self, other)

    @overload
    def ip(self, other: "MV") -> "MV": ...
    @overload
    def ip(self, other: Any) -> Any: ...
    def ip(self, other: Any) -> Any:
        """Inner product (symmetric)  (same as ``self | other``)."""
        if not isinstance(other, MV):
            return _expression_dispatch("ip", self, other)
        return self._alg._ip_impl(self, other)

    def gp_mod(self, other: "MV", modulus: int) -> "MV":
        """Geometric product with explicit modular congruence reduction."""
        return self._alg.gp_mod(self, other, modulus)

    def op_mod(self, other: "MV", modulus: int) -> "MV":
        """Outer product with explicit modular congruence reduction."""
        return self._alg.op_mod(self, other, modulus)

    def ip_mod(self, other: "MV", modulus: int) -> "MV":
        """Inner product with explicit modular congruence reduction."""
        return self._alg.ip_mod(self, other, modulus)

    def reduce(self, modulus: int) -> "MV":
        """Apply half-space modular reduction: map all coefficients into [-mod/2, mod/2]."""
        return self._alg.reduce(self, modulus)

    def inv(self, modulus: int | None = None) -> "MV":
        """Multiplicative inverse.  Pass *modulus* for integer-dtype algebras."""
        return self._alg.inv(self, modulus)

    def rev(self) -> "MV":
        """Reverse: reverses the order of basis vectors in each blade."""
        return self._alg.rev(self)

    def conj(self) -> "MV":
        """Clifford conjugate: rev(self) * (-1)^r per blade."""
        return self._alg.conj(self)

    @overload
    def vp(self, b: "MV") -> "MV": ...
    @overload
    def vp(self, b: Any) -> Any: ...
    def vp(self, b: Any) -> Any:
        """Versor product: self * b * reverse(self)."""
        if not isinstance(b, MV):
            return _expression_dispatch("vp", self, b)
        return self._alg.vp(self, b)

    @overload
    def nvp(self, b: "MV") -> "MV": ...
    @overload
    def nvp(self, b: Any) -> Any: ...
    def nvp(self, b: Any) -> Any:
        """Normalized versor product: self * b * inverse(self)."""
        if not isinstance(b, MV):
            return _expression_dispatch("nvp", self, b)
        return self._alg.nvp(self, b)

    def grade(self, k: int | list[int]) -> "MV":
        """Extract grade-k part ⟨self⟩_k, or sum of grade parts for a list."""
        return self._alg.grade_proj(self, k)

    def complement(self) -> "MV":
        """Compute the unsigned complement: blade mask is the bitwise complement
        within the algebra; complement(complement(A)) = A for all dimensions and
        signatures.  No sign changes are applied to coefficients.

        This is a purely combinatorial operation, NOT the Clifford dual.
        Use ``dual()`` for the geometrically correct dual ★A = A · I⁻¹."""
        return self._alg.complement(self)

    def dual(self) -> "MV":
        """Compute the signed dual ★self = self · I⁻¹.
        The dual-of-dual may introduce a sign change depending on dimension
        and signature: ★★A = (−1)^(D(D−1)/2 + s) · A.

        In G(3,0): ★(a ∧ b) = a × b  (the vector cross product)."""
        return self._alg.dual(self)

    def ldual(self) -> "MV":
        """Compute the left dual I · self.
        Left-multiplies by the pseudoscalar I without using its inverse.
        In G(3,0): ldual(a ∧ b) = −(a × b) = −dual(a ∧ b).

        This is simpler than the (right) dual for algebras where the
        pseudoscalar is not invertible (e.g. PGA), since it uses I
        directly with no pseudoinverse."""
        return self._alg.ldual(self)

    @overload
    def sp(self, other: "MV") -> "float | int": ...
    @overload
    def sp(self, other: Any) -> Any: ...
    def sp(self, other: Any) -> Any:
        """Scalar product (scalar part of self * other)."""
        if not isinstance(other, MV):
            return _expression_dispatch("sp", self, other)
        return self._alg.sp(self, other)

    def project_onto(self, other: "MV | BladeMask") -> "MV":
        """Restrict self to a blade set, keeping only self's components.

        - ``MV`` — retain self's blades that are non-zero in *other*.
        - ``BladeMask`` — retain self's blades whose id is exactly in
          ``other.ids``.
        """
        return self._alg.project_onto(self, other)

    # -----------------------------------------------------------------------
    # Phase A — Grade‑based involution & conjugation
    # -----------------------------------------------------------------------
    def grade_involution(self) -> "MV":
        """Grade involution: negate odd-grade parts. ``ginvol(⟨A⟩_k) = (−1)^k · ⟨A⟩_k``."""
        return self._alg.grade_involution(self)

    def grade_conj(self) -> "MV":
        """Grade‑based Clifford conjugate. ``grade_conj(⟨A⟩_k) = (−1)^{k(k+1)/2} · ⟨A⟩_k``."""
        return self._alg.grade_conj(self)

    def scalar_product(self, other: "MV", *, rev: bool = False) -> float | int:
        """Scalar product with optional reverse of self.

        ``rev=True`` computes ``scalar_part(rev(self) * other)``.
        ``rev=False`` (default) is ``sp(self, other)``.
        """
        return self._alg.scalar_product(self, other, rev=rev)

    def qform(self) -> float | int:
        """Quadratic form: ``scalar_part(rev(A) * A)``."""
        return self._alg.qform(self)

    def even(self) -> "MV":
        """Extract the even‑grade part (grades 0, 2, 4, …)."""
        return self._alg.even(self)

    def odd(self) -> "MV":
        """Extract the odd‑grade part (grades 1, 3, 5, …)."""
        return self._alg.odd(self)

    # -----------------------------------------------------------------------
    # Phase B — Norm & exponentiation
    # -----------------------------------------------------------------------
    def norm2(self) -> float:
        """Quadratic-form-based squared norm: ``|scalar_part(rev(A) * A)|``."""
        return self._alg.norm2(self)

    def norm(self) -> float:
        """Quadratic-form-based norm: ``sqrt(norm2(A))``."""
        return self._alg.norm(self)

    def exp(self) -> "MV":
        """Exponential of a multivector whose square is a scalar."""
        return self._alg.exp(self)

    # -----------------------------------------------------------------------
    # Phase D — Duals & products
    # -----------------------------------------------------------------------
    def undual(self) -> "MV":
        """Inverse of the signed dual: ``A * I``."""
        return self._alg.undual(self)

    @overload
    def cp(self, other: "MV") -> "MV": ...
    @overload
    def cp(self, other: Any) -> Any: ...
    def cp(self, other: Any) -> Any:
        """Commutator: ``(A * B − B * A) / 2``."""
        if not isinstance(other, MV):
            return _expression_dispatch("cp", self, other)
        return self._alg.cp(self, other)

    @overload
    def acp(self, other: "MV") -> "MV": ...
    @overload
    def acp(self, other: Any) -> Any: ...
    def acp(self, other: Any) -> Any:
        """Anti‑commutator: ``(A * B + B * A) / 2``."""
        if not isinstance(other, MV):
            return _expression_dispatch("acp", self, other)
        return self._alg.acp(self, other)

    @overload
    def rc(self, other: "MV") -> "MV": ...
    @overload
    def rc(self, other: Any) -> Any: ...
    def rc(self, other: Any) -> Any:
        """Right contraction ``A ⌊ B``."""
        if not isinstance(other, MV):
            return _expression_dispatch("rc", self, other)
        return self._alg.rc(self, other)

    def gp_min(self, other: "MV") -> "MV":
        """Hestenes inner product for pure blades: ``⟨AB⟩_{|k−j|}``."""
        return self._alg.gp_min(self, other)

    def gp_max(self, other: "MV") -> "MV":
        """Outermost grade product for pure blades: ``⟨AB⟩_{k+j}``."""
        return self._alg.gp_max(self, other)

    # Phase D: GP/IP/OP with reverse/conjugate flags
    def gp_rev(
        self, other: "MV", rev_self: bool = False, rev_other: bool = False
    ) -> "MV":
        """Geometric product with optional reverse on operands."""
        return self._alg.gp_rev(self, other, rev_self, rev_other)

    def gp_conj(
        self, other: "MV", conj_self: bool = False, conj_other: bool = False
    ) -> "MV":
        """Geometric product with optional conjugate on operands."""
        return self._alg.gp_conj(self, other, conj_self, conj_other)

    def ip_rev(
        self, other: "MV", rev_self: bool = False, rev_other: bool = False
    ) -> "MV":
        """Inner product with optional reverse on operands."""
        return self._alg.ip_rev(self, other, rev_self, rev_other)

    def ip_conj(
        self, other: "MV", conj_self: bool = False, conj_other: bool = False
    ) -> "MV":
        """Inner product with optional conjugate on operands."""
        return self._alg.ip_conj(self, other, conj_self, conj_other)

    def op_rev(
        self, other: "MV", rev_self: bool = False, rev_other: bool = False
    ) -> "MV":
        """Outer product with optional reverse on operands."""
        return self._alg.op_rev(self, other, rev_self, rev_other)

    def op_conj(
        self, other: "MV", conj_self: bool = False, conj_other: bool = False
    ) -> "MV":
        """Outer product with optional conjugate on operands."""
        return self._alg.op_conj(self, other, conj_self, conj_other)

    def show_str(
        self, label: str = "", fmt: str | None = None, align_col: int = 30
    ) -> str:
        """Return this multivector as a string in the algebra's display basis."""
        return self._alg.show_str(self, label=label, fmt=fmt, align_col=align_col)

    def show(
        self, label: str = "", fmt: str | None = None, align_col: int = 30
    ) -> None:
        """Print this multivector in the algebra's display basis."""
        self._alg.show(self, label, fmt, align_col=align_col)

    # -----------------------------------------------------------------------
    # Phase E — Type checks & coefficients
    # -----------------------------------------------------------------------
    @property
    def is_vector(self) -> bool:
        """True if only grade‑1 blades have non‑zero coefficients."""
        return self._alg.is_vector(self)

    @property
    def is_base(self) -> bool:
        """True if this is exactly one basis blade with coefficient 1."""
        return self._alg.is_base(self)

    @property
    def is_blade(self) -> bool:
        """True if this is a simple r‑vector (blade)."""
        return self._alg.is_blade(self)

    @property
    def is_versor(self) -> bool:
        """True if this is a versor (product of invertible vectors)."""
        return self._alg.is_versor(self)

    def blade_coefs(self, blade_lst: list["MV"] | None = None) -> list[float]:
        """Coefficients for each blade in *blade_lst* (or all blades)."""
        return self._alg.blade_coefs(self, blade_lst)

    def components(self) -> list["MV"]:
        """Decompose into a list of single‑blade MVs."""
        return self._alg.components(self)

    def get_coefs(self, k: int) -> list[float]:
        """Grade‑*k* coefficients in canonical blade order."""
        return self._alg.get_coefs(self, k)

    # -----------------------------------------------------------------------
    # Blade operations (Phase E)
    # -----------------------------------------------------------------------
    def blade_inverse(self) -> "MV":
        """Compute the proper inverse of this blade (caller must ensure self is a blade)."""
        return self._alg.blade_inverse(self)

    def blade_pseudo_inverse(self) -> "MV":
        """Compute the pseudo-inverse of this blade: conjugate(A) / IP(A, conjugate(A)).

        This is an inverse only w.r.t. the inner product (<A . A^-1>_0 = 1), not
        the geometric product (except in a positive-definite metric).  A null
        (degenerate) blade has no geometric inverse at all; this is the only
        reciprocal such a blade has.  Use ``blade_inverse`` only for non-degenerate
        blades, where a geometric inverse exists.
        """
        return self._alg.blade_pseudo_inverse(self)

    def blade_factorize(self) -> list["MV"]:
        """Factorize this blade into k normalized grade-1 vectors."""
        return self._alg.blade_factorize(self)

    def join(self, other: "MV") -> "MV":
        """Compute the join of self and other.

        For the plane-based PGA models (``BasisPGA2``/``BasisPGA3``) this is the
        Gunn/Dorst ``join`` (union/span, regressive product).  For all other
        algebras it is the progressive product (the smallest-grade blade
        containing both).
        """
        return self._alg.join(self, other)

    def meet(self, other: "MV") -> "MV":
        """Compute the meet of self and other.

        For the plane-based PGA models (``BasisPGA2``/``BasisPGA3``) this is the
        Gunn/Dorst ``meet`` (intersection, progressive/outer product).  For all
        other algebras it is the regressive product (the largest-grade blade
        contained in both).
        """
        return self._alg.meet(self, other)

    def blade_factorize_versor(
        self, eps: float = 1e-6, max_iterations: int = 64
    ) -> "tuple[MV, list[MV]]":
        """Factorize this versor into (scale, factor_vectors).

        See :meth:`pytanga.algebra.Algebra.blade_factorize_versor` for the
        ``eps`` / ``max_iterations`` semantics.
        """
        return self._alg.blade_factorize_versor(
            self, eps=eps, max_iterations=max_iterations
        )

    def project(self, blade: "MV") -> "MV":
        """Project this multivector onto a non-degenerate blade: proj_N(A) = (A . N) N^-1.

        For a null (degenerate) blade there is no geometric inverse, so the
        pseudo-inverse is used as a fallback and the result is not a true
        orthogonal projection.
        """
        return self._alg.blade_project(self, blade)

    def reject(self, blade: "MV") -> "MV":
        """Compute the rejection of this multivector from a non-degenerate blade: A - proj_N(A).

        For a null (degenerate) blade there is no geometric inverse, so the
        pseudo-inverse is used as a fallback and the result is not a true
        orthogonal rejection.
        """
        return self._alg.blade_reject(self, blade)
