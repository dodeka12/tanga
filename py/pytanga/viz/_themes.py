# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Theme registry loader/validator for the Tanga viewer.

Resolves a theme id to an ordered CSS file list from
``templates/themes/registry.json``.  This is the single source of truth used by
both the live server (which injects ``<link>`` tags) and the export bundler
(which inlines the CSS into a single ``<style>`` block).

The resolved order is: ``base`` → default ``tokens`` → theme ``tokens`` →
``components`` → theme ``overrides``.  Later files win at equal specificity.
"""

from __future__ import annotations

import json
from pathlib import Path

_THEMES_DIR = Path(__file__).resolve().parent / "templates" / "themes"
_REGISTRY_PATH = _THEMES_DIR / "registry.json"


class ThemeRegistry:
    """Load and validate ``registry.json`` and resolve themes to CSS file lists.

    Every path in the registry is relative to the ``themes/`` directory.  The
    loader validates that each referenced file exists on disk and raises
    :class:`ValueError` for missing files and :class:`KeyError` for unknown
    theme ids.
    """

    def __init__(
        self,
        registry_path: Path = _REGISTRY_PATH,
        themes_dir: Path = _THEMES_DIR,
    ) -> None:
        self._registry_path = Path(registry_path)
        self._themes_dir = Path(themes_dir)

        data = json.loads(self._registry_path.read_text(encoding="utf-8"))
        self._base: list[str] = list(data.get("base", []))
        self._default_tokens: str | None = data.get("tokens")
        self._components: list[str] = list(data.get("components", []))
        self._themes: dict[str, dict[str, object]] = data.get("themes", {})

        self._validate()

    # ── Accessors ────────────────────────────────────────────────

    @property
    def themes_dir(self) -> Path:
        """The ``themes/`` directory the registry resolves paths against."""
        return self._themes_dir

    @property
    def components(self) -> list[str]:
        """The ordered component CSS file list (paths relative to ``themes/``)."""
        return list(self._components)

    def list_themes(self) -> list[str]:
        """Return the theme ids in registry order."""
        return list(self._themes.keys())

    def default_theme(self) -> str:
        """Return the default theme id (the first entry, ``"dark"``)."""
        themes = self.list_themes()
        if not themes:
            raise ValueError("theme registry declares no themes")
        return themes[0]

    def theme_label(self, theme_id: str) -> str:
        """Return the human-readable label for *theme_id*."""
        entry = self._entry(theme_id)
        return str(entry.get("label", theme_id))

    def theme_css_files(self, theme_id: str) -> list[str]:
        """Return the resolved CSS file list (paths relative to ``themes/``)."""
        return [p.relative_to(self._themes_dir).as_posix() for p in self._resolve(theme_id)]

    def theme_css_paths(self, theme_id: str) -> list[Path]:
        """Return the resolved CSS file list as absolute :class:`Path` objects."""
        return self._resolve(theme_id)

    # ── Resolution / validation ─────────────────────────────────

    def _entry(self, theme_id: str) -> dict[str, object]:
        try:
            entry = self._themes[theme_id]
        except KeyError:
            raise KeyError(f"unknown theme: {theme_id!r}") from None
        return dict(entry)

    def _resolve(self, theme_id: str) -> list[Path]:
        entry = self._entry(theme_id)

        rel: list[str] = []
        rel.extend(self._base)
        if self._default_tokens:
            rel.append(self._default_tokens)
        theme_tokens = entry.get("tokens")
        if theme_tokens:
            rel.append(str(theme_tokens))
        rel.extend(self._components)
        overrides = entry.get("overrides") or {}
        if not isinstance(overrides, dict):
            raise ValueError(
                f"theme {theme_id!r} 'overrides' must be an object of id → path"
            )
        rel.extend(str(p) for p in overrides.values())

        return [self._path(r) for r in rel]

    def _path(self, rel: str) -> Path:
        path = self._themes_dir / rel
        if not path.is_file():
            raise ValueError(f"theme registry references missing file: {rel}")
        return path.resolve()

    def _validate(self) -> None:
        if not isinstance(self._base, list):
            raise ValueError("registry 'base' must be a list of paths")
        if self._default_tokens is not None and not isinstance(self._default_tokens, str):
            raise ValueError("registry 'tokens' must be a single path string")
        if not isinstance(self._components, list):
            raise ValueError("registry 'components' must be a list of paths")

        # Force file validation for every referenced path up front.
        for rel in self._base:
            self._path(rel)
        if self._default_tokens:
            self._path(self._default_tokens)
        for rel in self._components:
            self._path(rel)

        if not isinstance(self._themes, dict) or not self._themes:
            raise ValueError("registry 'themes' must be a non-empty object")

        for theme_id, entry in self._themes.items():
            if not isinstance(entry, dict):
                raise ValueError(f"theme {theme_id!r} must be an object")
            if "tokens" not in entry or not entry.get("tokens"):
                raise ValueError(f"theme {theme_id!r} is missing a 'tokens' path")
            self._path(str(entry["tokens"]))
            overrides = entry.get("overrides") or {}
            if not isinstance(overrides, dict):
                raise ValueError(
                    f"theme {theme_id!r} 'overrides' must be an object of id → path"
                )
            for rel in overrides.values():
                self._path(str(rel))


# Module-level singleton, matching the plan's ``list_themes`` / ``theme_css_files``
# surface.  Imported by ``pytanga.viz`` and reused by the export bundler.
registry = ThemeRegistry()


def list_themes() -> list[str]:
    """Return the available theme ids in registry order."""
    return registry.list_themes()


def theme_label(theme_id: str) -> str:
    """Return the human-readable label for *theme_id*."""
    return registry.theme_label(theme_id)


def theme_css_files(theme_id: str) -> list[str]:
    """Return the resolved CSS file list for *theme_id* (relative to the themes dir)."""
    return registry.theme_css_files(theme_id)


def default_theme() -> str:
    """Return the default theme id (``"dark"``)."""
    return registry.default_theme()

