# AGENTS.md

This file provides guidance for AI coding agents working on this project.

## Project Overview

This is a JupyterLite-based plugin for Operaton Cockpit that provides BPMN and DMN visualization support. The project builds a static JupyterLite site that can be embedded in Operaton Cockpit. It includes a custom Pyodide kernel with `bpmn-moddle` JavaScript library pre-loaded for BPMN diagram parsing.

## Tech Stack

- **Python 3.13+** - Runtime
- **uv** - Python package manager
- **Node.js 18+** - For building custom Pyodide kernel
- **npm** - JavaScript package manager (workspaces)
- **TypeScript** - Custom kernel implementation
- **JupyterLite** - Browser-based Jupyter environment
- **Pyodide** - Python runtime for WebAssembly
- **bpmn-moddle** - BPMN 2.0 parsing library (JavaScript)
- **devenv/Nix** - Development environment (optional)

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project configuration and dependencies |
| `package.json` | npm monorepo configuration |
| `jupyter_lite_config.json` | JupyterLite build configuration (Pyodide packages) |
| `jupyter-lite.json` | JupyterLite runtime settings |
| `Makefile` | Build and development commands |
| `files/operaton.py` | Unified Python library (BPMN/DMN moddle, differ, REST API) |
| `files/examples/` | Example notebooks demonstrating library usage |
| `devenv.nix` | Nix-based development environment configuration |

## Directory Structure

```
├── packages/                           # Custom JavaScript packages
│   ├── operaton-extension/             # JupyterLab extension (bridge)
│   │   ├── src/                        # TypeScript source
│   │   │   ├── index.ts                # BroadcastChannel bridge
│   │   │   ├── bpmn-moddle-umd.js      # BPMN moddle bundle entry
│   │   │   └── dmn-moddle-umd.js       # DMN moddle bundle entry
│   │   ├── operaton_extension/         # Python package
│   │   │   ├── labextension/           # Built JupyterLab extension
│   │   │   └── static/                 # Static assets (bpmn/dmn-moddle.umd.js)
│   │   ├── package.json
│   │   ├── pyproject.toml
│   │   └── tsconfig.json
│   ├── jupyterlab-bpmn/                # Vendored BPMN file renderer
│   │   ├── src/                        # TypeScript source
│   │   ├── jupyterlab_bpmn/            # Python package
│   │   └── package.json
│   └── jupyterlab-dmn/                 # Vendored DMN file renderer
│       ├── src/                        # TypeScript source
│       ├── jupyterlab_dmn/             # Python package
│       └── package.json
├── files/                              # Files included in build
│   ├── operaton.py                     # Unified Python library
│   └── examples/                       # Example notebooks
│       ├── bpmn-moddle.ipynb           # BPMN parsing demo
│       ├── dmn-moddle.ipynb            # DMN parsing demo
│       ├── bpmn-differ.ipynb           # BPMN comparison demo
│       └── operaton-api.ipynb          # REST API demo
├── dist/                               # Build output (gitignored)
└── node_modules/                       # npm packages (gitignored)
```

## Build System

The project uses a two-stage build process:

1. **JavaScript Build**: Builds custom Pyodide kernel with bpmn-moddle
2. **JupyterLite Build**: Creates the static site with locked dependencies

### Build Commands

```bash
# Full build (JS + JupyterLite)
make build

# JavaScript packages only
make build-js

# Install npm dependencies
make install-js

# Clean build artifacts
make clean

# Serve locally (port 8888)
make serve
```

### Build Output

- Output directory: `dist/`
- Build state: `.jupyterlite.doit.db`

## BroadcastChannel Bridge Architecture

The `@operaton/operaton-extension` provides a communication bridge between the JupyterLab main window and Pyodide Web Workers using the BroadcastChannel API:

1. **Extension (main window)** - Listens on BroadcastChannel `'operaton-bridge'`
2. **Python module (worker)** - Sends requests and receives responses via the same channel
3. **bpmn-moddle bundle** - Fetched by the extension and passed to workers on request

This architecture solves the problem that Web Workers cannot directly access:
- JavaScript libraries loaded in the main window
- localStorage

### Supported Actions

