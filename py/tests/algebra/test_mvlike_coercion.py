# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for MVLike coercion."""

import numpy as np
from pytanga import BladeMask
from pytanga.matrix.convert import to_matrix
from pytanga.solver.solve import solve, solve_mod


class TestMVLikeCoercion:
    def test_solve_scalar_coercion(self, alg_float):
        a = alg_float({"e1": 1.0, "e2": -2.0, 0: 0.5})
        x1 = solve(a, 1.0)
        x2 = solve(a, alg_float({0: 1.0}))
        assert x1.to_dict() == x2.to_dict()

    def test_solve_string_coercion(self, alg_float):
        a = alg_float({"e1": 1.0, "e2": -2.0, 0: 0.5})
        x1 = solve(a, "1")
        x2 = solve(a, 1.0)
        assert x1.to_dict() == x2.to_dict()

    def test_to_matrix_scalar(self, alg_float):
        mask = BladeMask(alg_float, grades=[0])
        m1 = to_matrix(0.5, mask=mask)
        m2 = to_matrix(alg_float({0: 0.5}), mask=mask)
        np.testing.assert_array_equal(m1.data, m2.data)

    def test_solve_mod_scalar_coercion(self, alg_int):
        a = alg_int({"e1": 3, "e2": 5, 0: 1})
        x1 = solve_mod(a, 1, 97)
        x2 = solve_mod(a, alg_int({0: 1}), 97)
        assert x1.to_dict() == x2.to_dict()
