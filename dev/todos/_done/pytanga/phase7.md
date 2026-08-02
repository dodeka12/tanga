# Phase 7 — Tests

**Overview plan:** [plan.md](plan.md)  
**Depends on:** Phase 1 (`_blade_names`, tested standalone), Phase 6 (full stack)  
**Required by:** nothing (final validation step)

---

## Goal

Write the four test files. They are ordered from least to most infrastructure
dependency so the first two can be run before any C++ is compiled.

Run the full suite with:
```powershell
python -m pytest pytanga/tests/ -v
```

---

## Test files

### 7.1 `pytanga/tests/test_blade_names.py` — no C++ required

```python
"""Tests for pytanga._blade_names — pure Python, no C++ compilation needed."""

import pytest
from pytanga._blade_names import blade_id, blade_name, grade, all_blades


# ---------------------------------------------------------------------------
# grade
# ---------------------------------------------------------------------------
class TestGrade:
    def test_scalar(self):
        assert grade(0) == 0

    def test_vector(self):
        assert grade(0b001) == 1
        assert grade(0b010) == 1
        assert grade(0b100) == 1

    def test_bivector(self):
        assert grade(0b011) == 2
        assert grade(0b101) == 2
        assert grade(0b110) == 2

    def test_pseudoscalar_3d(self):
        assert grade(0b111) == 3


# ---------------------------------------------------------------------------
# blade_name
# ---------------------------------------------------------------------------
class TestBladeName:
    def test_scalar(self):
        assert blade_name(0, 3) == "s"

    def test_pseudoscalar(self):
        assert blade_name(7, 3) == "I"

    def test_vectors(self):
        assert blade_name(1, 3) == "e1"
        assert blade_name(2, 3) == "e2"
        assert blade_name(4, 3) == "e3"

    def test_bivectors(self):
        assert blade_name(3, 3) == "e12"
        assert blade_name(5, 3) == "e13"
        assert blade_name(6, 3) == "e23"

    def test_out_of_range(self):
        with pytest.raises(ValueError):
            blade_name(8, 3)   # 8 >= 2^3


# ---------------------------------------------------------------------------
# blade_id
# ---------------------------------------------------------------------------
class TestBladeId:
    def test_scalar(self):
        assert blade_id("s", 3) == 0
        assert blade_id("0", 3) == 0

    def test_pseudoscalar(self):
        assert blade_id("I", 3) == 7

    def test_vectors(self):
        assert blade_id("e1", 3) == 1
        assert blade_id("e2", 3) == 2
        assert blade_id("e3", 3) == 4

    def test_bivectors(self):
        assert blade_id("e12", 3) == 3
        assert blade_id("e13", 3) == 5
        assert blade_id("e23", 3) == 6

    def test_order_independent(self):
        # e21 should give the same bitmask as e12
        assert blade_id("e21", 3) == blade_id("e12", 3)

    def test_index_out_of_range(self):
        with pytest.raises(ValueError):
            blade_id("e4", 3)   # dim=3, max index is 3

    def test_repeated_index(self):
        with pytest.raises(ValueError):
            blade_id("e11", 3)

    def test_roundtrip(self):
        for dim in (3, 4, 5):
            for b in range(1 << dim):
                name = blade_name(b, dim)
                assert blade_id(name, dim) == b


# ---------------------------------------------------------------------------
# all_blades
# ---------------------------------------------------------------------------
class TestAllBlades:
    def test_count(self):
        assert len(all_blades(3)) == 8
        assert len(all_blades(4)) == 16

    def test_sorted_by_grade(self):
        blades = all_blades(3)
        grades = [grade(b) for b in blades]
        assert grades == sorted(grades)

    def test_contains_all(self):
        assert set(all_blades(3)) == set(range(8))
```

---

### 7.2 `pytanga/tests/test_cache.py` — mocked build, no C++ required

