# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.codegen._build — compile a generated binding .cpp into a Python extension."""

from __future__ import annotations

import functools
import os
import platform
import shutil
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
        f"-DBINDING_CPP={_cmake_path(binding_cpp)}",
        f"-DTANGA_SOURCE={_cmake_path(tanga_source)}",
        f"-DMODULE_NAME={module_name}",
        f"-Dpybind11_DIR={pybind11.get_cmake_dir()}",
        "-DCMAKE_BUILD_TYPE=Release",
    ]

    compiler = os.environ.get("PYTANGA_CXX_COMPILER", _detect_default_compiler())
    configure_cmd.append(f"-DCMAKE_CXX_COMPILER={compiler}")

    gen = _resolve_generator()
    if gen:
        configure_cmd += ["-G", gen]

    run_env = None
    if (
        _SYSTEM == "Windows"
        and os.environ.get("PYTANGA_CXX_COMPILER") is None
        and shutil.which("cl.exe") is None
    ):
        msvc_env = _msvc_environment()
        if msvc_env:
            run_env = {**os.environ, **msvc_env}

    _run(configure_cmd, verbose=verbose, env=run_env)

    build_cmd = ["cmake", "--build", str(build_dir), "--config", "Release"]
    if verbose:
        build_cmd.append("--verbose")
    _run(build_cmd, verbose=verbose, env=run_env)

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

# Per-platform mappings
_SYSTEM = platform.system()

_EXT_MAP: dict[str, list[str]] = {
    "Windows": [".pyd"],
    "Darwin": [".so", ".dylib"],
    "Linux": [".so"],
}

_DEFAULT_COMPILER: dict[str, str] = {
    "Windows": "cl.exe",
    "Darwin": "clang++",
    "Linux": "g++",
}


def _cmake_path(p: Path) -> str:
    """Convert a Path to a CMake-safe string (forward slashes, no escape issues)."""
    return p.as_posix()


def _detect_default_compiler() -> str:
    """Return the default C++ compiler for the current platform."""
    return _DEFAULT_COMPILER.get(_SYSTEM, "g++")


def _locate_vcvars64() -> str | None:
    """Locate MSVC's ``vcvars64.bat`` on Windows, or return ``None``.

    Uses ``vswhere.exe`` (the Visual Studio Installer query tool) to find the
    latest MSVC installation that provides the x64 native tools, then resolves
    the toolchain environment batch file.
    """
    if _SYSTEM != "Windows":
        return None

    vswhere: str | None = None
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if program_files_x86:
        candidate = (
            Path(program_files_x86)
            / "Microsoft Visual Studio"
            / "Installer"
            / "vswhere.exe"
        )
        if candidate.is_file():
            vswhere = str(candidate)
    if vswhere is None:
        vswhere = shutil.which("vswhere")
    if not vswhere:
        return None

    try:
        result = subprocess.run(
            [
                vswhere,
                "-latest",
                "-products",
                "*",
                "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property",
                "installationPath",
            ],
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    install_path = result.stdout.strip()
    if not install_path:
        return None

    vcvars = Path(install_path) / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    return str(vcvars) if vcvars.is_file() else None


@functools.lru_cache(maxsize=1)
def _msvc_environment() -> dict[str, str]:
    """Capture the full MSVC toolchain environment (cached once per process).

    Runs ``vcvars64.bat`` in a sub-shell and parses the resulting ``set``
    output into a dict. Returns ``{}`` if MSVC cannot be located or the
    environment cannot be captured.
    """
    vcvars = _locate_vcvars64()
    if not vcvars:
        return {}

    try:
        result = subprocess.run(
            f'call "{vcvars}" >nul && set',
            shell=True,
            capture_output=True,
            text=True,
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return {}

    if result.returncode != 0:
        return {}

    env: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            env[key] = value
    return env


def _resolve_generator() -> str | None:
    """Return an explicit CMake generator if one should be used, else None.

    Precedence:
    1. ``PYTANGA_CMAKE_GENERATOR`` env var (explicit override).
    2. ``"Ninja"`` if ninja is available on any platform.
    3. Otherwise → ``None`` (let CMake auto-detect).
    """
    gen = os.environ.get("PYTANGA_CMAKE_GENERATOR")
    if gen:
        return gen
    if _ninja_available():
        return "Ninja"
    return None


def _run(
    cmd: list[str],
    verbose: bool,
    env: dict[str, str] | None = None,
) -> None:
    result = subprocess.run(
        cmd,
        stdout=None if verbose else subprocess.PIPE,
        stderr=None if verbose else subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.returncode != 0:
        output = result.stdout or ""
        raise RuntimeError(
            f"Command failed (exit {result.returncode}):\n  {' '.join(cmd)}\n\n{output}"
        )


def _ninja_available() -> bool:
    try:
        result = subprocess.run(
            ["ninja", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, OSError):
        return False
    return result.returncode == 0


def _find_extension(build_dir: Path, module_name: str) -> Path:
    """Locate the compiled extension in *build_dir*."""
    suffixes = _EXT_MAP.get(_SYSTEM, [".so"])
    for path in sorted(build_dir.rglob(f"{module_name}*")):
        if path.suffix in suffixes:
            return path
    raise FileNotFoundError(f"Extension for {module_name!r} not found in {build_dir}")
