# C++ Coding Style Guide

## Overview

This guide documents the C++ coding conventions used throughout the TanGA codebase. All new C++ code must follow these rules for consistency.

The conventions are derived from the existing source code in `source/Tan.Core`, `source/Tan.Math`, `source/Tan.GA`, and `source/Tan.Crypt`.

---

## Entity Prefixes

Every named entity carries a one-letter prefix that encodes its kind. This is the single most important rule in the codebase.

| Entity | Prefix | Example |
|---|---|---|
| Class | `C` | `CBlade`, `CMatrix`, `CDynamicMultivector` |
| Struct | `S` | `SValueBlade` |
| Enum (class) | `E` | `EResult`, `EMatrixResult` |
| Type alias / typedef | `T` | `TValue`, `TBlade`, `TMap` |
| Private class template (internal helper) | `_C` | `_CMultivector`, `_CBasisE3` |
| Namespace | *(PascalCase, no prefix)* | `Tan`, `Tan::GA`, `Tan::Math` |

These prefixes are mandatory. Do not create new classes, structs, enums, or type aliases without the correct prefix.

---

## Naming Conventions

### Classes and Structs

`C`-prefixed PascalCase for classes; `S`-prefixed PascalCase for plain data structs:

```cpp
class CBlade { ... };
class CDynamicMultivector { ... };
struct SValueBlade { ... };
```

### Enums

Use `enum class` with an `E` prefix. Values use plain PascalCase (no prefix):

```cpp
enum class EResult
{
    Success = 0,
    NotInvertible,
    InvalidComponentCongruence,
};
```

### Type Aliases

`T`-prefixed PascalCase for all `using` and `typedef` declarations:

```cpp
typedef _TValue TValue;
typedef std::map<TBlade, TValue> TMap;
using TBlade  = CBlade<t_uVectorSpaceDimension, t_uVectorSpaceSignature>;
using TBladeId = uint32_t;
```

Prefer `using` over `typedef` for new code (it reads more naturally with templates).

### Functions and Methods

PascalCase, no prefix:

```cpp
void Reset();
unsigned GetId() const;
bool IsZero(const TValue& dA) const;
void AddValueBlade(const TValue& fVal, const TBlade& xBlade);
```

### Member Variables

`m_` prefix followed by a single-letter **type hint**, then lowerCamelCase:

| Type hint | Meaning | Example |
|---|---|---|
| `n` | signed integer / index / size_t | `m_nRowDimIdx`, `m_nDimension` |
| `u` | unsigned integer | `m_uBlade` |
| `d` | floating-point value | `m_dPrec` |
| `b` | bool | `m_bReady` |
| `p` | pointer | `m_pvalData` |
| `vec` | `std::vector` | `m_vecData`, `m_vecSize` |
| `map` | `std::map` | `m_mapBladeValue` |
| `it` | iterator | `m_itCurrent` |
| `str` | string | `m_strName` |

```cpp
unsigned m_uBlade;
size_t   m_nDimension;
double   m_dPrec;
TData    m_vecData;
TMap     m_mapBladeValue;
```

### Local Variables

Same type-hint prefix as member variables, but **without** `m_`:

```cpp
TIdx     nPos   = 0;
unsigned uIdx   = 0;
TIterator itEl  = m_mapBladeValue.begin();
TValue*  pData  = m_vecData.data();
```

### Static / Compile-time Constants

PascalCase, no prefix, declared as `static const` or `static constexpr`:

```cpp
static const unsigned VectorSpaceDimension = t_uVectorSpaceDimension;
static const unsigned AlgebraDimension     = (1u << t_uVectorSpaceDimension);
static const unsigned PseudoScalarId       = AlgebraDimension - 1;
```

For local static constants the `c_` prefix with type hint is acceptable:

```cpp
static const unsigned c_uAlgDim = TDynMV::AlgebraDimension;
```

### Macros

`ALL_CAPS` with underscores, prefixed with `TAN_`:

```cpp
#define TAN_ASSERT(theCond)
#define TAN_THROW_RT(theText)
#define TAN_TEST_SUM_OVERFLOW(theValA, theValB)
```

Macro parameters use `the` prefix by convention:

```cpp
#define TAN_GA_DECL_BASIS_E3(theType)
```

### Namespaces

PascalCase. Nested namespaces use separate `namespace` blocks:

```cpp
namespace Tan
{
    namespace GA
    {
        // ...
    }   // namespace Tan::GA
}       // namespace Tan
```

Always add a closing comment with the full namespace path.

---

## Template Parameters

Non-type (compile-time value) parameters use a `t_` prefix followed by the type hint and a descriptive name:

```cpp
template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
class CBlade { ... };
```

Type parameters use a leading `_T` prefix:

```cpp
template<class _TValue, typename _TBlade>
class CDynamicMultivector { ... };
```

Within the class body, rebind template parameters to `T`-prefixed type aliases immediately:

```cpp
template<class _TValue, typename _TBlade>
class CDynamicMultivector
{
public:
    typedef _TValue TValue;
    typedef _TBlade TBlade;
    // ...
};
```

---

## File Organisation

### Header vs. Implementation Split

