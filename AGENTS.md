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
| `files/bpmn_moddle.py` | Python wrapper for bpmn-moddle |
| `files/test-bpmn-moddle.ipynb` | Test notebook for bpmn-moddle |
| `devenv.nix` | Nix-based development environment configuration |

## Directory Structure

```
├── packages/                           # Custom JavaScript packages
│   └── operaton-extension/             # JupyterLab extension
│       ├── src/                        # TypeScript source
│       │   └── index.ts                # BroadcastChannel bridge
│       ├── operaton_extension/         # Python package
│       │   ├── labextension/           # Built JupyterLab extension
│       │   └── static/                 # Static assets (bpmn-moddle.umd.js)
│       ├── package.json
│       ├── pyproject.toml
│       ├── tsconfig.json
│       └── webpack.config.js
├── files/                              # Files included in build
│   ├── bpmn_moddle.py                  # Python wrapper for bpmn-moddle
│   ├── operaton.py                     # Operaton API client
│   └── test-bpmn-moddle.ipynb          # Test notebook
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
| `get_bpmn_moddle_bundle` | Returns the bpmn-moddle UMD bundle code |
| `get_localstorage` | Read a localStorage value |
| `set_localstorage` | Write a localStorage value |
| `remove_localstorage` | Remove a localStorage key |
| `get_localstorage_keys` | List all localStorage keys |

### Usage from Python

```python
from bpmn_moddle import load_bpmn_moddle, parse_bpmn

# Load bpmn-moddle (fetched via BroadcastChannel bridge)
await load_bpmn_moddle()

# Parse BPMN XML
result = await parse_bpmn(bpmn_xml)
```

### Adding JavaScript Libraries

To add more JavaScript libraries to be served via the bridge:

1. Add dependency to `packages/operaton-extension/package.json`
2. Bundle via webpack into UMD format
3. Add a new action in `src/index.ts` to fetch and return the bundle
4. Add corresponding Python code in `files/bpmn_moddle.py` (or a new module)

### Adding Pyodide Packages

To add Python packages available in the JupyterLite environment, edit `jupyter_lite_config.json` under `PyodideLockAddon.specs`.

## Operaton Integration

The `files/operaton.py` module provides an `Operaton` class for interacting with the Operaton engine REST API from within notebooks. It uses environment variables:

- `OPERATON_ENGINE_API` - Base URL for the Operaton REST API
- `OPERATON_CSRF_TOKEN` - CSRF token for POST/PUT/DELETE requests

## Notes for Agents

- The `dist/` directory is the build output - don't commit it
- The `node_modules/` directory is gitignored
- When modifying Pyodide packages, update `jupyter_lite_config.json`
- When modifying JavaScript packages, run `make build-js`
- The project uses offline mode (`PyodideLockOfflineAddon`) to bundle all packages
- Files in `files/` directory are automatically included in the JupyterLite build
- TypeScript compilation errors in kernel packages will break the build