| Action | Description |
|--------|-------------|
| `get_bpmn_moddle_bundle` | Returns the bpmn-moddle UMD bundle code (with Camunda extensions) |
| `get_dmn_moddle_bundle` | Returns the dmn-moddle UMD bundle code (with Camunda extensions) |
| `get_bpmn_js_differ_bundle` | Returns the bpmn-js-differ UMD bundle code |
| `get_localstorage` | Read a localStorage value |
| `set_localstorage` | Write a localStorage value |
| `remove_localstorage` | Remove a localStorage key |
| `get_localstorage_keys` | List all localStorage keys |

### Usage from Python

All functionality is available through the unified `operaton` module:

```python
import operaton
from operaton import Operaton

# Load environment (required for REST API)
await operaton.load_env()

# REST API
definitions = Operaton.get('/process-definition')

# BPMN parsing (with Camunda extensions)
await operaton.load_bpmn_moddle()
result = await operaton.parse_bpmn(bpmn_xml)
xml = await operaton.to_bpmn_xml(result.rootElement)

# DMN parsing (with Camunda extensions)
await operaton.load_dmn_moddle()
result = await operaton.parse_dmn(dmn_xml)
xml = await operaton.to_dmn_xml(result.rootElement)

# BPMN diffing (comparing two BPMN diagrams)
diff_result = await operaton.compare_bpmn(old_bpmn_xml, new_bpmn_xml)
print(diff_result.added_ids)     # List of added element IDs
print(diff_result.removed_ids)   # List of removed element IDs  
print(diff_result.changed_ids)   # List of changed element IDs
```

### Adding JavaScript Libraries

To add more JavaScript libraries to be served via the bridge:

1. Add dependency to `packages/operaton-extension/package.json`
2. Bundle via webpack into UMD format
3. Add a new action in `src/index.ts` to fetch and return the bundle
4. Add corresponding Python code in `files/operaton.py`

### Adding Pyodide Packages

To add Python packages available in the JupyterLite environment, edit `jupyter_lite_config.json` under `PyodideLockAddon.specs`.

## Operaton Integration

The `files/operaton.py` module is a unified Python library that provides:

1. **BroadcastChannel Bridge** - Communication with JupyterLab extension
2. **BPMN Moddle** - Parse and serialize BPMN 2.0 XML (with Camunda extensions)
3. **DMN Moddle** - Parse and serialize DMN 1.3 XML (with Camunda extensions)
4. **BPMN-JS-Differ** - Compare two BPMN diagrams
5. **REST API Client** - Interact with Operaton engine REST API

Environment variables (loaded via `await operaton.load_env()` from localStorage):

- `OPERATON_ENGINE_API` - Base URL for the Operaton REST API
- `OPERATON_CSRF_TOKEN` - CSRF token for POST/PUT/DELETE requests

## Async Limitations in ipywidgets + Pyodide + JupyterLite

This section documents critical limitations when using async/await with ipywidgets in Pyodide running in JupyterLite. Understanding these constraints is essential for building interactive notebooks.

### The Core Problem

ipywidgets event callbacks (like `button.on_click()`) are executed **synchronously** by the JavaScript event system. However, many operations in Pyodide require `async/await` (e.g., BroadcastChannel communication, JavaScript Promises). This creates a fundamental mismatch.

### Limitation 1: `asyncio.ensure_future()` in Callbacks

**Problem**: Using `asyncio.ensure_future(coroutine)` inside a widget callback (like `button.on_click`) often fails or behaves unexpectedly in Pyodide.

```python
# THIS DOES NOT WORK RELIABLY IN PYODIDE
def on_button_click(button):
    asyncio.ensure_future(some_async_function())  # May not execute properly

button.on_click(on_button_click)
```

**Why**: The Pyodide WebLoop is already running when the callback is triggered. `ensure_future` schedules the coroutine but the event loop may not process it as expected because the synchronous callback blocks the loop's ability to advance.

### Limitation 2: No `await` in Synchronous Callbacks

**Problem**: Widget callbacks are synchronous - you cannot use `await` directly:

```python
# THIS IS A SYNTAX ERROR - callbacks can't be async
async def on_button_click(button):
    result = await some_async_function()  # Can't do this!

button.on_click(on_button_click)  # on_click expects a sync function
```

### Limitation 3: Nested Event Loop Issues

**Problem**: Pyodide uses a custom `WebLoop` for asyncio that integrates with the browser's event loop. You cannot call `asyncio.run()` or `loop.run_until_complete()` from within a running event loop.

