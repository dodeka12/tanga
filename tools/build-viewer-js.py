# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Build the committed ``js/tanga-viewer.js`` bundle (content-addressed, incremental).

The bundle is the scene-independent viewer library produced by
``generate_library_js()``.  A manifest (``js/tanga-viewer.manifest.json``)
records the ordered list of source files, each file's sha256, a hash of the
Python generator code, the combined fingerprint, and the bundle hash.  The
bundle is only regenerated when that fingerprint changes.

Usage::

    uv run python tools/build-viewer-js.py            # incremental build
    uv run python tools/build-viewer-js.py --force    # always rebuild
    uv run python tools/build-viewer-js.py --check    # exit 1 on drift (CI)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from pytanga.viz.export._bootstrap import generate_library_js, library_source_files

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BUNDLE_PATH = _REPO_ROOT / "js" / "tanga-viewer.js"
_MANIFEST_PATH = _REPO_ROOT / "js" / "tanga-viewer.manifest.json"
_BOOTSTRAP_DIR = _REPO_ROOT / "py" / "pytanga" / "viz" / "export" / "_bootstrap"
_SCHEMA = 1


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize(data: bytes) -> bytes:
    """Normalize line endings to LF.

    ``generate_library_js`` reads its sources with ``Path.read_text`` (universal
    newlines), so the bundle content is always LF regardless of the working
    tree's line endings.  Normalize here too so the manifest fingerprint matches
    the bundle on every platform (notably Windows with ``core.autocrlf``).
    """
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _bundle_content() -> bytes:
    return (generate_library_js() + "\n").encode("utf-8")


def _generator_sha256() -> str:
    """Hash the Python generator sources that shape the bundle output."""
    digest = hashlib.sha256()
    for path in sorted(_BOOTSTRAP_DIR.rglob("*.py")):
        rel = path.relative_to(_REPO_ROOT).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(_normalize(path.read_bytes()))
        digest.update(b"\x00")
    return digest.hexdigest()


def _fingerprint() -> tuple[str, str, list[dict[str, str]]]:
    """Return (fingerprint, generator_sha256, files) for the current sources."""
    generator = _generator_sha256()
    payload = [generator]
    files: list[dict[str, str]] = []
    for path in library_source_files():
        rel = path.resolve().relative_to(_REPO_ROOT).as_posix()
        file_hash = _sha256(_normalize(path.read_bytes()))
        files.append({"path": rel, "sha256": file_hash})
        payload.append(f"{rel}\x00{file_hash}")
    fingerprint = _sha256("\x00".join(payload).encode("utf-8"))
    return fingerprint, generator, files


def _load_manifest() -> dict[str, Any] | None:
    if not _MANIFEST_PATH.exists():
        return None
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def _write_manifest(
    fingerprint: str, generator: str, files: list[dict[str, str]], bundle_hash: str
) -> None:
    manifest = {
        "schema": _SCHEMA,
        "generator_sha256": generator,
        "files": files,
        "fingerprint_sha256": fingerprint,
        "bundle_sha256": bundle_hash,
    }
    _MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build(*, force: bool = False) -> None:
    """Regenerate the bundle + manifest only when inputs changed (or forced)."""
    fingerprint, generator, files = _fingerprint()
    manifest = _load_manifest()
    if not force and manifest and manifest.get("fingerprint_sha256") == fingerprint:
        print("js/tanga-viewer.js up to date")
        return

    content = _bundle_content()
    _BUNDLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _BUNDLE_PATH.write_bytes(content)
    _write_manifest(fingerprint, generator, files, _sha256(content))
    print(f"bundled js/tanga-viewer.js ({len(content)} bytes)")


def check() -> int:
    """Verify the committed bundle + manifest match the current sources."""
    content = _bundle_content()
    if not _BUNDLE_PATH.exists() or _BUNDLE_PATH.read_bytes() != content:
        print(
            "ERROR: js/tanga-viewer.js is stale; run tools/build-viewer-js.py",
            file=sys.stderr,
        )
        return 1

    manifest = _load_manifest()
    if manifest is None:
        print(
            "ERROR: js/tanga-viewer.manifest.json is missing; "
            "run tools/build-viewer-js.py",
            file=sys.stderr,
        )
        return 1

    fingerprint, _, _ = _fingerprint()
    if manifest.get("fingerprint_sha256") != fingerprint:
        print(
            "ERROR: manifest fingerprint is stale; run tools/build-viewer-js.py",
            file=sys.stderr,
        )
        return 1
    if manifest.get("bundle_sha256") != _sha256(content):
        print(
            "ERROR: manifest bundle_sha256 is stale; run tools/build-viewer-js.py",
            file=sys.stderr,
        )
        return 1

    print("js/tanga-viewer.js up to date")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="exit non-zero if the bundle drifted"
    )
    parser.add_argument(
        "--force", action="store_true", help="always regenerate the bundle"
    )
    args = parser.parse_args(argv)

    if args.check:
        return check()
    build(force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
