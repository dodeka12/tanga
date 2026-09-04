# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Multivector wrapper for TANGA geometric algebra."""

from __future__ import annotations

from types import NotImplementedType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._algebra import Algebra
    from pytanga.blade_mask import BladeMask


class MV:
    """
    A multivector belonging to a specific Algebra instance.

    Coefficients are stored in the wrapped C++ DynMV object.
    Arithmetic operators delegate to the parent Algebra.
    """

    __slots__ = ("_impl", "_alg")

    def __init__(self, impl, alg: "Algebra") -> None:
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
            return NotImplemented
        return self._alg.add(self, other)

    def __radd__(self, other: "int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg.add(self._alg.multivector({0: other}), self)
        return NotImplemented

    def __sub__(self, other: "MV | int | float") -> "MV":
        if isinstance(other, (int, float)):
            other = self._alg.multivector({0: other})
        elif not isinstance(other, MV):
            return NotImplemented
        return self._alg.sub(self, other)

    def __rsub__(self, other: "int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg.sub(self._alg.multivector({0: other}), self)
        return NotImplemented

    def __mul__(self, other: "MV | int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg.scale(self, other)
        if isinstance(other, MV):
            return self._alg.gp(self, other)
        return NotImplemented

    def __rmul__(self, other: "int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg.scale(self, other)
        return NotImplemented

    def __truediv__(self, other: "MV | int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg.scale(self, 1.0 / other)
        if isinstance(other, MV):
            return self._alg.gp(self, self._alg.inv(other))
        return NotImplemented

    def __rtruediv__(self, other: "int | float") -> "MV":
        if isinstance(other, (int, float)):
            return self._alg.scale(self._alg.inv(self), other)
        return NotImplemented

    def __xor__(self, other: "MV") -> "MV | NotImplementedType":
        if not isinstance(other, MV):
            return NotImplemented
        return self._alg.op(self, other)

    def __or__(self, other: "MV") -> "MV | NotImplementedType":
        if not isinstance(other, MV):
            return NotImplemented
        return self._alg.ip(self, other)

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

    def to_dict(self) -> dict[str | int, float | int]:
        """Return {blade_name: coeff} for all non-zero blades."""
        from ._blade_names import blade_name

        dim = self._alg.dim
        return {blade_name(k, dim): v for k, v in self._impl.to_dict().items()}

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
    def gp(self, other: "MV") -> "MV":
        """Geometric product self * other  (same as ``self * other``)."""
        return self._alg.gp(self, other)

    def op(self, other: "MV") -> "MV":
        """Outer (wedge) product self ∧ other  (same as ``self ^ other``)."""
        return self._alg.op(self, other)

    def ip(self, other: "MV") -> "MV":
        """Inner product (symmetric)  (same as ``self | other``)."""
        return self._alg.ip(self, other)

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

    def vp(self, b: "MV") -> "MV":
        """Versor product: self * b * reverse(self)."""
        return self._alg.vp(self, b)

    def nvp(self, b: "MV") -> "MV":
        """Normalized versor product: self * b * inverse(self)."""
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

    def sp(self, other: "MV") -> float | int:
        """Scalar product (scalar part of self * other)."""
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

    def cp(self, other: "MV") -> "MV":
        """Commutator: ``(A * B − B * A) / 2``."""
        return self._alg.cp(self, other)

    def acp(self, other: "MV") -> "MV":
        """Anti‑commutator: ``(A * B + B * A) / 2``."""
        return self._alg.acp(self, other)

    def rc(self, other: "MV") -> "MV":
        """Right contraction ``A ⌊ B``."""
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

    def blade_factorize_versor(self) -> "tuple[MV, list[MV]]":
        """Factorize this versor into (scale, factor_vectors)."""
        return self._alg.blade_factorize_versor(self)

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
