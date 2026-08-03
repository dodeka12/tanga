# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

cmake_minimum_required(VERSION 3.18)
project(pytanga_binding LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ---------------------------------------------------------------------------
# Required inputs (passed via -D on the cmake command line)
# ---------------------------------------------------------------------------
# BINDING_CPP     — absolute path to the generated binding source file
# TANGA_SOURCE    — absolute path to the vendored C++ sources (_ga_src/)
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
# Use the modern FindPython machinery instead of the deprecated
# FindPythonInterp / FindPythonLibs modules (suppresses CMP0148 warnings).
# ---------------------------------------------------------------------------
set(PYBIND11_FINDPYTHON ON)
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
    target_compile_options(${MODULE_NAME} PRIVATE /bigobj /O2)
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