- **Headers (`.h`)** contain class declarations and all template definitions. Template methods are defined inline in the header — do not separate them into `.cpp` files.
- **Implementation files (`.cpp`)** contain non-template definitions and explicit template instantiations.

Example `.cpp` pattern for explicit instantiation:

```cpp
#include "Array.h"
#include <cstdint>

template class Tan::CArray<int64_t>;
template class Tan::CArray<double>;
```

### File Naming

PascalCase. Use a dot separator for compound names:

```
Blade.h
DynamicMultivector.h
Matrix.Algo.GE.h
Matrix.Enum.cpp
```

### Include Guards

Use `#pragma once` — no `#ifndef` guards:

```cpp
#pragma once

#include <string>
#include "Tan.Core/Defines.h"
```

### License Header

Every file begins with the standard Apache 2.0 licence block enclosed in `<<licence: start>>` / `<<licence: end>>` markers.

---

## Class Layout

Arrange class sections in this order:

1. `public` — type aliases and `typedef`s
2. `public` — static constants
3. `protected` — member variables
4. `public` — constructors and assignment operators
5. `public` — methods and accessors
6. `protected` — internal helper methods
7. `private` — implementation details

```cpp
class CDynamicMultivector
{
public:
    typedef _TValue TValue;
    typedef _TBlade TBlade;

public:
    static const unsigned AlgebraDimension = TBlade::AlgebraDimension;

protected:
    TMap m_mapBladeValue;

public:
    CDynamicMultivector() = default;

    void Reset();
    bool AddValueBlade(const TValue& fVal, const TBlade& xBlade);

protected:
    void _Normalize();
};
```

---

## Formatting

### Brace Style — Allman

Opening braces go on their own line for every construct (classes, functions, `if`, `for`, lambdas):

```cpp
void CMatrix::SetSize(const TSizeVec& vecSize)
{
    if (vecSize.empty())
    {
        TAN_THROW_RT("Empty size vector.");
    }
    // ...
}
```

**Exception:** Trivial single-statement getters may be written on one line:

```cpp
unsigned GetId() const { return m_uBlade; }
void Reset()            { m_uBlade = 0; }
```

### Pointer and Reference Placement

Attach `*` and `&` to the **type**, not the variable name:

```cpp
TValue*       GetDataPtr();
const TValue* GetDataPtr() const;
const TValue& GetValuePrecision() const;
TMultivector& operator=(const TMultivector& wA);
```

### `const` Placement — West Const

Place `const` to the left of the type:

```cpp
const TValue& fVal          // ✅
const TValue* pData         // ✅
TValue const& fVal          // ❌
```

Method-level `const` (read-only method) is always appended after the parameter list:

```cpp
unsigned GetId() const;
bool IsZero(const TValue& dA) const;
```

### Indentation

4 spaces per level. No tabs.

---

## Comments and Documentation

### File-level and Class-level Blocks

Use a banner of `/`-slashes for visual separation:

```cpp
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// <summary>
///     Brief description of the class or function.
/// </summary>
///
/// <tparam name="t_uVectorSpaceDimension">  Dimension of the vector space. </tparam>
/// <tparam name="t_uVectorSpaceSignature">  Signature of the metric. </tparam>
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
template<unsigned t_uVectorSpaceDimension, unsigned t_uVectorSpaceSignature>
class CBlade { ... };
```

### Method-level Documentation

Use `///` triple-slash comments with XML tags before every public method:

```cpp
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// <summary>
///     Returns the number of negative-squaring base vectors in this blade.
/// </summary>
///
/// <param name="uGrade">    [out] Total grade. </param>
/// <param name="uGradeNeg"> [out] Number of negative-squaring basis vectors. </param>
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void GetGradeNeg(unsigned& uGrade, unsigned& uGradeNeg) const;
```

Supported XML tags: `<summary>`, `<param>`, `<returns>`, `<remarks>`, `<tparam>`, `<author>`.

### Inline Comments

Use `//` for short clarifications. Keep them brief:

```cpp
unsigned uCount = 0;    // accumulate set bits
```

---

## Error Handling

Use the project macros rather than raw `throw` or `assert`:

```cpp
// Runtime error — always active
TAN_THROW_RT("Container has invalid size.");

// Assertion — active in debug builds
TAN_ASSERT(nRow < GetRowCount() && nCol < GetColCount());

// Overflow guard — active in debug builds only
TAN_TEST_SUM_OVERFLOW(nA, nB);
```

Do not catch exceptions silently. Rethrow with context using `TAN_RETHROW`.

---

## Summary Checklist

- [ ] Class → `C` prefix, Struct → `S`, Enum → `E`, Type alias → `T`
- [ ] Template type params → `_T` prefix; non-type params → `t_` prefix
- [ ] Member variables → `m_` + type hint
- [ ] Local variables → type hint (no `m_`)
- [ ] Methods → PascalCase, no prefix
- [ ] Macros → `TAN_` prefix, `ALL_CAPS`
- [ ] `#pragma once` in every header
- [ ] Allman brace style (new-line opening brace)
- [ ] `*` and `&` attached to type
- [ ] West const
- [ ] `///` XML doc comments on every public method
- [ ] Closing namespace comment with full path
