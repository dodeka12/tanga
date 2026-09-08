# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Export-time download + bundling for ``delivery="offline"``.

Downloads pinned third-party assets (three.js, marked, KaTeX + fonts,
html2canvas) into a user cache, then bundles three.js + the Tanga library with
esbuild so the result can be inlined into a fully self-contained HTML file.
Requires Node.js and esbuild; raises :class:`OfflineToolchainError` otherwise.
"""

from __future__ import annotations

import base64
import functools
import hashlib
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from pytanga.viz.export._bootstrap import generate_library_js

THREE_VERSION = "0.170.0"
MARKED_VERSION = "15.0.0"
KATEX_VERSION = "0.16.11"
HTML2CANVAS_VERSION = "1.4.1"

_CDN = "https://cdn.jsdelivr.net/npm"

_VERSION_HASH = hashlib.sha256(
    f"{THREE_VERSION}|{MARKED_VERSION}|{KATEX_VERSION}|{HTML2CANVAS_VERSION}".encode()
).hexdigest()[:16]

_FONT_FACE_RE = re.compile(r"@font-face\{[^}]*\}")
_SRC_RE = re.compile(r"src:([^;}]+)")


class OfflineToolchainError(RuntimeError):
    """Raised when Node.js or esbuild is unavailable for offline export."""


@dataclass
class OfflineAssets:
    library_js: Path
    marked_js: Path
    katex_js: Path
    auto_render_js: Path
    katex_css: Path
    html2canvas_js: Path


def _cache_root() -> Path:
    root = os.environ.get("TANGA_CACHE_DIR")
    if root:
        return Path(root).expanduser() / "offline"
    return Path.home() / ".cache" / "tanga" / "offline"


def _cache_dir() -> Path:
    return _cache_root() / _VERSION_HASH


def find_node() -> str:
    """Return the node executable path, or raise :class:`OfflineToolchainError`."""
    node = shutil.which("node")
    if node is None:
        raise OfflineToolchainError(
            "delivery='offline' requires Node.js; install it and retry."
        )
    return node


def find_esbuild() -> str:
    """Return the esbuild executable path, or raise :class:`OfflineToolchainError`."""
    env = os.environ.get("TANGA_ESBUILD")
    if env and Path(env).exists():
        return env

    # Dev checkout: esbuild installed under dev/node_modules.
    repo_dev = (
        Path(__file__).resolve().parents[4]
        / "dev"
        / "node_modules"
        / "esbuild"
        / "bin"
        / "esbuild"
    )
    if repo_dev.exists():
        return str(repo_dev)

    for name in ("esbuild", "esbuild.cmd"):
        found = shutil.which(name)
        if found:
            return found

    raise OfflineToolchainError(
        "delivery='offline' requires esbuild; install it with "
        "`npm install -g esbuild` (or set TANGA_ESBUILD)."
    )


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "tanga-offline"})
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)


def _download_three(work: Path) -> Path:
    """Download + extract the three npm tarball into ``work/three``."""
    three_dir = work / "three"
    if (three_dir / "build" / "three.module.js").exists() and (
        three_dir / "examples" / "jsm" / "controls" / "OrbitControls.js"
    ).exists():
        return three_dir
    url = f"https://registry.npmjs.org/three/-/three-{THREE_VERSION}.tgz"
    tgz = work / "three.tgz"
    _download(url, tgz)
    with tarfile.open(tgz, "r:gz") as tf:
        members = [
            m
            for m in tf.getmembers()
            if m.name.startswith("package/build/three.module.js")
            or m.name.startswith("package/examples/jsm/")
        ]
        with tempfile.TemporaryDirectory() as td:
            tf.extractall(td, members=members, filter="data")
            src = Path(td) / "package"
            (three_dir / "build").mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                src / "build" / "three.module.js",
                three_dir / "build" / "three.module.js",
            )
            if (three_dir / "examples" / "jsm").exists():
                shutil.rmtree(three_dir / "examples" / "jsm")
            shutil.copytree(src / "examples" / "jsm", three_dir / "examples" / "jsm")
    tgz.unlink(missing_ok=True)
    return three_dir


def _build_offline_bundle(work: Path, three_dir: Path) -> Path:
    """Bundle three.js + the Tanga library into ``work/tanga-viewer.offline.js``."""
    del three_dir  # resolved relative to the entry in ``work``
    out = work / "tanga-viewer.offline.js"
    entry = work / "tanga-offline-entry.js"
    lib = generate_library_js().replace("'three/addons/", "'./three/examples/jsm/")

    entry_hash = hashlib.sha256(lib.encode("utf-8")).hexdigest()
    sidecar = work / "tanga-viewer.offline.js.sha256"
    if out.exists() and sidecar.exists() and sidecar.read_text() == entry_hash:
        return out

    entry.write_text(lib, encoding="utf-8")
    cmd = [
        find_node(),
        find_esbuild(),
        "--bundle",
        "--format=esm",
        "--alias:three=./three/build/three.module.js",
        str(entry),
        f"--outfile={out}",
        "--log-level=warning",
    ]
    subprocess.run(cmd, cwd=work, check=True)
    entry.unlink(missing_ok=True)
    sidecar.write_text(entry_hash, encoding="utf-8")
    return out


def _download_leaf_assets(work: Path) -> tuple[Path, Path, Path, Path]:
    marked = work / "marked.min.js"
    katex_js = work / "katex.min.js"
    auto_render = work / "auto-render.min.js"
    html2canvas = work / "html2canvas.min.js"
    if not marked.exists():
        _download(f"{_CDN}/marked@{MARKED_VERSION}/marked.min.js", marked)
    if not katex_js.exists():
        _download(f"{_CDN}/katex@{KATEX_VERSION}/dist/katex.min.js", katex_js)
    if not auto_render.exists():
        _download(
            f"{_CDN}/katex@{KATEX_VERSION}/dist/contrib/auto-render.min.js",
            auto_render,
        )
    if not html2canvas.exists():
        _download(
            f"{_CDN}/html2canvas@{HTML2CANVAS_VERSION}/dist/html2canvas.min.js",
            html2canvas,
        )
    if not (work / "katex.min.css").exists():
        _download(
            f"{_CDN}/katex@{KATEX_VERSION}/dist/katex.min.css",
            work / "katex.min.css",
        )
    return marked, katex_js, auto_render, html2canvas


def _build_katex_offline_css(work: Path) -> Path:
    """Download KaTeX woff2 fonts and build ``katex.offline.css`` (base64)."""
    fonts_dir = work / "fonts"
    css = (work / "katex.min.css").read_text(encoding="utf-8")
    names = sorted(set(re.findall(r"url\(fonts/([^)]*\.woff2)\)", css)))
    fonts_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        if not (fonts_dir / name).exists():
            _download(
                f"{_CDN}/katex@{KATEX_VERSION}/dist/fonts/{name}",
                fonts_dir / name,
            )

    def _replace_block(match: re.Match[str]) -> str:
        block = match.group(0)
        src_match = _SRC_RE.search(block)
        if not src_match:
            return block
        woff2 = re.search(r"url\(fonts/([^)]*\.woff2)\)", src_match.group(1))
        if not woff2:
            return block
        name = woff2.group(1)
        b64 = base64.b64encode((fonts_dir / name).read_bytes()).decode("ascii")
        new_src = f'src:url(data:font/woff2;base64,{b64}) format("woff2")'
        return block[: src_match.start()] + new_src + block[src_match.end() :]

    offline = _FONT_FACE_RE.sub(_replace_block, css)
    out = work / "katex.offline.css"
    out.write_text(offline, encoding="utf-8")
    return out


@functools.lru_cache(maxsize=1)
def _build_assets() -> OfflineAssets:
    find_node()
    find_esbuild()
    work = _cache_dir()
    work.mkdir(parents=True, exist_ok=True)
    _download_three(work)
    library = _build_offline_bundle(work, work / "three")
    marked, katex_js, auto_render, html2canvas = _download_leaf_assets(work)
    katex_css = _build_katex_offline_css(work)
    return OfflineAssets(library, marked, katex_js, auto_render, katex_css, html2canvas)


def ensure_offline_assets() -> OfflineAssets:
    """Download + build the offline assets (cached per process)."""
    return _build_assets()


def offline_library_js() -> str:
    """Return the self-contained (three + Tanga) library source."""
    return ensure_offline_assets().library_js.read_text(encoding="utf-8")


def offline_third_party_html() -> str:
    """Return marked + KaTeX + html2canvas as inlined ``<script>`` tags."""
    a = ensure_offline_assets()
    parts = []
    for path in (a.marked_js, a.katex_js, a.auto_render_js, a.html2canvas_js):
        parts.append("<script>\n" + path.read_text(encoding="utf-8") + "\n</script>\n")
    return "".join(parts)


def offline_katex_css() -> str:
    """Return the offline KaTeX CSS as an inlined ``<style>`` block."""
    css = ensure_offline_assets().katex_css.read_text(encoding="utf-8")
    return "<style>\n" + css + "\n</style>\n"
