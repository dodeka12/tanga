# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the theme registry loader and the themes/ directory invariant."""

from __future__ import annotations

import json
import re

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
    "controls/progress-bar.css",
    "controls/file-chooser.css",
    "controls/table.css",
    "views/group-view.css",
    "views/menu-view.css",
    "views/dialog-view.css",
    "views/banner-view.css",
    "views/overlay-view.css",
    "views/label-view.css",
    "views/message-view.css",
    "views/markdown-view.css",
    "views/params-view.css",
    "views/separator-view.css",
    "views/stack-view.css",
    "views/toolbar-view.css",
]


def _theme_css(rel: str) -> str:
    """Return the source of a stylesheet under ``themes/`` (posix relative path)."""
    return (_THEMES_DIR / rel).read_text(encoding="utf-8")


def test_list_themes() -> None:
    assert list_themes() == ["dark", "light", "pastel", "compact"]


def test_default_theme_is_dark() -> None:
    assert default_theme() == "dark"


def test_theme_label() -> None:
    assert theme_label("dark") == "Dark"
    assert theme_label("light") == "Light"
    assert theme_label("compact") == "Compact"


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


def test_compact_resolved_order() -> None:
    expected = [
        "base.css",
        "tokens.css",
        "compact/tokens.css",
        *_COMPONENTS,
        "compact/overrides/value-edit.css",
    ]
    assert theme_css_files("compact") == expected


def test_unknown_theme_raises() -> None:
    with pytest.raises(KeyError):
        theme_css_files("nope")


def test_missing_file_raises(tmp_path) -> None:  # noqa: ANN001
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
                    "dark": {
                        "label": "Dark",
                        "tokens": "dark/tokens.css",
                        "overrides": {},
                    },
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


def test_visualizer_theme_constructor_arg() -> None:
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False, theme="compact")
    assert viz.theme == "compact"

    with pytest.raises(KeyError):
        Visualizer(add_default_axes=False, add_default_grid=False, theme="nope")


def test_set_theme_emits_theme_define(monkeypatch) -> None:  # noqa: ANN001
    from pytanga.viz import Visualizer
    from pytanga.viz._themes import theme_css_files

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    pushed: list[dict] = []
    monkeypatch.setattr(
        viz._theme_host,
        "_push_theme",
        lambda: pushed.append(viz._theme_host._theme_message()),
    )

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


def _external_theme_dir(tmp_path):  # noqa: ANN001, ANN202
    d = tmp_path / "corp"
    (d / "overrides").mkdir(parents=True)
    (d / "tokens.css").write_text(":root { --tanga-bg: #000; }", encoding="utf-8")
    (d / "overrides" / "button.css").write_text(
        ".tanga-action-button {}", encoding="utf-8"
    )
    (d / "overrides" / "checkbox.css").write_text(
        ".tanga-checkbox-input {}", encoding="utf-8"
    )
    return d


def test_register_external_theme_resolution(tmp_path):  # noqa: ANN001, ANN201
    reg = ThemeRegistry()
    theme_dir = _external_theme_dir(tmp_path)
    reg.register("corp", theme_dir, label="Corporate")

    assert reg.list_themes() == ["dark", "light", "pastel", "compact", "corp"]
    assert reg.default_theme() == "dark"
    assert reg.theme_label("corp") == "Corporate"

    files = reg.theme_css_files("corp")
    assert files[:2] == ["base.css", "tokens.css"]
    idx_tokens = files.index("user/corp/tokens.css")
    idx_components = files.index(_COMPONENTS[0])
    idx_override = files.index("user/corp/overrides/button.css")
    assert idx_tokens < idx_components < idx_override
    assert "user/corp/overrides/checkbox.css" in files

    src_paths = {str(p) for p in reg.theme_css_paths("corp")}
    assert str(theme_dir / "tokens.css") in src_paths
    assert str(theme_dir / "overrides" / "button.css") in src_paths

    assert reg.external_theme_dirs() == {"user/corp": theme_dir.resolve()}

    watched = {str(p) for p in reg.theme_source_files("corp")}
    assert str(theme_dir / "tokens.css") in watched
    assert str(theme_dir / "overrides" / "button.css") in watched
    assert not any("base.css" in p for p in watched)


def test_register_duplicate_and_missing_tokens(tmp_path):  # noqa: ANN001, ANN201
    reg = ThemeRegistry()
    theme_dir = _external_theme_dir(tmp_path)
    reg.register("corp", theme_dir)

    with pytest.raises(ValueError):
        reg.register("corp", theme_dir)
    with pytest.raises(ValueError):
        reg.register("dark", theme_dir)

    missing = tmp_path / "missing"
    missing.mkdir()
    with pytest.raises(ValueError):
        reg.register("nope", missing)


