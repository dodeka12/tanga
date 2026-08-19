# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Null-safe blade factorization — Python prototype (Option A + Option B).

Factorizes a k-blade into k grade-1 vectors, including null (degenerate)
blades, WITHOUT projecting onto the blade (which is undefined for null blades).

Algorithm (extract-and-divide, general metric — not e_inf/e_o specific):

  factorize(A):
      B = A
      while grade(B) >= 2:
          a = find_factor(B)       # Option A (probe E << B), fallback Option B
          b = partner(a)           # a if non-null, else basis vector with a.b != 0
          B = (b << B) / (a . b)   # divide out -> valid (grade-1) blade
      return factors + [B]

  Option A: for each coordinate (k-1)-blade E, v = E << B is a factor of B
            (grade-1, in B's subspace); return the first non-zero one.
  Option B: solve x ^ B == 0 for x via SVD of the matrix of the linear map
            x -> x ^ B (metric-free, always works).

Run:  uv run python dev/src/dev_factorize_blade_null.py
"""

from __future__ import annotations

import sys

import numpy as np

from pytanga.basis import BasisE3, BasisN3

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOL = 1e-9


def _dim(alg) -> int:
    return len(alg.all_blades()).bit_length() - 1


def _basis_vectors(alg, dim):
    return [alg.multivector({1 << bit: 1.0}) for bit in range(dim)]


def _grade_blade_ids(alg, dim, k):
    return [bid for bid in alg.all_blades() if bid.bit_count() == k]


def _find_factor_option_a(alg, B, kg, dim):
    """Probe with coordinate (kg-1)-blades; return first non-zero E << B."""
    for bid in _grade_blade_ids(alg, dim, kg - 1):
        E = alg.multivector({bid: 1.0})
        v = E.ip(B)  # E << B, grade 1
        if v.mag > TOL:
            return v
    return None


def _find_factor_option_b(alg, B, kg, dim, basis):
    """Solve x ^ B == 0 via SVD; return one non-trivial null-space vector."""
    k1_ids = _grade_blade_ids(alg, dim, kg + 1)
    M = np.zeros((len(k1_ids), dim))
    for j, e in enumerate(basis):
        w = e ^ B  # (kg+1)-blade
        for i, bid in enumerate(k1_ids):
            M[i, j] = float(w[bid])
    u, s, vh = np.linalg.svd(M)
    rank = int(np.sum(s > TOL * max(1.0, s[0] if s.size else 0.0)))
    if rank >= vh.shape[0]:
        return None
    x = vh[rank]  # one null-space vector (coefficients in the basis)
    v = sum((xi * basis[i] for i, xi in enumerate(x)), alg.multivector({}))
    return v if v.mag > TOL else None


def _partner(a, basis):
    """Return a vector b with a.b != 0 (a itself if non-null)."""
    if abs(a.sp(a)) > TOL:
        return a
    for e in basis:
        if abs(a.sp(e)) > TOL:
            return e
    raise ValueError("factor lies in the radical of the whole metric")


def factorize_blade_null(alg, A, *, tol: float = TOL):
    """Factorize a pure k-blade into k grade-1 vectors (null-safe)."""
    grades = A.grades
    if not grades or len(grades) != 1:
        raise ValueError(f"expected a pure blade, got grades {grades}")
    k = grades[0]
    if k == 0:
        raise ValueError("cannot factorize a scalar")

    dim = _dim(alg)
    basis = _basis_vectors(alg, dim)

    factors = []
    B = A
    while True:
        kg = B.grades[0]
        if kg == 1:
            factors.append(B)
            break

        a = _find_factor_option_a(alg, B, kg, dim)
        if a is None:
            a = _find_factor_option_b(alg, B, kg, dim, basis)
        if a is None:
            raise ValueError("failed to find a factor (blade may not be simple)")

        b = _partner(a, basis)
        B = b.ip(B) * (1.0 / a.sp(b))  # (b << B) / (a . b)
        factors.append(a)

    # Normalize by coefficient norm (matches the C++ FactorizeBlade contract).
    return [f / f.mag for f in factors]


def reconstruct(factors):
    r = factors[0]
    for f in factors[1:]:
        r = r ^ f
    return r


def check(name, alg, A):
    try:
        fac = factorize_blade_null(alg, A)
        recon = reconstruct(fac)
        # recon is a scalar multiple of A iff A ^ recon == 0 (same grade).
        err = (A ^ recon).mag
        gs = [f.grades for f in fac]
        status = "OK " if err < 1e-7 else "BAD"
        print(f"  [{status}] {name}: grades={A.grades} -> factor grades {gs}, "
              f"wedge-err={err:.2e}")
    except Exception as ex:  # noqa: BLE001 - diagnostic
        print(f"  [EXC] {name}: {type(ex).__name__}: {ex}")


def main() -> None:
    print("=== E3 (non-degenerate) ===")
    e3 = BasisE3()
    e1, e2, e3v = e3.e1, e3.e2, e3.e3
    check("e1^e2", e3, e1 ^ e2)
    check("e1^e2^e3", e3, e1 ^ e2 ^ e3v)
    check("(e1+2e2)^(3e1-e3)", e3, (e1 + 2 * e2) ^ (3 * e1 - e3v))

    print("=== N3 (conformal, includes null blades) ===")
    n3 = BasisN3()
    n1, n2, n3v = n3.e1, n3.e2, n3.e3
    einf, eo = n3.einf, n3.eo
    t = 0.5 * n1 + 0.3 * n2 + 0.1 * n3v

    check("t^einf (null bivector)", n3, t ^ einf)
    check("einf^eo (null bivector)", n3, einf ^ eo)
    check("e1^e2 (Euclid bivector)", n3, n1 ^ n2)
    check("t^einf^eo (null trivector)", n3, t ^ einf ^ eo)
    check("t^e1^e2 (Euclid trivector)", n3, t ^ n1 ^ n2)

    # Conformal points: Cop(x) = x + 0.5 x^2 e_inf + e_o (null vectors).
    def cop(x, y, z):
        rsq = x * x + y * y + z * z
        return (x * n1 + y * n2 + z * n3v) + (0.5 * rsq) * einf + eo

    p0, p1, p2 = cop(0, 0, 0), cop(1, 0, 0), cop(0, 1, 0)
    check("point pair p0^p1", n3, p0 ^ p1)
    check("point triple p0^p1^p2", n3, p0 ^ p1 ^ p2)
    check("p0^p1^p2^einf (null 4-blade)", n3, p0 ^ p1 ^ p2 ^ einf)
    check("dual(p0) (grade-4 null blade)", n3, p0.dual())

    # Compare with the built-in (currently broken for null blades).
    print("\n=== built-in blade_factorize for the same null cases ===")
    for name, A in [("t^einf", t ^ einf), ("p0^p1", p0 ^ p1)]:
        try:
            fac = A.blade_factorize()
            print(f"  [{name}] factor grades = {[f.grades for f in fac]}")
        except Exception as ex:  # noqa: BLE001
            print(f"  [{name}] EXC: {type(ex).__name__}: {str(ex).splitlines()[0]}")


if __name__ == "__main__":
    main()
