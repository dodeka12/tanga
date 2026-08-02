# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.solver.solve — high-level equation solvers for GA."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask
from pytanga.algebra import EProduct
from pytanga.matrix import MVMatrix
from pytanga.algebra import MV

if TYPE_CHECKING:
    from pytanga.algebra import Algebra

from pytanga.blade_mask.predict import inverse_blade_mask, product_blade_mask
from pytanga.matrix.convert import from_matrix, to_matrix
from pytanga.matrix.product import product_matrix as build_product_matrix
from pytanga.algebra import MVLike, _as_mv


def _resolve_alg_from_solver_inputs(
    a: MVLike | list[MVLike],
    c: MVLike | list[MVLike],
    a_mask: BladeMask | None = None,
    b_mask: BladeMask | None = None,
    c_mask: BladeMask | None = None,
    algebra: "Algebra | None" = None,
) -> "Algebra":
    """Resolve the algebra from masks, MVs, or explicit kwarg."""
    for mask in (a_mask, b_mask, c_mask):
        if mask is not None:
            return mask.algebra

    def _mv_alg(xs: list):
        for x in xs:
            if isinstance(x, MV):
                return x.algebra
        return None

    if isinstance(a, list):
        alg = _mv_alg(a)
        if alg is not None:
            return alg
    else:
        if isinstance(a, MV):
            return a.algebra

    if isinstance(c, list):
        alg = _mv_alg(c)
        if alg is not None:
            return alg
    else:
        if isinstance(c, MV):
            return c.algebra

    if algebra is not None:
        return algebra

    raise ValueError("Cannot determine algebra — provide a mask, an MV, or algebra=")


def solve(
    a: MVLike,
    c: MVLike,
    *,
    a_mask: BladeMask | None = None,
    b_mask: BladeMask | None = None,
    c_mask: BladeMask | None = None,
    product: EProduct = EProduct.GP,
    left: bool = True,
    algebra: "Algebra | None" = None,
) -> "MV":
    r"""Solve A ∘ B = C for a unique B using Gaussian elimination.

    When *b_mask* is not provided, it is computed from *a_mask* and
    *c_mask* via ``inverse_blade_mask``, and *c_mask* is set to
    *b_mask* so the system is square.  When *c_mask* is provided but
    *b_mask* is not, *b_mask* is still derived from *a_mask* and
    *c_mask* via ``inverse_blade_mask``.

    Only available for float dtypes; use ``solve_mod`` for integer algebras.

    Parameters
    ----------
    a : MVLike
        The fixed-coefficient operand A.
    c : MVLike
        The target C.
    a_mask : BladeMask | None
        Blade mask for A.  If None, auto-derived from A.
    b_mask : BladeMask | None
        Blade mask for the unknown B.  If None, computed from *a_mask*
        and *c_mask* via ``inverse_blade_mask``.
    c_mask : BladeMask | None
        Blade mask for the result C.  If None, auto-derived.
    product : 'gp' | 'ip' | 'op'
        Which product to use.
    left : bool
        True = A ∘ B = C; False = B ∘ A = C.
    algebra : Algebra | None
        Needed only when *a* and *c* are bare strings/scalars and no
        mask is given.

    Raises
    ------
    TypeError
        When called on an integer-dtype algebra.
    ValueError
        When the derived system is not square (use ``solve_lsq`` instead).
    numpy.linalg.LinAlgError
        When the system is singular.
    """
    alg = _resolve_alg_from_solver_inputs(a, c, a_mask, b_mask, c_mask, algebra=algebra)

    if alg.dtype not in ("float32", "float64"):
        raise TypeError(
            "solve() is only for float dtypes; use solve_mod() for integer algebras"
        )

    # Derive a_mask and c_mask from the actual MVs before computing b_mask
    mv_a = _as_mv(alg, a)
    mv_c = _as_mv(alg, c)
    if a_mask is None:
        a_mask = BladeMask(mv_a)

    if b_mask is None:
        if c_mask is None:
            c_mask = BladeMask(mv_c)
            b_mask = inverse_blade_mask(a_mask, c_mask, product=product, left=left)
            c_mask = b_mask
        else:
            b_mask = inverse_blade_mask(a_mask, c_mask, product=product, left=left)
    else:
        if c_mask is None:
            c_mask = product_blade_mask(a_mask, b_mask, product=product, left=left)

    M = build_product_matrix(
        mv_a,
        a_mask=a_mask,
        b_mask=b_mask,
        c_mask=c_mask,
        product=product,
        left=left,
    )

    c_vec = to_matrix(mv_c, mask=M.c_mask)
    M2d = M.data[0]  # (|c_mask|, |b_mask|)
    if M2d.shape[0] != M2d.shape[1]:
        b_data, _, _, _ = np.linalg.lstsq(M2d, c_vec.data, rcond=None)[0]
        return from_matrix(MVMatrix(b_data.reshape(-1, 1), M.b_mask))

    x_arr = np.linalg.solve(M2d, c_vec.data)
    return from_matrix(MVMatrix(x_arr, M.b_mask))


