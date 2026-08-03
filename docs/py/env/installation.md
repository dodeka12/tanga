# Environment & Installation

This guide covers setting up a pytanga development environment and using
pytanga as a dependency in your own project.

## Prerequisites

- **Python ≥ 3.12**
- **uv** (Python package manager and virtual‑environment tool)
- **C++ compiler** — only needed when pytanga must compile its C++ binding
  from source (i.e. when no pre-compiled wheel exists for your platform or
  you use a custom algebra).  See [Compiler Setup](#compiler-setup) below
  for per-platform installation instructions.


## Compiler Setup

pytanga compiles its C++ binding on-demand using CMake and a C++17 compiler.
The `[compile]` extra (`pip install "tanga-py[compile]"`) pulls in `cmake`,
`ninja`, and `pybind11` via pip — but **you must provide the C++ compiler**
separately.

Choose your platform below.

### Linux

Install GCC (recommended) or Clang via your package manager:

```bash
# Ubuntu / Debian
sudo apt install build-essential g++-13

# Fedora
sudo dnf install gcc-c++

# Arch
sudo pacman -S gcc
```

Verify:

```bash
g++ --version   # should show ≥ 13.x
```

Alternatively, install Clang:

```bash
# Ubuntu / Debian
sudo apt install clang-14

# Fedora
sudo dnf install clang
```

### macOS

Install the Xcode Command Line Tools (provides `clang++`):

```bash
xcode-select --install
```

Or install GCC via Homebrew:

```bash
brew install gcc
```

Verify:

```bash
clang++ --version   # should show ≥ 14.x
```

### Windows

You need the **Microsoft Visual C++ (MSVC)** toolchain.  There are three
options:

#### Option A: Visual Studio Build Tools (recommended)

1. Download the **Build Tools for Visual Studio 2022** from
   [visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
2. Run the installer and select the **"Desktop development with C++"** workload.
3. After installation, open the **"Developer Command Prompt for VS 2022"**
   from the Start Menu and run all `pip` / `uv` commands from that terminal.

#### Option B: Full Visual Studio 2022 Community Edition

1. Download **Visual Studio 2022 Community** (free) from
   [visualstudio.microsoft.com/vs/community/](https://visualstudio.microsoft.com/vs/community/)
2. During installation, select the **"Desktop development with C++"** workload.
3. Use the **"Developer Command Prompt for VS 2022"** or launch VS Code from
   the Developer Command Prompt (`code .`).

#### Option C: VS Code with C++ Extension

1. Install the **C/C++** extension (`ms-vscode.cpptools`) in VS Code.
2. Install the Build Tools from Option A.
3. Open your project folder; VS Code should detect MSVC automatically.

Verify (from the Developer Command Prompt):

```cmd
cl   :: should print the Microsoft C/C++ compiler version
```

> **Important:** CMake on Windows must be run from a terminal that has MSVC in
> its `PATH`.  The "Developer Command Prompt" configures this automatically.
> Without it, `cmake` will report `No CMAKE_CXX_COMPILER could be found`.

### Alternative: WSL (Windows Subsystem for Linux)

If you prefer a Linux toolchain on Windows, install WSL and a Linux distribution
(Ubuntu recommended), then follow the Linux instructions above inside the WSL
terminal.

```powershell
# From an Administrator PowerShell:
wsl --install -d Ubuntu
```

After installation, open the Ubuntu terminal and follow the [Linux](#linux)
instructions.


## Development Setup

Clone the repository and sync the `dev` dependency group:

```bash
git clone https://github.com/dodeka12/tanga.git
cd tanga

# Create .venv and install all dev tooling
uv sync --group dev
```

### What `--group dev` installs

The `dev` group (defined in `pyproject.toml` under `[dependency-groups]`)
pulls in:

| Package | Purpose |
|---------|---------|
| `pytest>=9.1.1` | Test runner |
| `ruff>=0.14.0`  | Linter and formatter |
| `tanga-py[compile,examples]` | The pytanga package itself plus its `compile` and `examples` extras |

The extras in turn provide:

| Extra | Packages | Needed for |
|-------|----------|------------|
| `compile` | `pybind11`, `cmake`, `ninja` | Compiling the C++ binding from source |
| `examples` | `scipy`, `ipykernel`, `jupyter`, `ipython` | Running iterative solvers and jupyter notebooks in example scripts under `py/examples/` |

After syncing you can run tests, lint, and execute example scripts:

```bash
uv run pytest
uv run ruff check py/
uv run python py/examples/solver_rotor_estimation.py
```

## Using pytanga as a Dependency

### Pre-Compiled Wheels (recommended)

If a pre-compiled wheel exists for your platform, simply:

```bash
pip install tanga-py
```

No C++ compiler or build tools are needed. pytanga ships precompiled
bindings for the five most common algebra configurations:

| Algebra | dim | sig | dtype |
|---------|-----|-----|-------|
| E3 (Euclidean) | 3 | 0 | float64 |
| P3 / PGA3 (Projective) | 4 | 8 | float64 |
| N3 (Conformal) | 5 | 16 | float64 |
| E3 modular (crypto) | 3 | 0 | int64 |
| Sparse high-dim (crypto) | 10 | 0 | int64 |

### Source Compilation (all platforms)

If no pre-compiled wheel is available for your platform, or if you need
an algebra not covered by the precompiled set, add the `compile` extra:

```bash
pip install "tanga-py[compile]"
```

This pulls in cmake, ninja, and pybind11 for on-the-fly compilation.
You also need a C++ compiler — see [Compiler Setup](#compiler-setup).

For the example scripts and iterative solvers, add the `examples` extra as
well:

```bash
pip install "tanga-py[compile,examples]"
```

### With uv

In your own project, add pytanga with uv:

```bash
uv add tanga-py
uv add "tanga-py[compile]"
uv add "tanga-py[compile,examples]"
```

### Virtual environment

The uv commands above automatically create and manage a `.venv/` for your
project.  There is nothing else to set up — uv handles the Python
interpreter, package installation, and environment activation transparently
via `uv run`.
