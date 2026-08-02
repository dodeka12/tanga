# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for solve_mod."""

import pytest
from pytanga.solver.solve import solve_mod


class TestSolveMod:
    def test_solve_mod_matches_inv(self, alg_int):
        a = alg_int({"e1": 3, "e2": 5, 0: 1})
        x = solve_mod(a, 1, 97)
        ref = alg_int.inv(a, 97)
        assert x.to_dict() == ref.to_dict()

    def test_solve_mod_verifies(self, alg_int):
        a = alg_int({"e1": 3, "e2": 5, 0: 1})
        x = solve_mod(a, 1, 97)
        prod = alg_int.gp_mod(a, x, 97)
        assert prod.to_dict().get("s", 0) % 97 == 1

    def test_solve_mod_zero_raises(self, alg_int):
        with pytest.raises(RuntimeError):
            solve_mod(alg_int({}), 1, 97)

    def test_solve_mod_float_raises(self, alg_float):
        a = alg_float({"e1": 1.0})
        with pytest.raises(TypeError):
            solve_mod(a, 1.0, 97)