def solve_lsq(
    a: MVLike | list[MVLike],
    c: MVLike | list[MVLike],
    *,
    a_mask: BladeMask | None = None,
    b_mask: BladeMask | None = None,
    c_mask: BladeMask | None = None,
    product: EProduct = EProduct.GP,
    left: bool = True,
    tol: float = 1e-10,
    algebra: "Algebra | None" = None,
) -> "MV":
    r"""Solve A ∘ X = C in the least-squares sense using ``numpy.linalg.lstsq``.

    Suitable for rank-deficient or overdetermined systems.  Only available
    for float dtypes.  When *b_mask* is not provided, it is computed from
    *a_mask* and *c_mask* via ``inverse_blade_mask``.

    When *a* and *c* are lists of the same length, the equations
    A_i ∘ X = C_i are stacked into a single overdetermined system and
    solved for a single X.

    Parameters
    ----------
    a : MVLike | list[MVLike]
        The fixed-coefficient operand A, or a list of operands A_i.
    c : MVLike | list[MVLike]
        The target C, or a list of targets C_i (same length as *a*).
    a_mask : BladeMask | None
        Blade mask for A.  If None, auto-derived from A (or union of A_i).
    b_mask : BladeMask | None
        Blade mask for the unknown X.  If None, computed from *a_mask*
        and *c_mask* via ``inverse_blade_mask``.
    c_mask : BladeMask | None
        Blade mask for the result C.  If None, auto-derived.
    product : 'gp' | 'ip' | 'op'
        Which product to use.
    left : bool
        True = A ∘ X = C; False = X ∘ A = C.
    tol : float
        Relative singular-value cutoff (``rcond`` passed to ``lstsq``).
    algebra : Algebra | None
        Needed only when *a* and *c* consist of bare strings/scalars and no
        mask is given.

    Raises
    ------
    TypeError
        When called on an integer-dtype algebra.
    ValueError
        When *a* and *c* are lists of different lengths, or one is a list
        while the other is a single MV.
    """
    alg = _resolve_alg_from_solver_inputs(a, c, a_mask, b_mask, c_mask, algebra=algebra)

    if alg.dtype not in ("float32", "float64"):
        raise TypeError(
            "solve_lsq() is only for float dtypes; use solve_mod() for integer algebras"
        )

    a_is_list = isinstance(a, list)
    c_is_list = isinstance(c, list)
    if a_is_list != c_is_list:
        raise ValueError(
            "a and c must both be single MVs or both be lists of the same length"
        )
    if a_is_list and len(a) != len(c):
        raise ValueError(
            f"a and c lists must have the same length, got {len(a)} and {len(c)}"
        )

    # Derive a_mask and c_mask from the actual MVs before computing b_mask
    if a_is_list:
        mvs_a = [_as_mv(alg, x) for x in a]
        mvs_c = [_as_mv(alg, x) for x in c]
        if a_mask is None:
            a_mask = BladeMask.from_array(mvs_a)
        b_mask_computed = b_mask
        c_mask_computed = c_mask
        if b_mask_computed is None:
            if c_mask_computed is None:
                c_mask_computed = BladeMask.from_array(mvs_c)
                b_mask_computed = inverse_blade_mask(
                    a_mask, c_mask_computed, product=product, left=left
                )
                c_mask_computed = b_mask_computed
            else:
                b_mask_computed = inverse_blade_mask(
                    a_mask, c_mask_computed, product=product, left=left
                )
        else:
            if c_mask_computed is None:
                c_mask_computed = product_blade_mask(
                    a_mask, b_mask_computed, product=product, left=left
                )

        a_arg = mvs_a
        c_arg = mvs_c
    else:
        mv_a = _as_mv(alg, a)
        mv_c = _as_mv(alg, c)
        if a_mask is None:
            a_mask = BladeMask(mv_a)
        b_mask_computed = b_mask
        c_mask_computed = c_mask
        if b_mask_computed is None:
            if c_mask_computed is None:
                c_mask_computed = BladeMask(mv_c)
                b_mask_computed = inverse_blade_mask(
                    a_mask, c_mask_computed, product=product, left=left
                )
                c_mask_computed = b_mask_computed
            else:
                b_mask_computed = inverse_blade_mask(
                    a_mask, c_mask_computed, product=product, left=left
                )
        else:
            if c_mask_computed is None:
                c_mask_computed = product_blade_mask(
                    a_mask, b_mask_computed, product=product, left=left
                )

        a_arg = mv_a
        c_arg = mv_c

    M = build_product_matrix(
        a_arg,
        a_mask=a_mask,
        b_mask=b_mask_computed,
        c_mask=c_mask_computed,
        product=product,
        left=left,
    )

    nb = len(M.b_mask)

    if a_is_list:
        M2d = M.data.reshape(-1, nb)
        b_vec_parts = [to_matrix(x, mask=M.c_mask).data for x in c_arg]
        b_vec = np.vstack(b_vec_parts)
    else:
        M2d = M.data[0]  # (nc, nb)
        b_vec = to_matrix(c_arg, mask=M.c_mask).data

    x_arr, _, _, _ = np.linalg.lstsq(M2d, b_vec, rcond=tol)
    return from_matrix(MVMatrix(x_arr.reshape(-1, 1), M.b_mask))