```python
# THIS WILL FAIL
def on_button_click(button):
    asyncio.run(some_async_function())  # RuntimeError: event loop already running
```

### Limitation 4: BroadcastChannel Responses May Be Lost

**Problem**: When async code is triggered from a synchronous callback, BroadcastChannel responses may not be processed because the message handler depends on the event loop advancing.

### Workarounds and Solutions

#### Solution 1: Pre-load All Async Resources Before Widget Interaction

Move all async operations to notebook cells that run before the widget is displayed:

```python
# Cell 1: Load everything async (this works - top-level await)
await operaton.load_env()
await operaton.load_bpmn_moddle()
await operaton.load_bpmn_js_differ()

# Cell 2: Now use synchronous-only operations in widgets
def on_button_click(button):
    # Use only sync operations here
    xml = Operaton.get(f'/process-definition/{id}/xml')  # Sync REST call
    # Store for later use
    global cached_xml
    cached_xml = xml
```

#### Solution 2: Use `pyodide.webloop.WebLoopPolicy` with `create_task`

In some cases, `asyncio.create_task()` may work better than `ensure_future()`:

```python
import asyncio

async def do_async_work():
    result = await some_async_function()
    # Update widget output here

def on_button_click(button):
    asyncio.create_task(do_async_work())
```

**Note**: This still has limitations and may not work in all scenarios.

#### Solution 3: Use JavaScript `setTimeout` to Defer Execution

Use JavaScript interop to defer the async work to a new event loop tick:

```python
from pyodide.ffi import create_proxy
import js

async def do_work():
    result = await async_operation()
    # process result

def on_button_click(button):
    # Defer to next event loop tick
    async def deferred():
        await do_work()
    
    proxy = create_proxy(lambda: asyncio.create_task(deferred()))
    js.setTimeout(proxy, 0)
```

#### Solution 4: Redesign to Avoid Async in Callbacks

The most robust solution is to redesign the workflow:

1. **Fetch all data upfront** in async cells before widget creation
2. **Cache results** in module-level variables
3. **Use only synchronous operations** in widget callbacks
4. **Display results** that were pre-computed

Example pattern:
```python
# Cell 1: Async setup (runs at cell execution time)
all_definitions = Operaton.get('/process-definition?latestVersion=false')
xml_cache = {}

async def prefetch_all_xml():
    for defn in all_definitions:
        response = Operaton.get(f'/process-definition/{defn["id"]}/xml')
        xml_cache[defn['id']] = response['bpmn20Xml']
        
await prefetch_all_xml()

# Cell 2: Widget with only sync operations
def on_compare_click(button):
    old_xml = xml_cache[old_dropdown.value]  # Sync lookup
    new_xml = xml_cache[new_dropdown.value]  # Sync lookup
    # ... compute diff using pre-loaded libraries
```

### Pyodide Stack Switching (Experimental)

Pyodide has experimental "stack switching" support (`enableRunUntilComplete` option in `loadPyodide`) that allows `run_until_complete` to block using WebAssembly stack switching. This is enabled by default in recent Pyodide versions (0.27.7+), but:

- Requires browser support for WebAssembly stack switching (JSPI)
- May not be fully compatible with JupyterLite's kernel architecture
- Should not be relied upon for production code yet

### Summary Table

| Pattern | Works in Pyodide/JupyterLite? | Notes |
|---------|------------------------------|-------|
| Top-level `await` in cells | ✅ Yes | The standard way to use async |
| `asyncio.ensure_future()` in callback | ⚠️ Unreliable | May not execute as expected |
| `asyncio.create_task()` in callback | ⚠️ Unreliable | Similar issues |
| `asyncio.run()` in callback | ❌ No | Event loop already running |
| `await` in callback | ❌ No | Callbacks must be sync |
| Pre-loading then sync operations | ✅ Yes | Recommended approach |

## Notes for Agents

- The `dist/` directory is the build output - don't commit it
- The `node_modules/` directory is gitignored
- When modifying Pyodide packages, update `jupyter_lite_config.json`
- When modifying JavaScript packages, run `make build-js`
- The project uses offline mode (`PyodideLockOfflineAddon`) to bundle all packages
- Files in `files/` directory are automatically included in the JupyterLite build
- TypeScript compilation errors in kernel packages will break the build
