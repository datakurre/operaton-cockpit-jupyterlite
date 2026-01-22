.PHONY: develop build clean serve

default: build

# Development environment
develop:
	devenv shell --profile devcontainer -- code .

# Clean build artifacts
clean:
	rm -rf dist .jupyterlite.doit.db

# Build JupyterLite site with locked dependencies
build: clean
	uv run jupyter lite build --output-dir dist

# Serve the built site locally
serve:
	uv run jupyter lite serve --output-dir dist --port 8888

# Build and serve
all: build serve
