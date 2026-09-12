# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Backward-compatible re-export of 3D quadric-space (Q3) analysis.

The Q3 analysis logic lives in :mod:`pytanga.quadric._analysis`; this module
keeps the ``geometry`` import path working for the analysis dispatcher.
"""

from pytanga.quadric._analysis import analyze_entity, analyze_operator, analyze_rotor

__all__ = ["analyze_entity", "analyze_operator", "analyze_rotor"]
