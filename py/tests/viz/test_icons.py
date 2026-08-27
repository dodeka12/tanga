# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Unit tests for pytanga.viz._icons — icon id grammar and enums."""

from __future__ import annotations

from pytanga.viz._icons import (
    EIconMaterial,
    EIconUC,
    Icon,
    icon_family,
    icon_name,
)


def test_material_enum_values_are_qualified() -> None:
    assert EIconMaterial.SETTINGS == "material:settings"
    assert EIconMaterial.PLAY_ARROW == "material:play_arrow"


def test_unicode_enum_values_are_qualified() -> None:
    assert EIconUC.PLAY == "uc:▶"
    assert EIconUC.GEAR == "uc:⚙"


def test_icon_family_prefixed() -> None:
    assert icon_family("material:settings") == "material"
    assert icon_family("uc:▶") == "uc"


def test_icon_family_bare_defaults_to_material() -> None:
    assert icon_family("settings") == "material"


def test_icon_name_prefixed() -> None:
    assert icon_name("material:settings") == "settings"
    assert icon_name("uc:▶") == "▶"


def test_icon_name_bare() -> None:
    assert icon_name("settings") == "settings"


def test_icon_accepts_enum_and_str() -> None:
    icons: list[Icon] = [
        EIconMaterial.SETTINGS,
        EIconUC.PLAY,
        "material:refresh",
    ]
    assert len(icons) == 3
