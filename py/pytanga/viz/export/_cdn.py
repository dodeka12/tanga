# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""jsDelivr delivery helpers for the HTML export bundles."""

from __future__ import annotations

import importlib.metadata
import re
import subprocess
from typing import Literal

DeliveryMode = Literal["cdn", "inline", "offline"]

_CDN_BASE = "https://cdn.jsdelivr.net/gh/dodeka12/tanga"
_BUNDLE_PATH = "js/tanga-viewer.js"
_THEMES_REPO_PATH = "py/pytanga/viz/templates/themes"

_FINAL_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_RC_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)rc(\d+)$")


def _installed_version() -> str:
    try:
        return importlib.metadata.version("tanga-py")
    except importlib.metadata.PackageNotFoundError as exc:
        raise ValueError(
            "Cannot resolve the installed tanga-py version; pass delivery_ref "
            "explicitly (a git tag, branch, or commit hash)."
        ) from exc


def _version_to_tag(version: str) -> str:
    """Map a PEP 440 version to this repo's git tag form."""
    version = version.lstrip("v")
    if _FINAL_RE.fullmatch(version):
        return f"v{version}"
    match = _RC_RE.fullmatch(version)
    if match:
        return f"v{match.group(1)}.{match.group(2)}.{match.group(3)}-rc{match.group(4)}"
    raise ValueError(
        f"Installed tanga-py version {version!r} has no matching release tag. "
        "Pass delivery_ref explicitly (a git tag, branch, or commit hash)."
    )


def _run_git(*args: str) -> str:
    """Run a git command; return stdout or an empty string on any failure."""
    try:
        proc = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=False
        )
    except OSError:  # git not installed
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _in_tanga_repo() -> bool:
    """True when the cwd is inside a clone of the tanga repo."""
    url = _run_git("remote", "get-url", "origin")
    return "dodeka12/tanga" in url


def _git_ref() -> str | None:
    """Return the current tag or branch when running from a tanga checkout."""
    if not _in_tanga_repo():
        return None
    tag = _run_git("describe", "--tags", "--exact-match")
    if tag:
        return tag
    branch = _run_git("branch", "--show-current")
    return branch or None


def resolve_delivery_ref(override: str | None = None) -> str:
    """Return the jsDelivr ``@version`` ref to pin the viewer bundle to.

    Resolution order:

    1. *override* (a tag such as ``v1.17.0``, a branch such as
       ``feat/view-architecture``, or a commit hash).
    2. The current git tag/branch when running from a tanga checkout.
    3. The installed ``tanga-py`` version mapped to its release tag.
    4. ``"main"`` (last resort).
    """
    if override:
        return override
    git_ref = _git_ref()
    if git_ref:
        return git_ref
    try:
        return _version_to_tag(_installed_version())
    except ValueError:
        return "main"


def build_bundle_url(ref: str | None = None) -> str:
    """Return the full jsDelivr URL for the committed viewer bundle."""
    return f"{_CDN_BASE}@{resolve_delivery_ref(ref)}/{_BUNDLE_PATH}"


def build_theme_css_url(rel: str, ref: str | None = None) -> str:
    """Return the jsDelivr URL for a bundled theme CSS file.

    *rel* is a theme-relative path as returned by
    ``ThemeRegistry.theme_css_files`` (e.g. ``base.css`` or ``dark/tokens.css``).
    """
    return f"{_CDN_BASE}@{resolve_delivery_ref(ref)}/{_THEMES_REPO_PATH}/{rel}"


def build_library_script_tag(
    delivery: DeliveryMode = "cdn", delivery_ref: str | None = None
) -> str:
    """Return the ``<script type="module">`` that loads the viewer library."""
    if delivery == "cdn":
        return (
            f'<script type="module" src="{build_bundle_url(delivery_ref)}"></script>\n'
        )
    if delivery == "inline":
        from pytanga.viz.export._bootstrap import generate_library_js

        return f'<script type="module">\n{generate_library_js()}\n</script>\n'
    if delivery == "offline":
        from pytanga.viz.export._offline import offline_library_js

        return f'<script type="module">\n{offline_library_js()}\n</script>\n'
    raise ValueError(f"Unknown delivery mode: {delivery!r}")
