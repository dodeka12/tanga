# Coding Style Guide

## Overview

This document defines the coding standards for the Micro-Otter project. Consistency in code style improves readability, maintainability, and reduces cognitive load when reviewing or modifying code.

---

## Python

### Style Standard

Follow **[PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)** for all Python code.

**Key PEP 8 Guidelines:**

- **Indentation**: 4 spaces per level (no tabs)
- **Line Length**: Maximum 100 characters (configured in `pyproject.toml`)
- **Imports**: Grouped in order: standard library, third-party, local application
- **Naming Conventions**:
  - `snake_case` for functions, methods, variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
  - Single leading underscore `_name` for non-public methods/attributes

### Critical Rule: Respect Encapsulation

**⚠️ NEVER access private members of other classes.**

```python
# ❌ WRONG - Accessing private members
class ViewManager:
    def __init__(self):
        self._modal_layer = document.createElement('div')

# In another class:
manager._modal_layer.appendChild(dialog)  # WRONG!

# ✅ CORRECT - Use public API
manager.showModal(dialog)  # Correct!
```

**Rationale:**
- Private members (prefixed with `_`) are implementation details
- Direct access breaks encapsulation and makes refactoring brittle
- Public methods provide stable contracts between components

**Enforcement:**
- Code reviews must reject direct access to `_private` members from external classes
- If you need access to internal state, propose a public method or property

---

## TypeScript

### Style Standard

Follow modern TypeScript conventions with consistency across the codebase:

- **Indentation**: 4 spaces per level (no tabs)
- **Line Length**: Maximum 100 characters (enforced by Prettier)
- **Semicolons**: Optional (project uses semicolons for consistency)
- **Quotes**: Single quotes `'string'` for strings (enforced by Prettier)
- **Naming Conventions**:
  - `camelCase` for functions, methods, variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
    - Private fields: `#fieldName` (private class fields)
    - Private methods: `_methodName()` or `#methodName()`

### Critical Rule: Respect Encapsulation

**⚠️ NEVER access private members of other classes.**

```ts
// ❌ WRONG - Accessing private members
class ViewManager {
    constructor() {
        this._modalLayer = document.createElement('div');
    }
}

// In another class:
viewManager._modalLayer.appendChild(dialog);  // WRONG!

// ✅ CORRECT - Use public API
viewManager.showModal(dialog);  // Correct!
```

**Why This Matters:**

- **Private fields** (`#field`) are truly private and inaccessible outside the class
- **Underscore-prefixed members** (`_field`) are conventionally private:
  - Not part of the public API
  - May change without notice
  - Accessing them breaks encapsulation

**Examples of Private vs Public:**

```ts
class Workspace {
    #completedSources = new Set();  // Truly private (ES private field)
    _progressListener = null;       // Conventionally private
    splashScreen = null;            // Public property

    constructor() { }

    // ✅ Public method - OK to call from other classes
    load() {
        return this._loadInternal();
    }

    // ❌ Private method - DO NOT call from other classes
    _loadInternal() {
        // Implementation details
    }

    // ✅ Public method for accessing derived state
    isLoadComplete() {
        return this.#completedSources.size === 5;
    }
}

// From another class:
workspace.load();              // ✅ Correct - public API
workspace.isLoadComplete();    // ✅ Correct - public API
workspace._loadInternal();     // ❌ WRONG - private method
workspace._progressListener;   // ❌ WRONG - private property
```

**Enforcement:**
- Code reviews must reject direct access to `_private` or `#private` members from external classes
- If you need access to internal state, propose a public method or getter

### Internal Event Contract Pattern (v2)

For internal app-domain emitters, use the shared `AppEventEmitter` contract consistently:

- Use canonical APIs: `emit(eventName, payload)`, `on(eventName, listener)`, `off(eventName, listener)`, `once(eventName, listener)`
- Use wildcard listeners only when intentionally subscribing to all events: `on('*', listener)`
- Emit typed payloads only: payload objects must be `AppPayload` instances
- Avoid ad-hoc payload literals in emissions (for example `emit('x', { ... })` is not allowed)

Boundary-facing browser/event channels may continue using native `EventTarget`/`CustomEvent` contracts where required by external APIs.

### Exception Handling

Do not type caught exceptions as `any` just to access `.message`.

