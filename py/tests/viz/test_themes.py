# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the theme registry loader and the themes/ directory invariant."""

from __future__ import annotations

import json

import pytest

from pytanga.viz import default_theme, list_themes, theme_css_files, theme_label
from pytanga.viz._themes import _THEMES_DIR, ThemeRegistry

_COMPONENTS = [
    "controls/button.css",
    "controls/slider.css",
    "controls/checkbox.css",
    "controls/dropdown.css",
    "controls/text-field.css",
    "controls/text-area.css",
    "controls/color-picker.css",
    "controls/value-edit.css",
    "controls/file-chooser.css",
    "controls/table.css",
    "views/group-view.css",
    "views/menu-view.css",
    "views/dialog-view.css",
    "views/banner-view.css",
    "views/overlay-view.css",
    "views/stack-view.css",
]


def test_list_themes() -> None:
    assert list_themes() == ["dark", "light", "pastel"]


def test_default_theme_is_dark() -> None:
    assert default_theme() == "dark"


def test_theme_label() -> None:
    assert theme_label("dark") == "Dark"
    assert theme_label("light") == "Light"


def test_dark_resolved_order() -> None:
    expected = ["base.css", "tokens.css", "dark/tokens.css", *_COMPONENTS]
    assert theme_css_files("dark") == expected


def test_light_resolved_order() -> None:
    expected = [
        "base.css",
        "tokens.css",
        "light/tokens.css",
        *_COMPONENTS,
        "light/overrides/button.css",
        "light/overrides/checkbox.css",
    ]
    assert theme_css_files("light") == expected


def test_pastel_resolved_order() -> None:
    expected = [
        "base.css",
        "tokens.css",
        "pastel/tokens.css",
        *_COMPONENTS,
        "pastel/overrides/button.css",
        "pastel/overrides/checkbox.css",
    ]
    assert theme_css_files("pastel") == expected


def test_unknown_theme_raises() -> None:
    with pytest.raises(KeyError):
        theme_css_files("nope")


def test_missing_file_raises(tmp_path) -> None:
    registry_path = tmp_path / "registry.json"
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    (themes_dir / "base.css").write_text("", encoding="utf-8")
    registry_path.write_text(
        json.dumps(
            {
                "base": ["base.css"],
                "tokens": "tokens.css",
                "components": [],
                "themes": {
                    "dark": {"label": "Dark", "tokens": "dark/tokens.css", "overrides": {}},
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        ThemeRegistry(registry_path=registry_path, themes_dir=themes_dir)


def test_components_drift_guard() -> None:
    """Every CSS under themes/controls and themes/views must be in components."""
    registry = ThemeRegistry()
    referenced = set(registry.components)

    on_disk = set()
    for sub in ("controls", "views"):
        for p in (_THEMES_DIR / sub).rglob("*.css"):
            on_disk.add(p.relative_to(_THEMES_DIR).as_posix())

    missing = on_disk - referenced
    stale = referenced - on_disk
    assert not missing, (
        "CSS files under themes/ are missing from registry 'components': "
        f"{sorted(missing)}"
    )
    assert not stale, (
        "registry 'components' lists CSS files that do not exist on disk: "
        f"{sorted(stale)}"
    )


def test_visualizer_theme_default_and_set() -> None:
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    assert viz.theme == "dark"

    viz.set_theme("light")
    assert viz.theme == "light"

    with pytest.raises(KeyError):
        viz.set_theme("nope")


def test_set_theme_emits_theme_define(monkeypatch) -> None:
    from pytanga.viz import Visualizer
    from pytanga.viz._themes import theme_css_files

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    pushed: list[dict] = []
    monkeypatch.setattr(viz, "_push_theme", lambda: pushed.append(viz._theme_message()))

    viz.set_theme("light")

    assert len(pushed) == 1
    msg = pushed[0]
    assert msg["type"] == "theme_define"
    assert msg["theme"] == "light"
    assert msg["label"] == "Light"
    assert msg["css"] == theme_css_files("light")


def test_set_theme_async_pushes_once() -> None:
    import asyncio

    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)

    class _FakeServer:
        def __init__(self) -> None:
            self.pushed: list[str] = []

        async def push_raw(self, data: str) -> None:
            self.pushed.append(data)

    viz._server = _FakeServer()
    asyncio.run(viz.set_theme_async("light"))

    assert len(viz._server.pushed) == 1
    msg = json.loads(viz._server.pushed[0])
    assert msg["type"] == "theme_define"
    assert msg["theme"] == "light"
    assert msg["label"] == "Light"


