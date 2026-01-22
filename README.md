# Operaton Cockpit Jupyter Lite

A JupyterLite-based plugin for Operaton Cockpit that provides BPMN and DMN visualization, parsing, comparison, and REST API access. The project builds a static JupyterLite site that can be embedded in Operaton Cockpit.

## Features

- **BPMN Moddle** - Parse and serialize BPMN 2.0 XML with Camunda extensions
- **DMN Moddle** - Parse and serialize DMN 1.3 XML with Camunda extensions
- **BPMN-JS-Differ** - Compare two BPMN diagrams and identify changes
- **REST API Client** - Interact with the Operaton engine REST API
- **BPMN/DMN Renderers** - Visual rendering of BPMN and DMN files in notebooks

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - Python package manager
- [Node.js](https://nodejs.org/) (v18+) - For building JavaScript packages
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
2. Build the JupyterLab extensions (operaton-extension, jupyterlab-bpmn, jupyterlab-dmn)
3. Build the JupyterLite static site

### Serve locally

```bash
make serve
```

Then open http://localhost:8888 in your browser.

## Usage from Python

The unified `operaton` module provides all functionality:

```python
import operaton
from operaton import Operaton

# Load environment variables from localStorage (required for REST API)
await operaton.load_env()

# REST API
definitions = Operaton.get('/process-definition')

# BPMN Moddle - parse and serialize BPMN XML
await operaton.load_bpmn_moddle()
result = await operaton.parse_bpmn(bpmn_xml)
xml = await operaton.to_bpmn_xml(result.rootElement)

# DMN Moddle - parse and serialize DMN XML
await operaton.load_dmn_moddle()
result = await operaton.parse_dmn(dmn_xml)
xml = await operaton.to_dmn_xml(result.rootElement)

# BPMN Differ - compare two BPMN diagrams
diff_result = await operaton.compare_bpmn(old_bpmn_xml, new_bpmn_xml)
print(diff_result.added_ids)     # List of added element IDs
print(diff_result.removed_ids)   # List of removed element IDs
print(diff_result.changed_ids)   # List of changed element IDs
```

## Example Notebooks

See the [files/examples/](files/examples/) directory for working examples:

- [bpmn-moddle.ipynb](files/examples/bpmn-moddle.ipynb) - BPMN parsing demo
- [dmn-moddle.ipynb](files/examples/dmn-moddle.ipynb) - DMN parsing demo
- [bpmn-differ.ipynb](files/examples/bpmn-differ.ipynb) - BPMN comparison demo
- [operaton-api.ipynb](files/examples/operaton-api.ipynb) - REST API demo

## Architecture

The `@operaton/operaton-extension` JupyterLab extension provides a BroadcastChannel bridge between the main window and Pyodide Web Workers. This enables Python code to access:

- JavaScript libraries (bpmn-moddle, dmn-moddle, bpmn-js-differ)
- localStorage (not available directly in Web Workers)

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

## Make Targets

| Target | Description |
|--------|-------------|
| `make build` | Clean, build JS packages, and build JupyterLite site |
| `make build-debug` | Build with debug logging enabled |
| `make build-js` | Build only the JavaScript packages |
| `make install-js` | Install npm dependencies |
| `make clean` | Remove build artifacts |
| `make serve` | Serve the site on port 8888 |

## Clean Build

To perform a clean build (recommended when changing dependencies):

```bash
make clean build
```
