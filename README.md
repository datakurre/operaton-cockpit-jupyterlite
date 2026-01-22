# Operaton Cockpit Jupyter Lite

A JupyterLite-based plugin for Operaton Cockpit with BPMN and DMN support, including JavaScript interop with `bpmn-moddle`.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - Python package manager
- [Node.js](https://nodejs.org/) (v18+) - For building custom Pyodide kernel
- [devenv](https://devenv.sh/) - Development environment (optional)

## Quick Start

### Install dependencies

```bash
uv sync
npm install
```

### Build JupyterLite site

```bash
make build
```

This will:
1. Install npm dependencies
2. Build the custom Pyodide kernel with bpmn-moddle
3. Build the JupyterLite site

### Serve locally

```bash
make serve
```

Then open http://localhost:8888 in your browser.

## Clean Build

To perform a clean build (recommended when changing dependencies):

```bash
make clean build
```

## BPMN Moddle Integration

This project includes the `@operaton/operaton-extension` JupyterLab extension that provides a BroadcastChannel bridge between the main window and Pyodide workers. This enables Python code to access the `bpmn-moddle` JavaScript library and localStorage.

### Usage from Python

```python
# Use the Python wrapper
from bpmn_moddle import load_bpmn_moddle, parse_bpmn

# Load the bpmn-moddle library (fetched via BroadcastChannel)
await load_bpmn_moddle()

# Parse BPMN XML
result = await parse_bpmn(bpmn_xml)
print(result['definitions'])
```

See [files/test-bpmn-moddle.ipynb](files/test-bpmn-moddle.ipynb) for more examples.

## Configuration

### Python Packages

Python packages for the Pyodide kernel are configured in `jupyter_lite_config.json` under `PyodideLockAddon.specs`:

- `pyodide-kernel` - Core kernel
- `piplite` - Package installer
- `ipykernel` - IPython kernel
- `comm` - Jupyter comm implementation
- `ipywidgets` - Interactive widgets
- `bqplot` - 2-D plotting library
- `jupyterlab-bpmn` - BPMN viewer/editor
- `jupyterlab-dmn` - DMN viewer/editor

### Offline Mode

The `PyodideLockOfflineAddon` is enabled to download all locked packages for offline use. This ensures the site works without network access.

## Development

```bash
make develop
```

## Make Targets

| Target | Description |
|--------|-------------|
| `make build` | Clean, build JS packages, and build JupyterLite site |
| `make build-js` | Build only the JavaScript packages |
| `make install-js` | Install npm dependencies |
| `make clean` | Remove build artifacts |
| `make serve` | Serve the site on port 8888 |
| `make develop` | Open VS Code in devenv shell |
| `make all` | Build and serve |

## Project Structure

```
├── packages/                      # Custom JavaScript packages
│   └── operaton-extension/        # JupyterLab extension with BroadcastChannel bridge
│       ├── src/                   # TypeScript source
│       └── operaton_extension/    # Python package with built labextension
├── files/                         # Files included in JupyterLite
│   ├── bpmn_moddle.py            # Python wrapper for bpmn-moddle
│   ├── operaton.py               # Operaton API client
│   └── test-bpmn-moddle.ipynb    # BPMN moddle test notebook
├── jupyter_lite_config.json      # JupyterLite build config
├── jupyter-lite.json             # JupyterLite runtime settings
├── package.json                  # npm monorepo config
└── pyproject.toml                # Python project config
```
