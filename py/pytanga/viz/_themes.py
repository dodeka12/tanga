# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Theme registry loader/validator for the Tanga viewer.

Resolves a theme id to an ordered CSS file list.  Bundled themes come from
``templates/themes/registry.json``; additional themes can be registered at
runtime with :func:`register_theme` from a local folder that provides a
``tokens.css`` (required) and optional ``overrides/*.css``.

Each resolved file carries two paths:

* ``served_rel`` — the URL path relative to ``themes/`` that the browser
  requests (bundled files use their on-disk relative path; external files use
  ``user/<id>/...``).
* ``source`` — the absolute path on disk (for export inlining, copying, and
  watching).

The resolved order is: ``base`` → default ``tokens`` → theme ``tokens`` →
``components`` → theme ``overrides``.  Later files win at equal specificity.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

_THEMES_DIR = Path(__file__).resolve().parent / "templates" / "themes"
_REGISTRY_PATH = _THEMES_DIR / "registry.json"


@dataclass(frozen=True)
class _ResolvedCss:
    """A single resolved CSS file (served URL path + source file)."""

    served_rel: str
    source: Path


@dataclass
class _ExternalTheme:
    """A runtime-registered theme folder."""

    label: str
    dir: Path
    served_prefix: str
    overrides: list[str]


class ThemeRegistry:
    """Load and validate ``registry.json`` and resolve themes to CSS file lists.

    Every path in the registry is relative to the ``themes/`` directory.  The
    loader validates that each referenced file exists on disk and raises
    :class:`ValueError` for missing files and :class:`KeyError` for unknown
    theme ids.  External themes registered with :meth:`register` live outside
    the bundled ``themes/`` directory and are served under ``themes/user/<id>/``.
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
        self._external: dict[str, _ExternalTheme] = {}

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
        """Return bundled theme ids followed by registered external ids."""
        return [*self._themes.keys(), *self._external.keys()]

    def default_theme(self) -> str:
        """Return the default theme id (the first bundled entry, ``"dark"``)."""
        themes = list(self._themes.keys())
        if not themes:
            raise ValueError("theme registry declares no themes")
        return themes[0]

    def theme_label(self, theme_id: str) -> str:
        """Return the human-readable label for *theme_id*."""
        ext = self._external.get(theme_id)
        if ext is not None:
            return ext.label
        entry = self._entry(theme_id)
        return str(entry.get("label", theme_id))

    def theme_css_files(self, theme_id: str) -> list[str]:
        """Return the resolved CSS file list (URL paths relative to ``themes/``)."""
        return [r.served_rel for r in self._resolve(theme_id)]

    def theme_css_paths(self, theme_id: str) -> list[Path]:
        """Return the resolved CSS file list as absolute source paths."""
        return [r.source for r in self._resolve(theme_id)]

    def theme_source_files(self, theme_id: str) -> list[Path]:
        """Return the theme's own source files (tokens + overrides), for watching."""
        ext = self._external.get(theme_id)
        if ext is not None:
            paths = [ext.dir / "tokens.css"]
            paths.extend(ext.dir / "overrides" / name for name in ext.overrides)
            return paths
        entry = self._entry(theme_id)
        paths = [self._path(str(entry["tokens"]))]
        overrides = entry.get("overrides") or {}
        paths.extend(self._path(str(rel)) for rel in overrides.values())
        return paths

    def theme_dir(self, theme_id: str) -> Path:
        """Return the theme's own directory (bundled subdir or external folder)."""
        ext = self._external.get(theme_id)
        if ext is not None:
            return ext.dir
        self._entry(theme_id)  # validate
        return self._themes_dir / theme_id

    def external_theme_dirs(self) -> dict[str, Path]:
        """Return ``{served_prefix: source_dir}`` for every external theme."""
        return {ext.served_prefix: ext.dir for ext in self._external.values()}

    # ── Registration ────────────────────────────────────────────

    def register(
        self,
        theme_id: str,
        theme_dir: str | Path,
        *,
        label: str | None = None,
    ) -> None:
        """Register an external theme folder.

        The folder must contain ``tokens.css``; a flat ``overrides/*.css``
        directory is optional and auto-discovered in sorted order.
        """
        if not theme_id or not str(theme_id).strip():
            raise ValueError("theme id must be a non-empty string")
        if theme_id in self._themes or theme_id in self._external:
            raise ValueError(f"theme already registered: {theme_id!r}")

        theme_dir = Path(theme_dir)
        if not (theme_dir / "tokens.css").is_file():
            raise ValueError(f"theme folder is missing tokens.css: {theme_dir}")

        overrides: list[str] = []
        overrides_dir = theme_dir / "overrides"
        if overrides_dir.is_dir():
            overrides = sorted(p.name for p in overrides_dir.glob("*.css"))

        self._external[theme_id] = _ExternalTheme(
            label=label if label is not None else theme_id,
            dir=theme_dir.resolve(),
            served_prefix=f"user/{theme_id}",
            overrides=overrides,
        )

    # ── Resolution / validation ─────────────────────────────────

    def _entry(self, theme_id: str) -> dict[str, object]:
        try:
            entry = self._themes[theme_id]
        except KeyError:
            raise KeyError(f"unknown theme: {theme_id!r}") from None
        return dict(entry)

    def _resolve(self, theme_id: str) -> list[_ResolvedCss]:
        resolved: list[_ResolvedCss] = []

        def _bundled(rel: str) -> _ResolvedCss:
            return _ResolvedCss(rel, self._path(rel))

        for rel in self._base:
            resolved.append(_bundled(rel))
        if self._default_tokens:
            resolved.append(_bundled(self._default_tokens))

        ext = self._external.get(theme_id)
        if ext is not None:
            resolved.append(
                _ResolvedCss(f"{ext.served_prefix}/tokens.css", ext.dir / "tokens.css")
            )
            for rel in self._components:
                resolved.append(_bundled(rel))
            for name in ext.overrides:
                resolved.append(
                    _ResolvedCss(
                        f"{ext.served_prefix}/overrides/{name}",
                        ext.dir / "overrides" / name,
                    )
                )
            return resolved

        entry = self._entry(theme_id)
        theme_tokens = entry.get("tokens")
        if theme_tokens:
            resolved.append(_bundled(str(theme_tokens)))
        for rel in self._components:
            resolved.append(_bundled(rel))
        overrides = entry.get("overrides") or {}
        if not isinstance(overrides, dict):
            raise ValueError(
                f"theme {theme_id!r} 'overrides' must be an object of id → path"
            )
        for rel in overrides.values():
            resolved.append(_bundled(str(rel)))
        return resolved

    def _path(self, rel: str) -> Path:
        path = self._themes_dir / rel
        if not path.is_file():
            raise ValueError(f"theme registry references missing file: {rel}")
        return path.resolve()

    def _validate(self) -> None:
        if not isinstance(self._base, list):
            raise ValueError("registry 'base' must be a list of paths")
        if self._default_tokens is not None and not isinstance(
            self._default_tokens, str
        ):
            raise ValueError("registry 'tokens' must be a single path string")
        if not isinstance(self._components, list):
            raise ValueError("registry 'components' must be a list of paths")

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


def register_theme(
    theme_id: str, theme_dir: str | Path, *, label: str | None = None
) -> None:
    """Register an external theme folder with the global registry.

    *theme_dir* must contain a ``tokens.css`` (and may contain a flat
    ``overrides/*.css``).  After registration, *theme_id* can be passed to
    :meth:`~pytanga.viz.Visualizer.set_theme`.
    """
    registry.register(theme_id, theme_dir, label=label)


def external_theme_dirs() -> dict[str, Path]:
    """Return ``{served_prefix: source_dir}`` for every external theme."""
    return registry.external_theme_dirs()


def theme_source_files(theme_id: str) -> list[Path]:
    """Return the theme's own source files (tokens + overrides)."""
    return registry.theme_source_files(theme_id)


def copy_theme(theme_id: str, dest_dir: str | Path, *, overwrite: bool = False) -> Path:
    """Copy a theme's ``tokens.css`` + ``overrides/`` to *dest_dir*.

    A convenience for starting a custom theme from a built-in one (e.g.
    ``copy_theme("pastel", "my_theme")``).  Edit the result, then load it with
    :func:`register_theme`.  Returns the destination directory.
    """
    src = registry.theme_dir(theme_id)
    dest = Path(dest_dir)

    def _copy(src_path: Path, dest_path: Path) -> None:
        if dest_path.exists() and not overwrite:
            raise FileExistsError(f"refusing to overwrite existing file: {dest_path}")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)

    tokens = src / "tokens.css"
    if tokens.is_file():
        _copy(tokens, dest / "tokens.css")

    overrides_dir = src / "overrides"
    if overrides_dir.is_dir():
        for p in sorted(overrides_dir.rglob("*.css")):
            _copy(p, dest / "overrides" / p.relative_to(overrides_dir))

    return dest
