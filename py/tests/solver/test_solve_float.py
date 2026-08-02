# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for float solve."""

import pytest
from pytanga.solver.solve import solve, solve_lsq


class TestSolveFloat:
    def test_solve_inverse(self, alg_float):
        a = alg_float({"e1": 1.0, "e2": -2.0, 0: 0.5})
        x = solve(a, 1.0)
        check = a * x
        check.prune()
        d = check.to_dict()
        assert len(d) == 1
        assert list(d.values())[0] == pytest.approx(1.0, abs=1e-9)

    def test_solve_general(self, alg_float):
        a = alg_float({"e1": 1.0, "e2": -2.0, 0: 0.5})
        y = alg_float({"e1": 3.0, 0: 1.0})
        x = solve(a, y)
        check = a * x
        check.prune()
        for name, val in y.to_dict().items():
            assert check.to_dict().get(name, 0.0) == pytest.approx(val, abs=1e-9)

    def test_solve_string_input(self, alg_float):
        a = alg_float({"e1": 1.0, "e2": -2.0, 0: 0.5})
        x1 = solve(a, 1.0)
        x2 = solve(a, "1")
        assert x1.to_dict() == x2.to_dict()

    def test_solve_integer_algebra_raises(self, alg_int):
        a = alg_int({"e1": 3})
        with pytest.raises(TypeError):
            solve(a, 1)

    def test_solve_lsq(self, alg_float):
        a = alg_float({"e1": 1.0, "e2": -2.0, 0: 0.5})
        x = solve_lsq(a, 1.0)
        check = a * x
        check.prune()
        assert list(check.to_dict().values())[0] == pytest.approx(1.0, abs=1e-8)
