# Phase 2 — Binding CMake Infrastructure

**Overview plan:** [plan.md](plan.md)  
**Depends on:** Phase 0 (directory structure)  
**Required by:** Phase 4 (build driver calls cmake with this file)

---

## Goal

Write `pytanga/cmake/binding/CMakeLists.txt` — the CMake script that compiles
one generated binding `.cpp` into a Python extension module (`.pyd` on Windows,
`.so` on Linux/macOS).

Each binding is a **self-contained compilation unit**: the three tanga `.cpp`
files that contain explicit template specializations are compiled directly into
the binding, so no pre-built tanga shared library is needed.

---

## Background: what the binding needs at link time

`Tan.GA` is 100% header-only templates — no linking required.

Three tanga `.cpp` files contain non-template definitions that the compiler
cannot generate from headers alone:

| File | Symbols provided |
|---|---|
| `Tan.Math/ValuePrecision.cpp` | `CValuePrecision<T>::DefaultPrecision()` for float, double, int, int32_t, uint32_t, uint64_t, int64_t |
| `Tan.Core/ValueFormatString.cpp` | `ValueFormatString<T>()` for int, uint, float, double, int64_t, uint64_t — pulled in transitively via `Matrix.h` → `Matrix.Operators.h` |
| `Tan.Math/Matrix.Enum.cpp` | `Tan::ToString(EMatrixResult)` |

These three files are compiled **together with the generated binding `.cpp`**
in a single `pybind11_add_module` target.

`Array.cpp` and `Matrix.cpp` contain only explicit template instantiations
(e.g. `template class CMatrix<double>`). These are not needed because the
binding's own translation unit will instantiate the templates it requires.

---

## Steps

### 2.1 Write `pytanga/cmake/binding/CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.18)
project(pytanga_binding LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ---------------------------------------------------------------------------
# Required inputs (passed via -D on the cmake command line)
# ---------------------------------------------------------------------------
# BINDING_CPP     — absolute path to the generated binding source file
# TANGA_SOURCE    — absolute path to <repo>/source
# MODULE_NAME     — Python module name (no extension), e.g. binding_dim3_sig0_f64
# ---------------------------------------------------------------------------

if(NOT DEFINED BINDING_CPP)
    message(FATAL_ERROR "BINDING_CPP must be set")
endif()
if(NOT DEFINED TANGA_SOURCE)
    message(FATAL_ERROR "TANGA_SOURCE must be set")
endif()
if(NOT DEFINED MODULE_NAME)
    message(FATAL_ERROR "MODULE_NAME must be set")
endif()

# ---------------------------------------------------------------------------
# pybind11
# ---------------------------------------------------------------------------
find_package(pybind11 CONFIG REQUIRED)

# ---------------------------------------------------------------------------
# The three tanga .cpp files that must be compiled alongside the binding
# ---------------------------------------------------------------------------
set(TANGA_IMPL_SRCS
    "${TANGA_SOURCE}/Tan.Math/ValuePrecision.cpp"
    "${TANGA_SOURCE}/Tan.Core/ValueFormatString.cpp"
    "${TANGA_SOURCE}/Tan.Math/Matrix.Enum.cpp"
)

# ---------------------------------------------------------------------------
# Extension module
# ---------------------------------------------------------------------------
pybind11_add_module(${MODULE_NAME} MODULE
    "${BINDING_CPP}"
    ${TANGA_IMPL_SRCS}
)

target_include_directories(${MODULE_NAME} PRIVATE "${TANGA_SOURCE}")

# ---------------------------------------------------------------------------
# Compiler flags — mirror the existing tanga CMakeLists.txt
# ---------------------------------------------------------------------------
if(MSVC)
    target_compile_options(${MODULE_NAME} PRIVATE /arch:SSE4.1 /O2)
else()
    target_compile_options(${MODULE_NAME} PRIVATE -msse4.1 -mpopcnt -O3)
endif()

# ---------------------------------------------------------------------------
# Output goes to the build directory root so the build driver can find it
# ---------------------------------------------------------------------------
set_target_properties(${MODULE_NAME} PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"   # Windows .dll/.pyd
)
```

### 2.2 Verify pybind11 discovery

The `find_package(pybind11 CONFIG REQUIRED)` call needs pybind11 to be
findable. The build driver (Phase 4) will pass its location via
`-Dpybind11_DIR=<path>`. To get this path from Python:

```python
import pybind11
pybind11_cmake_dir = pybind11.get_cmake_dir()
```

The build driver will append `-Dpybind11_DIR=<pybind11_cmake_dir>` to the
cmake configure command.

### 2.3 Confirm the three required source files exist

Before writing Phase 4, manually verify all three paths resolve:

```powershell
$src = "C:\Users\chris\Documents\code\github\tanga\source"
Test-Path "$src\Tan.Math\ValuePrecision.cpp"   # must be True
Test-Path "$src\Tan.Core\ValueFormatString.cpp" # must be True
Test-Path "$src\Tan.Math\Matrix.Enum.cpp"       # must be True
```

### 2.4 Manual smoke test (optional but recommended)

Write a minimal hand-crafted binding for `G(3,0)` with `double` values,
compile it with this CMakeLists, and confirm Python can import it. Use a
throwaway directory:

```powershell
cmake -S pytanga/cmake/binding -B /tmp/test_bind `
  -DBINDING_CPP=/tmp/test_bind.cpp `
  -DTANGA_SOURCE=$src `
  -DMODULE_NAME=test_bind_dim3_sig0_f64 `
  -Dpybind11_DIR=$(python -c "import pybind11; print(pybind11.get_cmake_dir())")
cmake --build /tmp/test_bind --config Release
```

Import the resulting `.pyd`/`.so` in Python and call a basic function.

---

## Completion check

- [ ] `pytanga/cmake/binding/CMakeLists.txt` exists and is syntactically valid
  (`cmake -S . -B /tmp/x` with required vars reports no errors beyond missing
  source file)
- [ ] A manually crafted minimal binding compiles successfully
- [ ] The three tanga impl `.cpp` files are confirmed present at their expected
  paths relative to `TANGA_SOURCE`
