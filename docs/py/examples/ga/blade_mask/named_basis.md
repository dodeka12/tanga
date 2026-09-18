# BladeMask named bases (auto display basis, composed names, with_basis)

**Keywords:** BladeMask · basis · N3 · conformal · twist · with_basis

Shows that a BladeMask carries both raw blade ids and an optional named basis:
the N3 display basis is auto-attached on construction, composed names like
`einf` expand to raw ids in string parsing, and `with_basis` attaches a
reduced physical-DOF basis (e.g. the 6 twist directions over 9 raw blades).

## Run

```bash
uv run python py/examples/ga/blade_mask/named_basis.py
```

## Source

[`ga/blade_mask/named_basis.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/blade_mask/named_basis.py)

## Code

````python
#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""named_basis.py — BladeMask named bases (auto display basis, composed names, with_basis).

Shows that a BladeMask carries both raw blade ids and an optional named basis:
the N3 display basis is auto-attached on construction, composed names like
``einf`` expand to raw ids in string parsing, and ``with_basis`` attaches a
reduced physical-DOF basis (e.g. the 6 twist directions over 9 raw blades).

Run with:  uv run python py/examples/ga/blade_mask/named_basis.py

Keywords: BladeMask, basis, N3, conformal, twist, with_basis
"""

from pytanga import BladeMask
from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, TwistBivector


def main() -> None:
    alg = BasisN3()

    grade1 = BladeMask(alg, grades=[1])
    print("grade-1 ids:  ", grade1.ids)
    print("grade-1 basis:", grade1.basis_names)

    composed = BladeMask(alg, "e1 + einf")
    print("\nBladeMask(N3, 'e1 + einf') ids:", composed.ids)

    geo = Geometry(alg)
    twist = geo.mask_for(TwistBivector)
    print("\nTwistBivector ids:  ", twist.ids)
    print("TwistBivector basis:", twist.basis_names)
    print("basis_matrix shape: ", twist.basis_matrix().shape)


if __name__ == "__main__":
    main()
````
