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

    def __init__(
        self,
        dim: int,
        sig: int | tuple[int, ...] = 0,
        dtype: str = "float64",
        *,
        verbose: bool = False,
        modulus: int | None = None,
        print_fmt: str = ".4g",
        precision: float = 1e-10,
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
        self._precision = precision
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
    def precision(self) -> float:
        """Numerical zero tolerance for ``prune()``, ``is_zero()``, ``is_scalar()``."""
        return self._precision

    @precision.setter
    def precision(self, value: float) -> None:
        self._precision = float(value)

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
            # Build a named-basis dict for composite blades (e.g. e0 = ep + em in PGA3)
            # that cannot be resolved via the primitive blade_id() function.
            named_basis: dict[str, dict[int, float]] = {}
            for name, mv in self.blades().items():
                raw = mv._impl.to_dict()
                # A composite blade has more than one non-zero primitive blade
                if len(raw) > 1:
                    named_basis[name] = raw
            for bid, val in _parse_mv_string(
                coeffs, self._dim, named_basis or None
            ).items():
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

    def grade_proj(self, a: MV, grade: int | list[int]) -> MV:
        """Extract grade-k part ⟨A⟩_k, or sum of grade parts for a list.

        - ``int`` — extract grade‑*k* part (existing behaviour).
        - ``list[int]`` — extract sum of those grade parts, e.g.
          ``grade_proj([0, 2])`` returns the scalar + bivector part.
        """
        if isinstance(grade, list):
            result = self.multivector()
            for k in grade:
                result = self.add(result, self.grade_proj(a, k))
            return result
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

    # -----------------------------------------------------------------------
    # Phase A — Grade‑based involution & conjugation
    # -----------------------------------------------------------------------
    def grade_involution(self, a: MV) -> MV:
        """Grade involution: negate odd-grade parts.

        ``ginvol(⟨A⟩_k) = (−1)^k · ⟨A⟩_k``.
        """
        return self.even(a) - self.odd(a)

    def grade_conj(self, a: MV) -> MV:
        """Grade‑based Clifford conjugate (galgebra ``ccon``, metric‑independent).

        ``grade_conj(⟨A⟩_k) = (−1)^{k(k+1)/2} · ⟨A⟩_k``.
        Equivalent to ``grade_involution(self).rev()``.
        """
        return self.rev(self.grade_involution(a))

    # -----------------------------------------------------------------------
    # Phase A — Scalar product with optional reverse
    # -----------------------------------------------------------------------
    def scalar_product(self, a: MV, b: MV, *, rev: bool = False) -> float | int:
        """Scalar product with optional reverse of *a*.

        - ``rev=False`` (default): ``scalar_part(a * b)`` — same as ``sp(a, b)``.
        - ``rev=True``: ``scalar_part(rev(a) * b)``.

        This is galgebra's full ``sp(a, b, switch='rev')``.
        """
        if rev:
            a = self.rev(a)
        return self.sp(a, b)

    # -----------------------------------------------------------------------
    # Phase A — Quadratic form
    # -----------------------------------------------------------------------
    def qform(self, a: MV) -> float | int:
        """Quadratic form: ``scalar_part(rev(A) * A)``.

        In Euclidean algebra this equals ``mag2(A)``.  In non‑Euclidean
        algebras it may differ due to sign contributions from negative‑metric
        basis vectors.
        """
        return self.sp(self.rev(a), a)

    # -----------------------------------------------------------------------
    # Phase A — Even / odd grade extraction
    # -----------------------------------------------------------------------
    def even(self, a: MV) -> MV:
        """Extract the even‑grade part (grades 0, 2, 4, …)."""
        result = self.multivector()
        for k in range(0, self._dim + 1, 2):
            result = self.add(result, self.grade_proj(a, k))
        return result

    def odd(self, a: MV) -> MV:
        """Extract the odd‑grade part (grades 1, 3, 5, …)."""
        result = self.multivector()
        for k in range(1, self._dim + 1, 2):
            result = self.add(result, self.grade_proj(a, k))
        return result

    # -----------------------------------------------------------------------
    # Scalar product (original — kept unchanged)
    # -----------------------------------------------------------------------
    def sp(self, a: MV, b: MV) -> float | int:
        """Scalar product (scalar part of a * b)."""
        return self._mod.sp(a._impl, b._impl)

    # -----------------------------------------------------------------------
    # Phase B — Norm (quadratic‑form based)
    # -----------------------------------------------------------------------
    def norm2(self, a: MV) -> float:
        """Quadratic-form-based squared norm: ``|scalar_part(rev(A) * A)|``.

        In Euclidean algebras this equals ``mag2(A)``.  In non‑Euclidean
        algebras it gives the absolute value of the quadratic form, which
        may differ from the sum-of-squares magnitude.
        """
        return abs(self.qform(a))

    def norm(self, a: MV) -> float:
        """Quadratic-form-based norm: ``sqrt(norm2(A))``.

        The square root of ``|scalar_part(rev(A) * A)|``.
        """
        import math

        return math.sqrt(self.norm2(a))

    # -----------------------------------------------------------------------
    # Phase B — Exponential of a multivector
    # -----------------------------------------------------------------------
    def exp(self, a: MV) -> MV:
        """Exponential of a multivector whose square is a scalar.

        For a multivector ``A`` with ``A² = s ∈ ℝ``:

        - ``s > 0``: ``exp(A) = cosh(√s) + (sinh(√s)/√s) · A``
        - ``s = 0``: ``exp(A) = 1 + A``
        - ``s < 0``: ``exp(A) = cos(√|s|) + (sin(√|s|)/√|s|) · A``

        Raises ``ValueError`` if ``A²`` is not a scalar (i.e. ``A`` is not
        a "blade‑like" element).
        """
        import math

        a_sq = self.gp(a, a)
        if not self.is_scalar(a_sq):
            raise ValueError(
                "exp() requires A² to be a scalar; "
                "the multivector is not blade‑like."
            )
        s = self.scalar(a_sq)

        if s == 0:
            # exp(0) = 1 + A
            return self.add(self.multivector({0: 1.0}), a)
        elif s > 0:
            sqrt_s = math.sqrt(s)
            cosh_val = math.cosh(sqrt_s)
            sinc_val = math.sinh(sqrt_s) / sqrt_s
            return self.add(
                self.multivector({0: cosh_val}),
                self.scale(a, sinc_val),
            )
        else:  # s < 0
            sqrt_abs_s = math.sqrt(-s)
            cos_val = math.cos(sqrt_abs_s)
            sinc_val = math.sin(sqrt_abs_s) / sqrt_abs_s
            return self.add(
                self.multivector({0: cos_val}),
                self.scale(a, sinc_val),
            )

    def magnitude_sq(self, a: MV) -> float | int:
        """Sum of squared coefficients."""
        return self._mod.magnitude_sq(a._impl)

    # -----------------------------------------------------------------------
    # Phase D — Undual (algebra‑specific, can be overridden in subclasses)
    # -----------------------------------------------------------------------
    def undual(self, a: MV) -> MV:
        """Inverse of the signed dual: multiply by pseudoscalar I.

        In algebras with an invertible pseudoscalar (E3, P3, N3):
        ``undual(A) = A * I``, satisfying ``dual(undual(A)) == A``.

        Subclasses (BasisPGA3, BasisPGA2) override this for the J‑map.
        """
        I = self.multivector({self.pseudoscalar_id: 1.0})
        return self.gp(a, I)

    # -----------------------------------------------------------------------
    # Phase D — Commutator and anti‑commutator
    # -----------------------------------------------------------------------
    def cp(self, a: MV, b: MV) -> MV:
        """Commutator: ``(a * b - b * a) / 2``."""
        return self.scale(self.sub(self.gp(a, b), self.gp(b, a)), 0.5)

    def acp(self, a: MV, b: MV) -> MV:
        """Anti‑commutator: ``(a * b + b * a) / 2``."""
        return self.scale(self.add(self.gp(a, b), self.gp(b, a)), 0.5)

    # -----------------------------------------------------------------------
    # Phase D — Right contraction
    # -----------------------------------------------------------------------
    def rc(self, a: MV, b: MV) -> MV:
        """Right contraction ``A ⌊ B``.

        For pure-grade operands: ``grade(A) ≥ grade(B)`` keeps the parts
        yielding ``grade(A) − grade(B)``; otherwise zero.

        For general multivectors, decomposes into grade parts and sums.
        ``rc(A, B) = ip(B, A) * (−1)^{j·(k−j)}`` per grade-pair.
        """
        result = self.multivector()
        d_a = a._impl.to_dict()
        d_b = b._impl.to_dict()
        for bid_a, ca in d_a.items():
            ga = bin(bid_a).count("1")
            for bid_b, cb in d_b.items():
                gb = bin(bid_b).count("1")
                if ga < gb:
                    continue
                # rc = ip(B,A) * (−1)^{j·(k−j)}
                blade_a = self.multivector({bid_a: ca})
                blade_b = self.multivector({bid_b: cb})
                ip_ba = self.ip(blade_b, blade_a)
                sign = 1 if (ga * (gb - ga)) % 2 == 0 else -1
                result = self.add(result, self.scale(ip_ba, sign))
        return result

    # -----------------------------------------------------------------------
    # Phase D — gp_min (Hestenes inner product) and gp_max
    # -----------------------------------------------------------------------
    def gp_min(self, a: MV, b: MV) -> MV:
        """Hestenes inner product for pure blades: ``⟨AB⟩_{|k−j|}``.

        Both operands must be pure blades (single non‑zero grade).
        Raises ``ValueError`` otherwise.
        """
        if not self._is_pure_blade(a):
            raise ValueError("gp_min requires a pure blade as first operand")
        if not self._is_pure_blade(b):
            raise ValueError("gp_min requires a pure blade as second operand")
        ga = self._blade_grade(a)
        gb = self._blade_grade(b)
        gp_ab = self.gp(a, b)
        return self.grade_proj(gp_ab, abs(ga - gb))

    def gp_max(self, a: MV, b: MV) -> MV:
        """Outermost grade product for pure blades: ``⟨AB⟩_{k+j}``.

        Both operands must be pure blades (single non‑zero grade).
        Raises ``ValueError`` otherwise.
        For vectors this coincides with the outer product ``a ^ b``.
        """
        if not self._is_pure_blade(a):
            raise ValueError("gp_max requires a pure blade as first operand")
        if not self._is_pure_blade(b):
            raise ValueError("gp_max requires a pure blade as second operand")
        ga = self._blade_grade(a)
        gb = self._blade_grade(b)
        gp_ab = self.gp(a, b)
        return self.grade_proj(gp_ab, ga + gb)

    def _is_pure_blade(self, a: MV) -> bool:
        """True if *a* is a pure blade (all non‑zero coefficients share one grade)."""
        grades = set()
        for bid, v in a._impl.to_dict().items():
            if abs(v) >= self._precision:
                grades.add(bin(bid).count("1"))
                if len(grades) > 1:
                    return False
        return len(grades) == 1

    def _blade_grade(self, a: MV) -> int:
        """Return the single grade of a pure blade.  Assumes pure blade."""
        for bid, v in a._impl.to_dict().items():
            if abs(v) >= self._precision:
                return bin(bid).count("1")
        return 0

    def magnitude(self, a: MV) -> float:
        """sqrt(sum of squared coefficients)."""
        return self._mod.magnitude(a._impl)

    def is_zero(self, a: MV) -> bool:
        """True if all coefficients are within ``precision`` of zero."""
        tol = self._precision
        return all(abs(v) < tol for v in a._impl.to_dict().values())

    def is_scalar(self, a: MV) -> bool:
        """True if all non-scalar coefficients are within ``precision`` of zero."""
        tol = self._precision
        return all(
            abs(v) < tol
            for blade_id, v in a._impl.to_dict().items()
            if blade_id != 0
        )

    def project_to(self, a: MV, other: MV | int | list[int]) -> MV:
        """Restrict *a* to a blade set.

        - ``MV`` — retain only blades present in *other* (existing behaviour).
        - ``int`` — treat as a blade mask; retain only blades whose mask is
          a subset of this mask.
        - ``list[int]`` — treat as a list of blade IDs; retain only those
          exact blades.
        """
        if isinstance(other, MV):
            return MV(self._mod.project_to(a._impl, other._impl), self)
        if isinstance(other, int):
            mask = other
            result = self.multivector()
            d = a._impl.to_dict()
            for blade_id, v in d.items():
                if blade_id & ~mask == 0:
                    result = self.add(
                        result, self.scale(self.multivector({blade_id: 1.0}), v)
                    )
            return result
        if isinstance(other, list):
            result = self.multivector()
            d = a._impl.to_dict()
            for blade_id in other:
                v = d.get(blade_id, 0)
                if abs(v) > 0:
                    result = self.add(
                        result, self.scale(self.multivector({blade_id: 1.0}), v)
                    )
            return result
        raise TypeError(
            f"project_to expects MV, int, or list[int], got {type(other).__name__}"
        )

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
        display_basis : optional list of ``(name, blade, pinv, blade_id)`` tuples.
                        When provided, coefficients are extracted via
                        ``mv[blade_id]`` for simple blades, or ``ip(mv, pinv)``
                        for composite blades; otherwise the primitive blade
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
            for name, _blade, pinv, blade_id in display_basis:
                if blade_id is not None:
                    coeff = mv[blade_id]
                else:
                    coeff = self.ip(mv, pinv)[0]
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
        tol = self._precision
        if display_basis is not None:
            terms: list[tuple[float, str]] = []
            for name, _blade, pinv, blade_id in display_basis:
                if blade_id is not None:
                    coeff = mv[blade_id]
                else:
                    coeff = self.ip(mv, pinv)[0]
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