- Catch as `unknown` (or untyped catch variable in strict mode).
- Normalize thrown values via shared helper: `toErrorMessage(error)` from `js/core/error-utils.ts`.
- Avoid direct `error.message` unless you first narrow with a type guard.

```ts
import { toErrorMessage } from '../core/error-utils.js';

try {
    await doWork();
} catch (error) {
    this._log('operation-failed', { error: toErrorMessage(error) });
}
```

---

## General Principles

### 1. Encapsulation First

**Always prefer public methods over direct property access:**

```ts
// ❌ Avoid
const activeId = workspace.config.activeCollectionId;

// ✅ Prefer
const activeId = workspace.getActiveCollectionId();
```

**Benefits:**
- Method can validate, transform, or compute the value
- Implementation can change without breaking callers
- Clear contract between components

### 2. Minimal Public API

**Keep public APIs small and intentional:**

- Only expose what external code truly needs
- Prefer private by default; make public when necessary
- Document public methods with TSDoc/docstrings

### 3. Consistent Naming

**Private members signal intent:**

- `_helper()` - Internal helper, may change
- `#private` - Truly private, not accessible
- `publicMethod()` - Stable contract

**If a method is public but shouldn't be called by external code, document it:**

```ts
/**
 * Internal method called by ViewFactory during deserialization.
 * External code should use deserialize() instead.
 * @internal
 */
_deserializeInternal(data) { }
```

### 4. Document Public APIs

**All public methods should have clear documentation:**

```python
def get_active_collection(self):
    """
    Get the currently active collection.

    Returns:
        Collection: The active collection instance, or None if no collections exist.
    """
    pass
```

```ts
/**
 * Get the currently active collection.
 * @returns {Collection|null} The active collection instance, or null if no collections exist.
 */
getActiveCollection() { }
```

---

## Logging Best Practices

### Do Not Log in High-Frequency Event Handlers

**Never add logging to event handlers that fire frequently (60+ times per second):**

```ts
// ❌ WRONG - Logging in high-frequency events
onMouseMove(event) {
    this._log('mouse-moved', 'debug', { x: event.clientX, y: event.clientY });
    // ... handle mouse move
}

onResizeObserver(entries) {
    this._log('resize-observed', 'debug', entries[0].contentRect);
    // ... handle resize
}

// ✅ CORRECT - Use browser DevTools for event debugging
onMouseMove(event) {
    // ... handle mouse move (no logging)
}

onResizeObserver(entries) {
    // ... handle resize (no logging)
}
```

**High-frequency events to avoid logging:**
- **Mouse**: `mousemove`, `mouseenter`, `mouseleave`, `mouseover`, `mouseout`
- **Touch**: `touchmove`, drag operations
- **Resize**: `ResizeObserver` callbacks, `scroll` events
- **Animation**: `requestAnimationFrame` callbacks
- **Viewport**: Pan, zoom, transform updates

**Rationale:**
- Creates performance overhead (object allocation, function calls)
- Clutters console output making debugging harder
- Browser DevTools provide better real-time event inspection

### Use Lazy Evaluation for Complex Log Data

Wrap expensive log data in functions to defer evaluation until logging is enabled:

```ts
// ❌ WRONG - Object/array always created even when logging is disabled
this._log('nodes-updated', 'debug', {
    nodes: this._nodes.map(n => n.serialize()),
    connections: this.calculateConnections()
});

// ✅ CORRECT - Lazy evaluation with function
this._log('nodes-updated', 'debug', () => ({
    nodes: this._nodes.map(n => n.serialize()),
    connections: this.calculateConnections()
}));

// ✅ ALSO CORRECT - Guard expensive operations
if (this._logEnabled('nodes-updated', 'debug')) {
    const data = {
        nodes: this._nodes.map(n => n.serialize()),
        connections: this.calculateConnections()
    };
    this._log('nodes-updated', 'debug', data);
}
```

**When to use lazy evaluation:**
- Object literals with computed properties
- Array transformations (`map`, `filter`, `reduce`)
- Method calls that perform calculations
- Nested object serialization
- String concatenation/formatting with many inputs

**When direct values are fine:**
- Simple variables (strings, numbers, booleans)
- Already-existing object references
- Single property accesses (no computation)

### Choose Appropriate Log Levels

