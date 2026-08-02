# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Code generation and binding compilation for TANGA geometric algebra."""

from ._cache import cache_root, clear, get_or_build, invalidate, lookup, precompile
from ._generator import module_name

__all__ = [
    "cache_root",
    "clear",
    "get_or_build",
    "invalidate",
    "lookup",
    "module_name",
    "precompile",
]
