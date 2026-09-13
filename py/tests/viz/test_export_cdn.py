# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Tests for the jsDelivr delivery-ref resolver."""

import pytest

from pytanga.viz.export._cdn import (
    DeliveryMode,
    _version_to_tag,
    build_bundle_url,
    resolve_delivery_ref,
)


def test_override_passthrough():  # noqa: ANN201
    assert resolve_delivery_ref("feat/view-architecture") == "feat/view-architecture"
    assert resolve_delivery_ref("abc1234") == "abc1234"


def test_version_to_tag_final():  # noqa: ANN201
    assert _version_to_tag("1.17.0") == "v1.17.0"


def test_version_to_tag_rc():  # noqa: ANN201
    assert _version_to_tag("1.17.0rc3") == "v1.17.0-rc3"


def test_version_to_tag_dev_raises():  # noqa: ANN201
    with pytest.raises(ValueError):
        _version_to_tag("1.17.0.dev5+gabc1234")


def test_resolve_ref_uses_installed_version(monkeypatch):  # noqa: ANN001, ANN201
    import pytanga.viz.export._cdn as cdn

    monkeypatch.setattr(cdn, "_git_ref", lambda: None)
    monkeypatch.setattr(cdn.importlib.metadata, "version", lambda _: "1.17.0")
    assert resolve_delivery_ref() == "v1.17.0"


def test_resolve_ref_uses_git_branch(monkeypatch):  # noqa: ANN001, ANN201
    import pytanga.viz.export._cdn as cdn

    monkeypatch.setattr(cdn, "_git_ref", lambda: "feat/view-architecture")
    assert resolve_delivery_ref() == "feat/view-architecture"


def test_resolve_ref_uses_git_tag(monkeypatch):  # noqa: ANN001, ANN201
    import pytanga.viz.export._cdn as cdn

    monkeypatch.setattr(cdn, "_git_ref", lambda: "v1.17.0")
    assert resolve_delivery_ref() == "v1.17.0"


def test_resolve_ref_falls_back_to_version_when_not_in_repo(monkeypatch):  # noqa: ANN001, ANN201
    import pytanga.viz.export._cdn as cdn

    monkeypatch.setattr(cdn, "_git_ref", lambda: None)
    monkeypatch.setattr(cdn.importlib.metadata, "version", lambda _: "1.17.0")
    assert resolve_delivery_ref() == "v1.17.0"


def test_build_bundle_url():  # noqa: ANN201
    expected = "https://cdn.jsdelivr.net/gh/dodeka12/tanga@v1.17.0/js/tanga-viewer.js"
    assert build_bundle_url("v1.17.0") == expected


def test_delivery_mode_values():  # noqa: ANN201
    assert set(DeliveryMode.__args__) == {"cdn", "inline", "offline"}
