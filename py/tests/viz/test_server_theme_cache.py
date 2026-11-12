# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for cache headers on runtime-registered theme assets."""

from __future__ import annotations

import asyncio
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from pytanga.viz.server import VizServer


def _write_theme(root: Path) -> Path:
    theme_dir = root / "acme"
    overrides = theme_dir / "overrides"
    overrides.mkdir(parents=True)
    (theme_dir / "tokens.css").write_text(
        ":root { --tanga-accent: #f00; }\n", encoding="utf-8"
    )
    (overrides / "button.css").write_text(
        ".tanga-action-button { color: red; }\n", encoding="utf-8"
    )
    return theme_dir


def test_registered_theme_assets_are_served_no_cache(tmp_path: Path) -> None:
    """External theme CSS is revalidated instead of served from a stale cache."""
    server = VizServer()
    server._theme_static_dirs = {"user/acme": _write_theme(tmp_path)}

    async def _fetch() -> None:
        async with TestClient(TestServer(server._build_app())) as client:
            for path in (
                "/themes/user/acme/tokens.css",
                "/themes/user/acme/overrides/button.css",
            ):
                response = await client.get(path)
                assert response.status == 200
                assert response.headers["Cache-Control"] == "no-cache"

    asyncio.run(_fetch())
