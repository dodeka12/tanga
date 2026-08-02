# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.codegen._build — compile a generated binding .cpp into a Python extension."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent  # …/pytanga/codegen/

# 1. Bundled source directory (exists in installed wheel)
_BUNDLED_GA_SRC = _HERE.parent / "_ga_src"  # …/pytanga/_ga_src/

# 2. Repo-relative fallback (exists when running from a git checkout)
# _HERE is …/pytanga/codegen → 3 levels up reaches the repo root
_REPO_ROOT = _HERE.parent.parent.parent
_REPO_CPP = _REPO_ROOT / "cpp"

# Resolve TANGA_SOURCE: env var → bundled → repo fallback
_tanga_source_raw = os.environ.get("PYTANGA_TANGA_SOURCE")
if _tanga_source_raw:
    TANGA_SOURCE = Path(_tanga_source_raw).resolve()
elif _BUNDLED_GA_SRC.is_dir():
    TANGA_SOURCE = _BUNDLED_GA_SRC
else:
    TANGA_SOURCE = _REPO_CPP

# CMakeLists.txt is inside the codegen package
_CMAKE_SOURCE_DIR = _HERE  # …/pytanga/codegen/ (contains CMakeLists.txt)
_PYTHON_EXE = sys.executable


def build_binding(
    binding_cpp: Path,
    build_dir: Path,
    module_name: str,
    *,
    tanga_source: Path = TANGA_SOURCE,
    verbose: bool = False,
) -> Path:
    """Configure and build a pybind11 binding.

    Parameters
    ----------
    binding_cpp  : absolute path to the generated .cpp file
    build_dir    : cmake build directory (will be created)
    module_name  : Python module name (no extension)
    tanga_source : path to <repo>/source
    verbose      : pass --verbose to cmake build step

    Returns
    -------
    Path to the compiled extension (.pyd on Windows, .so on Linux/macOS)
    """
    import pybind11

    build_dir.mkdir(parents=True, exist_ok=True)

    configure_cmd = [
        "cmake",
        "-S",
        str(_CMAKE_SOURCE_DIR),
        "-B",
        str(build_dir),
        f"-DBINDING_CPP={binding_cpp}",
        f"-DTANGA_SOURCE={tanga_source}",
        f"-DMODULE_NAME={module_name}",
        f"-Dpybind11_DIR={pybind11.get_cmake_dir()}",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_CXX_COMPILER=g++",
    ]
    if _ninja_available():
        configure_cmd += ["-G", "Ninja"]

    _run(configure_cmd, verbose=verbose)

    build_cmd = ["cmake", "--build", str(build_dir), "--config", "Release"]
    if verbose:
        build_cmd.append("--verbose")
    _run(build_cmd, verbose=verbose)

    return _find_extension(build_dir, module_name)


def build_and_load(
    dim: int,
    sig: int,
    dtype: str,
    build_dir: Path,
    *,
    tanga_source: Path = TANGA_SOURCE,
    verbose: bool = False,
):
    """Generate, compile, and import a binding for (dim, sig, dtype).

    Returns
    -------
    tuple[module, Path]
        The imported module object and the path to the compiled .so/.pyd.
    """
    import importlib.util

    from ._generator import generate
    from ._generator import module_name as mk_module_name

    mod_name = mk_module_name(dim, sig, dtype)
    cpp_path = build_dir / f"{mod_name}.cpp"

    generate(dim, sig, dtype, cpp_path)

    so_path = build_binding(
        binding_cpp=cpp_path,
        build_dir=build_dir / "cmake_build",
        module_name=mod_name,
        tanga_source=tanga_source,
        verbose=verbose,
    )

    spec = importlib.util.spec_from_file_location(mod_name, so_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, so_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], verbose: bool) -> None:
    result = subprocess.run(
        cmd,
        stdout=None if verbose else subprocess.PIPE,
        stderr=None if verbose else subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        output = result.stdout or ""
        raise RuntimeError(
            f"Command failed (exit {result.returncode}):\n  {' '.join(cmd)}\n\n{output}"
        )


def _ninja_available() -> bool:
    return (
        subprocess.run(
            ["ninja", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def _find_extension(build_dir: Path, module_name: str) -> Path:
    """Locate the compiled extension in *build_dir*."""
    suffixes = [".pyd"] if platform.system() == "Windows" else [".so"]
    for path in sorted(build_dir.rglob(f"{module_name}*")):
        if path.suffix in suffixes or ".so" in path.name:
            return path
    raise FileNotFoundError(f"Extension for {module_name!r} not found in {build_dir}")
