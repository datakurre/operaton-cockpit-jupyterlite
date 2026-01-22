"""JupyterLab extension that provides bpmn-moddle to Python via globalThis."""

__version__ = "0.1.0"

def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "@operaton/bpmn-moddle-extension"}]
