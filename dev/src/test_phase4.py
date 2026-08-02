# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""End-to-end smoke test for Phase 4 build driver."""
from pathlib import Path
import tempfile
from pytanga._build import build_and_load

def main():
    with tempfile.TemporaryDirectory() as td:
        build_dir = Path(td)
        mod, so_path = build_and_load(3, 0, "float64", build_dir, verbose=True)
        print(f"Compiled extension location: {so_path}")
        print(f"Algebra dimension: {mod.ALGEBRA_DIM}")
        a = mod.DynMV()
        a.set(1, 1.0)   # e1
        b = mod.DynMV()
        b.set(1, 1.0)
        c = mod.gp(a, b)        # e1 * e1 = 1 (scalar)
        res = c.to_dict()
        print(f"gp(e1, e1) = {res}")
        assert res == {0: 1.0}, f"Unexpected result: {res}"
        print("Phase 4 smoke test PASSED")

if __name__ == "__main__":
    main()
