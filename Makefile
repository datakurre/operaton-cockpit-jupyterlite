.PHONY: develop build build-js clean serve

default: build

# Development environment
develop:
	devenv shell --profile devcontainer -- code .

# Clean build artifacts
clean:
	rm -rf dist .jupyterlite.doit.db jupyter-lite-route.js
	cd packages/operaton-extension && rm -f tsconfig.tsbuildinfo && rm -rf bpmn_moddle_extension && npm run clean --if-present || true

# Install Node.js dependencies
install-js:
	npm install

# Build JavaScript packages (JupyterLab extension with bpmn-moddle)
# Step 1: Build TypeScript and webpack bundle
# Step 2: Build labextension using uv run (requires lib/ to exist first)
# Step 3: Install in venv for JupyterLite to find
build-js: install-js
	npm run build
	uv run jupyter labextension build packages/operaton-extension --development True
	uv run jupyter labextension build /workspaces/camunda-cockpit-plugin-jupyter/packages/jupyterlab-bpmn --development True
	uv run jupyter labextension build /workspaces/camunda-cockpit-plugin-jupyter/packages/jupyterlab-dmn --development True
	@echo "Installing extensions in venv..."
	mkdir -p .devenv/state/venv/share/jupyter/labextensions/@operaton/operaton-extension/static
	cp -r packages/operaton-extension/operaton_extension/labextension/* .devenv/state/venv/share/jupyter/labextensions/@operaton/operaton-extension/
	cp packages/operaton-extension/operaton_extension/static/bpmn-moddle.umd.js .devenv/state/venv/share/jupyter/labextensions/@operaton/operaton-extension/static/
	cp packages/operaton-extension/operaton_extension/static/dmn-moddle.umd.js .devenv/state/venv/share/jupyter/labextensions/@operaton/operaton-extension/static/
	mkdir -p .devenv/state/venv/share/jupyter/labextensions/jupyterlab-bpmn
	cp -r packages/jupyterlab-bpmn/jupyterlab_bpmn/labextension/* .devenv/state/venv/share/jupyter/labextensions/jupyterlab-bpmn/
	mkdir -p .devenv/state/venv/share/jupyter/labextensions/jupyterlab-dmn
	cp -r packages/jupyterlab-dmn/jupyterlab_dmn/labextension/* .devenv/state/venv/share/jupyter/labextensions/jupyterlab-dmn/

# Build JupyterLite site with locked dependencies
build: clean build-js
	uv run jupyter lite build --output-dir dist
	@echo "Copying fresh extension files to dist..."
	cp -r packages/operaton-extension/operaton_extension/labextension/static/* dist/extensions/@operaton/operaton-extension/static/
	cp packages/operaton-extension/operaton_extension/labextension/package.json dist/extensions/@operaton/operaton-extension/
	cp packages/operaton-extension/operaton_extension/static/bpmn-moddle.umd.js dist/extensions/@operaton/operaton-extension/static/
	cp packages/operaton-extension/operaton_extension/static/dmn-moddle.umd.js dist/extensions/@operaton/operaton-extension/static/
	cp -r packages/jupyterlab-bpmn/jupyterlab_bpmn/labextension/static/* dist/extensions/jupyterlab-bpmn/static/
	cp packages/jupyterlab-bpmn/jupyterlab_bpmn/labextension/package.json dist/extensions/jupyterlab-bpmn/
	cp -r packages/jupyterlab-dmn/jupyterlab_dmn/labextension/static/* dist/extensions/jupyterlab-dmn/static/
	cp packages/jupyterlab-dmn/jupyterlab_dmn/labextension/package.json dist/extensions/jupyterlab-dmn/
	@echo "Copying Operaton Cockpit route plugin..."
	cp jupyter-lite-route.js dist/

# Serve the built site locally
serve:
	uv run jupyter lite serve --output-dir dist --port 8888

# Build and serve
all: build serve
