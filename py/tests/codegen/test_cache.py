# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
Tests for pytanga._cache — the build step is mocked so no C++ compilation
occurs. Validates key computation, lookup, store, invalidate, and clear.
"""

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Redirect the cache to a temporary directory for each test."""
    monkeypatch.setenv("PYTANGA_CACHE_DIR", str(tmp_path / "cache"))
    yield tmp_path / "cache"


class TestMakeKey:
    def test_same_inputs_same_key(self):
        from pytanga.codegen._cache import _make_key

        k1 = _make_key(3, 0, "float64")
        k2 = _make_key(3, 0, "float64")
        assert k1 == k2

    def test_different_dim(self):
        from pytanga.codegen._cache import _make_key

        assert _make_key(3, 0, "float64") != _make_key(4, 0, "float64")

    def test_different_dtype(self):
        from pytanga.codegen._cache import _make_key

        assert _make_key(3, 0, "float64") != _make_key(3, 0, "float32")


class TestLookup:
    def test_miss_on_empty_cache(self):
        from pytanga.codegen._cache import lookup

        assert lookup(3, 0, "float64") is None

    def test_hit_after_store(self, tmp_path, isolated_cache):
        from pytanga.codegen._cache import _make_key, lookup

        # Manually create a fake cache entry
        key = _make_key(3, 0, "float64")
        entry = isolated_cache / key
        cmake_bd = entry / "cmake_build"
        cmake_bd.mkdir(parents=True)
        fake_so = cmake_bd / "binding_dim3_sig0_f64.pyd"
        fake_so.write_bytes(b"fake")

        meta = {
            "dim": 3,
            "sig": 0,
            "dtype": "float64",
            "key": key,
            "module_name": "binding_dim3_sig0_f64",
            "so_path": "cmake_build/binding_dim3_sig0_f64.pyd",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        (entry / "meta.json").write_text(json.dumps(meta))

        assert lookup(3, 0, "float64") == fake_so

    def test_miss_when_so_deleted(self, isolated_cache):
        # Reproduce the entry but without the .so file — should return None
        from pytanga.codegen._cache import _make_key, lookup

        key = _make_key(3, 0, "float64")
        entry = isolated_cache / key
        entry.mkdir(parents=True)
        meta = {
            "dim": 3,
            "sig": 0,
            "dtype": "float64",
            "key": key,
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
        from pytanga.codegen._cache import _make_key, get_or_build

        fake_mod = MagicMock()

        # fake_so must live under the cache entry dir so relative_to() works
        key = _make_key(3, 0, "float64")
        fake_so = isolated_cache / key / "cmake_build" / "binding.so"

        with patch(
            "pytanga.codegen._cache.build_and_load",
            return_value=(fake_mod, fake_so),
        ) as mock_build:
            fake_so.parent.mkdir(parents=True, exist_ok=True)
            fake_so.write_bytes(b"fake")

            mod = get_or_build(3, 0, "float64")

        assert mock_build.call_count == 1
        assert mod is fake_mod

    def test_no_rebuild_on_second_call(self, isolated_cache):
        """Second call with the same params must not invoke build_and_load."""
        # Manually populate the cache
        from pytanga.codegen._cache import _make_key

        key = _make_key(3, 0, "float64")
        entry = isolated_cache / key
        cmake_bd = entry / "cmake_build"
        cmake_bd.mkdir(parents=True)
        fake_so = cmake_bd / "binding_dim3_sig0_f64.pyd"
        fake_so.write_bytes(b"fake")
        meta = {
            "dim": 3,
            "sig": 0,
            "dtype": "float64",
            "key": key,
            "module_name": "binding_dim3_sig0_f64",
            "so_path": "cmake_build/binding_dim3_sig0_f64.pyd",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        (entry / "meta.json").write_text(json.dumps(meta))

        fake_mod = MagicMock()
        with (
            patch("pytanga.codegen._cache.build_and_load") as mock_build,
            patch("pytanga.codegen._cache._load", return_value=fake_mod),
        ):
            from pytanga.codegen._cache import get_or_build

            mod = get_or_build(3, 0, "float64")

        assert mock_build.call_count == 0
        assert mod is fake_mod


class TestInvalidateAndClear:
    def test_invalidate_removes_entry(self, isolated_cache):
        from pytanga.codegen._cache import _make_key, invalidate, lookup

        key = _make_key(3, 0, "float64")
        entry = isolated_cache / key
        cmake_bd = entry / "cmake_build"
        cmake_bd.mkdir(parents=True)
        fake_so = cmake_bd / "binding_dim3_sig0_f64.pyd"
        fake_so.write_bytes(b"fake")
        meta = {
            "dim": 3,
            "sig": 0,
            "dtype": "float64",
            "key": key,
            "module_name": "binding_dim3_sig0_f64",
            "so_path": "cmake_build/binding_dim3_sig0_f64.pyd",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        (entry / "meta.json").write_text(json.dumps(meta))

        assert lookup(3, 0, "float64") is not None
        invalidate(3, 0, "float64")
        assert lookup(3, 0, "float64") is None

    def test_clear_removes_all(self, isolated_cache):
        from pytanga.codegen._cache import cache_root, clear

        isolated_cache.mkdir(parents=True, exist_ok=True)
        (isolated_cache / "some_entry").mkdir()
        clear()
        assert not cache_root().exists()