def solve_mod(
    a: MVLike,
    c: MVLike,
    modulus: int | None = None,
    *,
    a_mask: BladeMask | None = None,
    b_mask: BladeMask | None = None,
    c_mask: BladeMask | None = None,
    product: EProduct = EProduct.GP,
    left: bool = True,
    algebra: "Algebra | None" = None,
) -> "MV":
    r"""Solve A ∘ B = C (mod *modulus*) using Gaussian elimination in Z/pZ.

    Only available for integer dtypes; use ``solve`` for float algebras.
    The C++ modular solver currently supports the geometric product only.

    When *b_mask* is not provided, it is computed from *a_mask* and
    *c_mask* via ``inverse_blade_mask``.

    Parameters
    ----------
    a : MVLike
        The fixed-coefficient operand A.
    c : MVLike
        The target C.
    modulus : int
        The modulus (should be prime for full invertibility).  If None,
        the algebra's ``modulus`` attribute is used.
    product : EProduct
        Which product to use (currently only GP is supported).
    left : bool
        True => A ∘ B = C; False => B ∘ A = C.
    algebra : Algebra | None
        Needed only when *a* and *c* are bare strings/scalars and no
        mask is given.

    Raises
    ------
    TypeError
        When called on a float-dtype algebra.
    RuntimeError
        When the system has no unique solution modulo *modulus*.
    """
    alg = _resolve_alg_from_solver_inputs(a, c, a_mask, b_mask, c_mask, algebra=algebra)

    if alg.dtype not in ("int32", "int64"):
        raise TypeError(
            "solve_mod() is only for integer dtypes; use solve() for float algebras"
        )

    if modulus is None:
        if alg.modulus is None:
            raise ValueError("modulus must be specified")
        modulus = alg.modulus

    if isinstance(a, MV) and a.algebra is not alg:
        raise ValueError("a belongs to a different algebra")
    if isinstance(c, MV) and c.algebra is not alg:
        raise ValueError("c belongs to a different algebra")

    mv_a = _as_mv(alg, a)
    mv_c = _as_mv(alg, c)
    a_mask_computed = BladeMask(mv_a)
    if not a_mask_computed.ids:
        raise RuntimeError(
            "solve_mod: A has no non-zero blades; system is not invertible"
        )

    if b_mask is None:
        if c_mask is None:
            c_mask = BladeMask(mv_c)
            b_mask = inverse_blade_mask(
                a_mask_computed, c_mask, product=product, left=left
            )
            c_mask = b_mask
        else:
            b_mask = inverse_blade_mask(
                a_mask_computed, c_mask, product=product, left=left
            )
    else:
        if c_mask is None:
            c_mask = product_blade_mask(
                a_mask_computed, b_mask, product=product, left=left
            )

    # Use the closure as both col and row (square system)
    impl = alg._mod.solve_mod(mv_a._impl, mv_c._impl, b_mask.ids, c_mask.ids, modulus)
    return MV(impl, alg)