def test_copy_theme(tmp_path):  # noqa: ANN001, ANN201
    from pytanga.viz import copy_theme

    dest = copy_theme("pastel", tmp_path / "mine")
    assert (dest / "tokens.css").is_file()
    assert (dest / "overrides" / "button.css").is_file()
    assert (dest / "overrides" / "checkbox.css").is_file()

    with pytest.raises(FileExistsError):
        copy_theme("pastel", tmp_path / "mine")
    copy_theme("pastel", tmp_path / "mine", overwrite=True)


def test_set_theme_and_refresh_emit_version(monkeypatch):  # noqa: ANN001, ANN201
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    pushed = []
    monkeypatch.setattr(
        viz._theme_host,
        "_push_theme",
        lambda: pushed.append(viz._theme_host._theme_message()),
    )

    viz.set_theme("light")
    assert pushed[-1]["theme"] == "light"
    assert pushed[-1]["version"] == 1

    viz.refresh_theme()
    assert pushed[-1]["theme"] == "light"
    assert pushed[-1]["version"] == 2


@pytest.mark.parametrize(
    ("token", "sheet"),
    [
        ("--tanga-group-title-font-size", "views/group-view.css"),
        ("--tanga-group-title-bg", "views/group-view.css"),
        ("--tanga-group-title-padding", "views/group-view.css"),
        ("--tanga-group-title-radius", "views/group-view.css"),
        ("--tanga-group-body-font-size", "views/group-view.css"),
        ("--tanga-group-toggle-font-size", "views/group-view.css"),
        ("--tanga-group-toggle-size", "views/group-view.css"),
        ("--tanga-group-padding", "views/group-view.css"),
        ("--tanga-group-header-padding", "views/group-view.css"),
        ("--tanga-group-header-margin-bottom", "views/group-view.css"),
        ("--tanga-group-header-gap", "views/group-view.css"),
        ("--tanga-group-small-padding", "views/group-view.css"),
        ("--tanga-group-small-title-font-size", "views/group-view.css"),
        ("--tanga-group-small-title-bg", "views/group-view.css"),
        ("--tanga-group-small-header-padding", "views/group-view.css"),
        ("--tanga-group-small-header-margin-bottom", "views/group-view.css"),
        ("--tanga-group-small-header-gap", "views/group-view.css"),
        ("--tanga-group-tiny-padding", "views/group-view.css"),
        ("--tanga-group-tiny-title-font-size", "views/group-view.css"),
        ("--tanga-group-tiny-title-bg", "views/group-view.css"),
        ("--tanga-group-tiny-header-padding", "views/group-view.css"),
        ("--tanga-group-tiny-header-margin-bottom", "views/group-view.css"),
        ("--tanga-group-tiny-header-gap", "views/group-view.css"),
        ("--tanga-font-size-log", "views/message-view.css"),
        ("--tanga-log-row-padding", "views/message-view.css"),
        ("--tanga-log-row-gap", "views/message-view.css"),
        ("--tanga-font-size-markdown", "views/markdown-view.css"),
        ("--tanga-markdown-table-cell-padding", "views/markdown-view.css"),
        ("--tanga-icon-size", "base.css"),
        ("--tanga-icon-button-icon-size", "controls/button.css"),
        ("--tanga-control-font-size", "controls/text-field.css"),
        ("--tanga-control-padding", "controls/text-field.css"),
        ("--tanga-control-label-margin-bottom", "base.css"),
        ("--tanga-button-font-size", "controls/button.css"),
        ("--tanga-button-padding", "controls/button.css"),
        ("--tanga-color-picker-height", "controls/color-picker.css"),
        ("--tanga-color-picker-padding", "controls/color-picker.css"),
        ("--tanga-step-button-icon-size", "controls/value-edit.css"),
    ],
)
def test_component_token_declared_and_consumed(token: str, sheet: str) -> None:
    assert re.search(re.escape(token) + r"\s*:", _theme_css("base.css")), (
        f"{token} is not declared in base.css"
    )
    assert re.search(re.escape(token) + r"\s*[,)]", _theme_css(sheet)), (
        f"{token} is not consumed by {sheet}"
    )