```python
"""
Tests for pytanga._cache — the build step is mocked so no C++ compilation
occurs. Validates key computation, lookup, store, invalidate, and clear.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Redirect the cache to a temporary directory for each test."""
    monkeypatch.setenv("PYTANGA_CACHE_DIR", str(tmp_path / "cache"))
    yield tmp_path / "cache"


class TestMakeKey:
    def test_same_inputs_same_key(self):
        from pytanga._cache import _make_key
        k1 = _make_key(3, 0, "float64")
        k2 = _make_key(3, 0, "float64")
        assert k1 == k2

    def test_different_dim(self):
        from pytanga._cache import _make_key
        assert _make_key(3, 0, "float64") != _make_key(4, 0, "float64")

    def test_different_dtype(self):
        from pytanga._cache import _make_key
        assert _make_key(3, 0, "float64") != _make_key(3, 0, "float32")


class TestLookup:
    def test_miss_on_empty_cache(self):
        from pytanga._cache import lookup
        assert lookup(3, 0, "float64") is None

    def test_hit_after_store(self, tmp_path, isolated_cache):
        from pytanga._cache import lookup, _make_key, cache_root
        import shutil

        # Manually create a fake cache entry
        key      = _make_key(3, 0, "float64")
        entry    = isolated_cache / key
        cmake_bd = entry / "cmake_build"
        cmake_bd.mkdir(parents=True)
        fake_so  = cmake_bd / "binding_dim3_sig0_f64.pyd"
        fake_so.write_bytes(b"fake")

        meta = {
            "dim": 3, "sig": 0, "dtype": "float64",
            "key": key, "module_name": "binding_dim3_sig0_f64",
            "so_path": "cmake_build/binding_dim3_sig0_f64.pyd",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        (entry / "meta.json").write_text(json.dumps(meta))

        assert lookup(3, 0, "float64") == fake_so

    def test_miss_when_so_deleted(self, isolated_cache):
        # Reproduce the entry but without the .so file — should return None
        from pytanga._cache import lookup, _make_key

        key   = _make_key(3, 0, "float64")
        entry = isolated_cache / key
        entry.mkdir(parents=True)
        meta = {
            "dim": 3, "sig": 0, "dtype": "float64", "key": key,
            "module_name": "binding_dim3_sig0_f64",
            "so_path": "cmake_build/binding_dim3_sig0_f64.pyd",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        (entry / "meta.json").write_text(json.dumps(meta))
        # .so not created

        assert lookup(3, 0, "float64") is None


class TestGetOrBuild:
    def test_calls_build_on_miss(self, isolated_cache):
        """get_or_build should call build_and_load exactly once on a miss."""
        fake_mod = MagicMock()
        fake_mod.ALGEBRA_DIM = 8

        # We also need _find_extension to return a real path so meta.json can be written
        fake_so = isolated_cache / "fake.pyd"

        with (
            patch("pytanga._cache.build_and_load", return_value=fake_mod) as mock_build,
            patch("pytanga._cache._find_extension", return_value=fake_so),
        ):
            fake_so.parent.mkdir(parents=True, exist_ok=True)
            fake_so.write_bytes(b"fake")

            from pytanga._cache import get_or_build
            mod = get_or_build(3, 0, "float64")

        assert mock_build.call_count == 1
        assert mod is fake_mod

    def test_no_rebuild_on_second_call(self, isolated_cache):
        """Second call with the same params must not invoke build_and_load."""
        # Manually populate the cache
        from pytanga._cache import _make_key

        key      = _make_key(3, 0, "float64")
        entry    = isolated_cache / key
        cmake_bd = entry / "cmake_build"
        cmake_bd.mkdir(parents=True)
        fake_so  = cmake_bd / "binding_dim3_sig0_f64.pyd"
        fake_so.write_bytes(b"fake")
        meta = {
            "dim": 3, "sig": 0, "dtype": "float64", "key": key,
            "module_name": "binding_dim3_sig0_f64",
            "so_path": "cmake_build/binding_dim3_sig0_f64.pyd",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        (entry / "meta.json").write_text(json.dumps(meta))

        fake_mod = MagicMock()
        with (
            patch("pytanga._cache.build_and_load") as mock_build,
            patch("pytanga._cache._load", return_value=fake_mod),
        ):
            from pytanga._cache import get_or_build
            mod = get_or_build(3, 0, "float64")

        assert mock_build.call_count == 0
        assert mod is fake_mod


class TestInvalidateAndClear:
    def test_invalidate_removes_entry(self, isolated_cache):
        from pytanga._cache import _make_key, lookup, invalidate

        key   = _make_key(3, 0, "float64")
        entry = isolated_cache / key
        cmake_bd = entry / "cmake_build"
        cmake_bd.mkdir(parents=True)
        fake_so = cmake_bd / "binding_dim3_sig0_f64.pyd"
        fake_so.write_bytes(b"fake")
        meta = {
            "dim": 3, "sig": 0, "dtype": "float64", "key": key,
            "module_name": "binding_dim3_sig0_f64",
            "so_path": "cmake_build/binding_dim3_sig0_f64.pyd",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        (entry / "meta.json").write_text(json.dumps(meta))

        assert lookup(3, 0, "float64") is not None
        invalidate(3, 0, "float64")
        assert lookup(3, 0, "float64") is None

    def test_clear_removes_all(self, isolated_cache):
        from pytanga._cache import clear, cache_root
        isolated_cache.mkdir(parents=True, exist_ok=True)
        (isolated_cache / "some_entry").mkdir()
        clear()
        assert not cache_root().exists()
```

---

### 7.3 `pytanga/tests/test_algebra_e3.py` — full stack, G(3,0)

