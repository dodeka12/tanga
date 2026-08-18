# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the frontend version hash helper."""

from pytanga.viz.server import compute_frontend_version


def test_returns_short_hex(tmp_path):
    (tmp_path / "viewer.html").write_text("<html></html>", encoding="utf-8")
    v = compute_frontend_version(tmp_path)
    assert isinstance(v, str)
    assert len(v) == 16
    int(v, 16)  # raises ValueError if not hex


def test_deterministic(tmp_path):
    (tmp_path / "a.js").write_text("hello", encoding="utf-8")
    assert compute_frontend_version(tmp_path) == compute_frontend_version(tmp_path)


def test_content_sensitive(tmp_path):
    f = tmp_path / "viewer.js"
    f.write_text("var a = 1;", encoding="utf-8")
    before = compute_frontend_version(tmp_path)
    f.write_text("var a = 2;", encoding="utf-8")
    assert compute_frontend_version(tmp_path) != before


def test_structure_sensitive(tmp_path):
    (tmp_path / "a.js").write_text("x", encoding="utf-8")
    before = compute_frontend_version(tmp_path)
    (tmp_path / "b.js").write_text("y", encoding="utf-8")
    assert compute_frontend_version(tmp_path) != before


def test_path_sensitive(tmp_path):
    (tmp_path / "a.js").write_text("same", encoding="utf-8")
    before = compute_frontend_version(tmp_path)
    (tmp_path / "a.js").rename(tmp_path / "renamed.js")
    assert compute_frontend_version(tmp_path) != before
