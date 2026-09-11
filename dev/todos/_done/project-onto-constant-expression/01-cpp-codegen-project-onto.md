# Phase 1 — C++ `ProjectOnto` + codegen bindings (additive)

## Goal

Add the correctly-directed C++ `ProjectOnto` (MV and `CBladeMask` overloads)
and expose them through codegen as `_mod.project_onto` / `_mod.project_onto_mask`.
Keep the existing `ProjectTo`/`project_to` in place for now so the suite stays
green; they are removed in Phase 2.

## Files

- Edit: `cpp/Tan.GA/MV_Operators.h`
- Edit: `cpp/Tan.GA/_CompileTest_Ops.cpp`
- Edit: `py/pytanga/codegen/_mv_operators.py`
- Edit: `py/pytanga/codegen/_generator.py`
- Edit: `py/pytanga/_template.cpp`

## Steps

- [x] **1.1 — Add C++ `ProjectOnto` overloads**
  - In `cpp/Tan.GA/MV_Operators.h`, add (next to `ProjectTo`, without removing
    it yet):
    ```cpp
    template <typename TMultivectorA, typename TMultivectorB>
    void ProjectOnto(TMultivectorA &wA, const TMultivectorB &wB)
    {
        typedef typename TMultivectorA::TValue TValue;
        typedef typename TMultivectorA::TBlade TBlade;
        wA.ForEachBlade([&](TValue &fValA, const TBlade &blA)
        {
            typename TMultivectorB::TValue fValB;
            if (!wB.GetValueBlade(fValB, blA))
                fValA = TValue(0);
        });
    }

    template <typename TMultivectorA>
    void ProjectOnto(TMultivectorA &wA,
                     const GA::CBladeMask<typename TMultivectorA::TBlade> &xMask)
    {
        typedef typename TMultivectorA::TValue TValue;
        typedef typename TMultivectorA::TBlade TBlade;
        wA.ForEachBlade([&](TValue &fValA, const TBlade &blA)
        {
            if (!xMask.Contains(blA))
                fValA = TValue(0);
        });
    }
    ```
  - `Prune()` is applied by the pybind binding (see 1.3), not inside the
    template.

- [x] **1.2 — Add compile-test instantiations**
  - In `cpp/Tan.GA/_CompileTest_Ops.cpp`, add explicit instantiations for the
    two new overloads (mirroring the existing `ProjectTo`/`ProjectToBlade`
    lines), e.g.:
    ```cpp
    template void GA::ProjectOnto(TMultivector &wA, const TMultivector &wB);
    template void GA::ProjectOnto(TMultivector &wA, const GA::CBladeMask<TMultivector::TBlade> &xMask);
    ```
  - Match the exact `TMultivector`/`TBlade` names already used in that file.

- [x] **1.3 — Add codegen binding fragments**
  - In `py/pytanga/codegen/_mv_operators.py`, add:
    - `project_onto_def()` — `m.def("project_onto", ...)` wrapping
      `Tan::GA::ProjectOnto(c, b); c.Prune();` for the MV case.
    - `project_onto_mask_def()` — `m.def("project_onto_mask", [](a, ids){...})`
      accepting `std::vector<unsigned>`, building a
      `GA::CBladeMask<TDynMV::TBlade>` from the ids (`xMask << TBlade(id)`),
      calling `Tan::GA::ProjectOnto(c, xMask)`, then `c.Prune()`.

- [x] **1.4 — Wire generator + template**
  - In `py/pytanga/codegen/_generator.py`, import `project_onto_def` and
    `project_onto_mask_def`, and add
    `template = sub_bare(template, "PROJECT_ONTO_DEF", project_onto_def())` and
    `template = sub_bare(template, "PROJECT_ONTO_MASK_DEF", project_onto_mask_def())`.
  - In `py/pytanga/_template.cpp`, add two `{ { PROJECT_ONTO_DEF } }` and
    `{ { PROJECT_ONTO_MASK_DEF } }` blocks next to the existing `PROJECT_TO_DEF`
    block (leave `PROJECT_TO_DEF` for now).

## Validation

```powershell
uv run python -c "from pytanga import Algebra; m = Algebra(dim=3, sig=0, dtype='float64', verbose=True)._mod; assert hasattr(m, 'project_onto') and hasattr(m, 'project_onto_mask') and hasattr(m, 'project_to'); print('ok')"
```

(First run JIT-compiles the binding because the cache key covers the changed
`.h`/template/codegen files.)

## Notes

- The cache key in `py/pytanga/codegen/_cache.py::_make_key` already hashes all
  `Tan.GA` headers, `_template.cpp`, and the codegen files, so touching them
  forces a rebuild — no manual `clear()` needed in normal use.
- Keep `ProjectTo`/`project_to` untouched this phase; Phase 2 removes them
  together with the Python wrappers so the suite stays green.