```python
"""
Integration tests for G(3,0,0) — the 3D Euclidean geometric algebra.
These tests compile the binding on first run (may take ~10 s).
"""

import math
import pytest
import pytanga


@pytest.fixture(scope="module")
def alg():
    return pytanga.Algebra(dim=3, sig=0)


class TestConstants:
    def test_algebra_dim(self, alg):
        assert alg.algebra_dim == 8   # 2^3

    def test_pseudoscalar_id(self, alg):
        assert alg.pseudoscalar_id == 7   # 0b111


class TestBasisVectorSquares:
    """In G(3,0), every basis vector squares to +1."""

    @pytest.mark.parametrize("name", ["e1", "e2", "e3"])
    def test_vector_squares_to_positive_scalar(self, alg, name):
        e = alg.multivector({name: 1.0})
        sq = e * e
        assert abs(sq["s"] - 1.0) < 1e-9
        assert sq["e1"] == pytest.approx(0.0, abs=1e-9)

    def test_e1_e2_anticommute(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e2 = alg.multivector({"e2": 1.0})
        assert (e1 * e2)["e12"] == pytest.approx( 1.0, abs=1e-9)
        assert (e2 * e1)["e12"] == pytest.approx(-1.0, abs=1e-9)


class TestOuterProduct:
    def test_e1_wedge_e2_gives_e12(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e2 = alg.multivector({"e2": 1.0})
        result = e1 ^ e2
        assert result["e12"] == pytest.approx(1.0, abs=1e-9)

    def test_wedge_with_self_is_zero(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        result = e1 ^ e1
        assert result._impl.blade_count() == 0


class TestInverse:
    def test_inv_e12(self, alg):
        """In G(3,0), e12 * e12 = -1, so inv(e12) = -e12."""
        e12    = alg.multivector({"e12": 1.0})
        inv_e12 = ~e12
        assert inv_e12["e12"] == pytest.approx(-1.0, abs=1e-9)

    def test_mv_times_inv_is_scalar_one(self, alg):
        """a * inv(a) should give scalar 1 (up to precision)."""
        a = alg.multivector({"e1": 1.0, "e2": 2.0, "e12": -1.0})
        result = a * (~a)
        assert result["s"] == pytest.approx(1.0, abs=1e-9)
        # All non-scalar components should vanish
        for k, v in result._impl.to_dict().items():
            if k != 0:
                assert abs(v) < 1e-9, f"Non-scalar blade {k} = {v}"


class TestOperatorOverloads:
    def test_mul_operator(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e2 = alg.multivector({"e2": 1.0})
        assert (e1 * e2)["e12"] == pytest.approx(1.0, abs=1e-9)

    def test_xor_operator(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e2 = alg.multivector({"e2": 1.0})
        assert (e1 ^ e2)["e12"] == pytest.approx(1.0, abs=1e-9)


class TestRepr:
    def test_repr_nonzero(self, alg):
        mv = alg.multivector({"e1": 1.0})
        assert "e1" in repr(mv)

    def test_repr_zero(self, alg):
        mv = alg.multivector()
        assert repr(mv) == "0"
```

---

### 7.4 `pytanga/tests/test_modular.py` — integer dtype with congruence

```python
"""
Tests for G(3,0) with dtype='int64' and CCongruence_HMod.
Mirrors the pattern in source/Tan.App.Test/Test_Crypt_03.cpp.
"""

import pytest
import pytanga


@pytest.fixture(scope="module")
def alg():
    return pytanga.Algebra(dim=3, sig=0, dtype="int64")


MODULUS = 101   # a small prime


class TestIntegerAlgebra:
    def test_algebra_dim(self, alg):
        assert alg.algebra_dim == 8

    def test_gp_integer_coefficients(self, alg):
        e1 = alg.multivector({"e1": 3})
        e2 = alg.multivector({"e2": 5})
        result = e1 * e2
        # 3*e1 * 5*e2 = 15*e12; no modulus applied to gp itself
        assert result["e12"] == 15

    def test_inv_requires_modulus(self, alg):
        e1 = alg.multivector({"e1": 1})
        with pytest.raises((ValueError, TypeError)):
            alg.inv(e1)   # must fail: no modulus provided

    def test_inv_modular(self, alg):
        """a * inv(a, p) should give scalar congruent to 1 (mod p)."""
        a = alg.multivector({"e1": 3, "e2": 7})
        inv_a = alg.inv(a, MODULUS)
        result = a * inv_a
        # Scalar coefficient should be 1 mod MODULUS
        scalar = result["s"] % MODULUS
        assert scalar == 1

    def test_not_invertible_raises(self, alg):
        zero_mv = alg.multivector()   # zero multivector
        with pytest.raises(RuntimeError):
            alg.inv(zero_mv, MODULUS)
```

---

## Running the tests incrementally

```bash
# Phase 1 done — run blade name tests immediately:
uv run pytest pytanga/tests/test_blade_names.py -v

# Phase 5 done — run cache tests (no C++ needed):
uv run pytest pytanga/tests/test_cache.py -v

# Phase 6 done — run full integration tests (will compile on first run):
uv run pytest pytanga/tests/test_algebra_e3.py -v -s
uv run pytest pytanga/tests/test_modular.py -v -s

# Full suite:
uv run pytest pytanga/tests/ -v
```

---

## Completion check

- [ ] `test_blade_names.py` — all tests pass
- [ ] `test_cache.py` — all tests pass (no C++ compiled)
- [ ] `test_algebra_e3.py` — all tests pass
- [ ] `test_modular.py` — all tests pass
- [ ] `pytest pytanga/tests/` exits with code 0
