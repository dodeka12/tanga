# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for least-squares recovery from overdetermined systems."""

import numpy as np
import pytest
from pytanga import Algebra, BladeMask, random_mask, random_mv
from pytanga.algebra import EProduct
from pytanga.solver.solve import solve_lsq


def _setup_lsq_system(alg, product, rng_seed):
    gen = np.random.default_rng(rng_seed)
    all_ids = alg.all_blades()
    a_mask = random_mask(alg, 8, rng=rng_seed)
    a_ids = a_mask.ids
    if product == EProduct.GP:
        reachable = set(all_ids)
    elif product == EProduct.OP:
        reachable = {k for k in all_ids if any((i & k) == 0 for i in a_ids)}
    elif product == EProduct.IP:
        reachable = {k for k in all_ids if any((i & k) == i for i in a_ids)}
    else:
        raise ValueError(f"unknown product {product!r}")
    reachable_ids = sorted(reachable)
    if len(reachable_ids) < 10:
        raise RuntimeError(
            f"Not enough reachable X blades ({len(reachable_ids)}) for {product!r}"
        )
    x_mask_ids = sorted(gen.choice(reachable_ids, size=10, replace=False).tolist())
    x_mask = BladeMask(alg, x_mask_ids)
    x_orig = random_mv(alg, mask=x_mask, rng=int(rng_seed + 2))
    a_list = [
        random_mv(alg, mask=a_mask, rng=int(rng_seed + 100 + i)) for i in range(10)
    ]
    if product == EProduct.GP:
        c_list = [a_i * x_orig for a_i in a_list]
    elif product == EProduct.IP:
        c_list = [a_i | x_orig for a_i in a_list]
    elif product == EProduct.OP:
        c_list = [a_i ^ x_orig for a_i in a_list]
    else:
        raise ValueError(f"unknown product {product!r}")
    return a_list, c_list, x_orig, x_mask


def _assert_x_recovered(x_orig, x_recovered, *, abs_tol=1e-8):
    d1 = x_orig.to_dict()
    d2 = x_recovered.to_dict()
    all_keys = set(d1) | set(d2)
    for k in all_keys:
        assert d1.get(k, 0.0) == pytest.approx(d2.get(k, 0.0), abs=abs_tol)


class TestLeastSquares:
    @pytest.fixture(scope="module")
    def alg8(self):
        return Algebra(8, 0, "float64")

    @pytest.mark.parametrize(
        "product, seed",
        [
            (EProduct.GP, 1001),
            (EProduct.IP, 1002),
            (EProduct.OP, 1003),
        ],
    )
    def test_lsq_exact(self, alg8, product, seed):
        a_list, c_list, x_orig, x_mask = _setup_lsq_system(alg8, product, seed)
        x_rec = solve_lsq(a_list, c_list, product=product, b_mask=x_mask)
        _assert_x_recovered(x_orig, x_rec, abs_tol=1e-8)

    @pytest.mark.parametrize(
        "product, seed, noise_seed",
        [
            (EProduct.GP, 2001, 2002),
            (EProduct.IP, 2003, 2004),
            (EProduct.OP, 2005, 2006),
        ],
    )
    def test_lsq_noisy(self, alg8, product, seed, noise_seed):
        a_list, c_list, x_orig, x_mask = _setup_lsq_system(alg8, product, seed)
        union_mask = BladeMask.from_array(c_list)
        gen = np.random.default_rng(noise_seed)
        c_noisy = []
        for ci in c_list:
            noisy_d = {}
            for bid in union_mask.ids:
                noisy_d[bid] = float(gen.uniform(-1e-3, 1e-3))
            noise_mv = alg8.multivector(noisy_d)
            c_noisy.append(ci + noise_mv)
        x_rec = solve_lsq(a_list, c_noisy, product=product, b_mask=x_mask)
        _assert_x_recovered(x_orig, x_rec, abs_tol=1e-2)