Use log levels to indicate severity and enable production filtering:

```ts
// ✅ CORRECT - Use appropriate log levels
this._log('node-created', 'debug', nodeId);           // Development only
this._log('file-loaded', 'info', filename);           // Development only
this._log('deprecated-api', 'warn', methodName);      // Production too
this._log('operation-failed', 'error', errorDetails); // Production too
```

**Log levels:**
- **`debug`**: Detailed diagnostic information (removed in production builds)
- **`info`**: General informational messages (removed in production builds)
- **`warn`**: Warning conditions that should be investigated (kept in production)
- **`error`**: Error conditions that need attention (kept in production)

**Production builds:**
- Debug and info logs are completely eliminated via tree-shaking
- Warn and error logs remain for production debugging
- Results in smaller bundles and zero runtime overhead

### Standard Logging Pattern

Use the standard `_log()` method in all classes:

```ts
class MyClass extends ViewBase {
    someMethod() {
        // Simple values - no lazy evaluation needed
        this._log('button-clicked', 'info', buttonId);
        
        // Complex data - use lazy evaluation
        this._log('state-changed', 'debug', () => ({
            oldState: this._previousState,
            newState: this._currentState,
            delta: this.computeDelta()
        }));
    }
}
```

**See also:** Logging System Usage Guide for comprehensive documentation.

---

## Tooling

### Python

**Linting and Formatting:**
- **Ruff**: Configured in `pyproject.toml` for linting and formatting
- Run: `uv run ruff check src/` (lint)
- Run: `uv run ruff format src/` (format)

**Type Checking:**
- Not currently enforced but encouraged for new code
- Consider adding type hints for complex functions

### TypeScript

**Linting and Formatting:**
- **ESLint**: Configured in `eslint.config.js` for linting
- **Prettier**: Configured in `.prettierrc` for formatting
- Run: `npm run lint` (lint)
- Run: `npm run format` (format)

**Editor Integration:**
- VS Code automatically applies ESLint/Prettier on save
- Configure in `.vscode/settings.json` if not already set

---

## Enforcement

### Code Review Checklist

Reviewers must verify:

- [ ] **No private member access** from external classes
- [ ] **PEP 8 compliance** (Python)
- [ ] **Consistent naming conventions** (both languages)
- [ ] **Public API documented** with TSDoc/docstrings
- [ ] **ESLint/Ruff** passes without warnings

### Automated Checks

- **Pre-commit hooks**: Run linters automatically before commits
- **CI/CD**: GitHub Actions run linters on all PRs
- **Editor integration**: Real-time feedback in VS Code

---

## Migration Notes

### Fixing Private Member Access

If you find code accessing private members:

1. **Identify the need**: Why is this access required?
2. **Propose public API**: Create a public method to expose the functionality
3. **Update callers**: Refactor to use the new public method
4. **Document**: Add TSDoc/docstring to the new method

**Example Refactoring:**

```ts
// BEFORE - Direct private access
class ViewManager {
    constructor() {
        this._modalLayer = document.createElement('div');
    }
}

// External code:
viewManager._modalLayer.appendChild(dialog);  // WRONG

// AFTER - Public API added
class ViewManager {
    constructor() {
        this._modalLayer = document.createElement('div');
    }

    /**
     * Display a modal dialog.
     * @param {ViewBase} dialog - Dialog view to display
     */
    showModal(dialog) {
        dialog.attachTo(this._modalLayer);
        this._modalLayer.style.display = 'flex';
    }
}

// External code:
viewManager.showModal(dialog);  // CORRECT
```

---

## Summary

**Key Takeaways:**

- ✅ Follow **PEP 8** for Python, modern conventions for TypeScript
- ✅ **Never access private members** (`_field`, `#field`) from external classes
- ✅ **Use public APIs** exclusively for inter-class communication
- ✅ **Document public methods** with TSDoc/docstrings
- ✅ **Keep public APIs minimal** and intentional

**When in doubt:**
- If it starts with `_` or `#`, don't access it from another class
- If you need functionality, propose a public method
- Encapsulation > convenience

---

## Related Documentation

- **[Python PEP 8](https://peps.python.org/pep-0008/)** - Official Python style guide
- **View System Architecture** - Public API examples
- **Data Backbone Architecture** - Encapsulation patterns