def test_group_variant_rules_rescope_tokens() -> None:
    css = _theme_css("views/group-view.css")
    for variant in ("small", "tiny"):
        selector = f".tanga-group.tanga-group-{variant}"
        start = css.index(selector)
        block = css[start : css.index("}", start)]
        for token in (
            "--tanga-group-padding",
            "--tanga-group-title-font-size",
            "--tanga-group-title-bg",
            "--tanga-group-header-padding",
        ):
            assert token in block, f"{selector} does not re-scope {token}"

    nested_start = css.index(".tanga-group.tanga-group-nested")
    nested_block = css[nested_start : css.index("}", nested_start)]
    assert "--tanga-group-small-padding" in nested_block
    assert "--tanga-group-small-title-font-size" in nested_block


def test_group_generic_consumers_use_base_tokens() -> None:
    css = _theme_css("base.css")
    consumers = {
        "--tanga-group-padding": "--tanga-group-padding-base",
        "--tanga-group-header-padding": "--tanga-group-header-padding-base",
        "--tanga-group-header-margin-bottom": "--tanga-group-header-margin-bottom-base",
        "--tanga-group-header-gap": "--tanga-group-header-gap-base",
    }
    for token, base in consumers.items():
        assert re.search(
            re.escape(token) + r"\s*:\s*var\(" + re.escape(base) + r"\)", css
        ), f"{token} does not default to {base}"


def test_compact_theme_targets_variant_titles() -> None:
    css = _theme_css("compact/tokens.css")
    assert "--tanga-group-title-font-size:" in css
    assert "--tanga-group-small-title-font-size:" in css
    assert "--tanga-group-tiny-title-font-size:" in css


def test_compact_theme_overrides_group_spacing() -> None:
    css = _theme_css("compact/tokens.css")
    for token in (
        "--tanga-stack-gap",
        "--tanga-group-padding-base",
        "--tanga-group-small-padding",
        "--tanga-group-tiny-padding",
    ):
        assert f"{token}:" in css


def test_compact_theme_tightens_control_chrome() -> None:
    css = _theme_css("compact/tokens.css")
    for token in (
        "--tanga-icon-control-size",
        "--tanga-icon-size",
        "--tanga-icon-button-icon-size",
        "--tanga-control-font-size",
        "--tanga-control-padding",
        "--tanga-control-label-margin-bottom",
        "--tanga-button-padding",
        "--tanga-color-picker-height",
        "--tanga-color-picker-padding",
        "--tanga-step-button-icon-size",
    ):
        assert f"{token}:" in css


def test_control_chrome_defaults_alias_type_scale() -> None:
    css = _theme_css("base.css")
    assert re.search(
        r"--tanga-control-font-size\s*:\s*var\(--tanga-font-size-body\)", css
    )
    assert re.search(
        r"--tanga-button-font-size\s*:\s*var\(--tanga-control-font-size\)", css
    )


def test_group_base_tokens_feed_all_variants() -> None:
    css = _theme_css("base.css")
    base_tokens = (
        "--tanga-group-padding-base",
        "--tanga-group-title-bg-base",
        "--tanga-group-header-padding-base",
        "--tanga-group-header-margin-bottom-base",
        "--tanga-group-header-gap-base",
    )
    for token in base_tokens:
        assert re.search(re.escape(token) + r"\s*:", css), f"{token} not declared"

    for variant in ("small", "tiny"):
        for suffix in (
            "padding",
            "title-bg",
            "header-padding",
            "header-margin-bottom",
            "header-gap",
        ):
            knob = f"--tanga-group-{variant}-{suffix}"
            base = f"--tanga-group-{suffix}-base"
            assert re.search(
                re.escape(knob) + r"\s*:\s*var\(" + re.escape(base) + r"\)", css
            ), f"{knob} does not default to {base}"


def test_every_used_token_is_declared() -> None:
    declared: set[str] = set()
    declaration = re.compile(r"(--tanga-[a-z0-9-]+)\s*:")
    for rel in (
        "base.css",
        "tokens.css",
        *(p.as_posix() for p in _THEMES_DIR.glob("*/tokens.css")),
    ):
        declared.update(declaration.findall(_theme_css(rel)))

    used: set[str] = set()
    usage = re.compile(r"var\((--tanga-[a-z0-9-]+)")
    for rel in ("base.css", *_COMPONENTS):
        used.update(usage.findall(_theme_css(rel)))

    missing = sorted(used - declared)
    assert not missing, f"tokens used but never declared: {missing}"


def test_type_scale_is_consumed() -> None:
    sources = [_theme_css(rel) for rel in ("base.css", *_COMPONENTS)]
    for token in ("--tanga-font-size-title", "--tanga-font-size-body"):
        assert any(f"var({token})" in css for css in sources), (
            f"{token} is declared but never consumed"
        )


def test_markdown_styles_tables() -> None:
    assert ".tanga-markdown-body table" in _theme_css("views/markdown-view.css")
