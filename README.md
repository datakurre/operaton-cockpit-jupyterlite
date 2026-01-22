# Operaton Cockpit Jupyter Lite

A JupyterLite-based plugin for Operaton Cockpit with BPMN and DMN support.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - Python package manager
- [devenv](https://devenv.sh/) - Development environment (optional)

## Quick Start

### Install dependencies

```bash
uv sync
```

### Build JupyterLite site

```bash
make build
```

Or manually:

```bash
uv run jupyter lite build --output-dir dist
```

### Serve locally

```bash
make serve
```

Or manually:

```bash
uv run jupyter lite serve --output-dir dist --port 8888
```

## Clean Build

To perform a clean build (recommended when changing dependencies):

```bash
make clean build
```

Or manually:

```bash
rm -rf dist .jupyterlite.doit.db
uv run jupyter lite build --output-dir dist
```

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
| `make build` | Clean and build the JupyterLite site |
| `make clean` | Remove build artifacts |
| `make serve` | Serve the site on port 8888 |
| `make develop` | Open VS Code in devenv shell |
| `make all` | Build and serve |
