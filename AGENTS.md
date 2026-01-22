# AGENTS.md

This file provides guidance for AI coding agents working on this project.

## Project Overview

This is a JupyterLite-based plugin for Operaton Cockpit that provides BPMN and DMN visualization support. The project builds a static JupyterLite site that can be embedded in Operaton Cockpit.

## Tech Stack

- **Python 3.13+** - Runtime
- **uv** - Package manager
- **JupyterLite** - Browser-based Jupyter environment
- **Pyodide** - Python runtime for WebAssembly
- **devenv/Nix** - Development environment (optional)

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project configuration and dependencies |
| `jupyter_lite_config.json` | JupyterLite build configuration (Pyodide packages) |
| `jupyter-lite.json` | JupyterLite runtime settings |
| `Makefile` | Build and development commands |
| `files/operaton.py` | Python API client for Operaton engine (included in build) |
| `devenv.nix` | Nix-based development environment configuration |

## Build System

The project uses JupyterLite with `jupyterlite-pyodide-lock` to create reproducible builds with locked dependencies.

### Build Output

- Output directory: `dist/`
- Build state: `.jupyterlite.doit.db`

### Adding Pyodide Packages

To add Python packages available in the JupyterLite environment, edit `jupyter_lite_config.json` under `PyodideLockAddon.specs`.

## Common Tasks

```bash
# Install dependencies
uv sync

# Build the site
make build

# Serve locally (port 8888)
make serve

# Clean build artifacts
make clean
```

## Operaton Integration

The `files/operaton.py` module provides an `Operaton` class for interacting with the Operaton engine REST API from within notebooks. It uses environment variables:

- `OPERATON_ENGINE_API` - Base URL for the Operaton REST API
- `OPERATON_CSRF_TOKEN` - CSRF token for POST/PUT/DELETE requests

## Notes for Agents

- The `dist/` directory is the build output - don't commit it
- When modifying Pyodide packages, update both `jupyter_lite_config.json` and the README.md documentation
- The project uses offline mode (`PyodideLockOfflineAddon`) to bundle all packages for network-free operation
- Files in `files/` directory are automatically included in the JupyterLite build
