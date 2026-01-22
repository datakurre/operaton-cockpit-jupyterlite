"""Patch index.html for Operaton plugin.

This addon patches the JupyterLite index.html files to listen for environment
data from the parent Operaton Cockpit window and store it in localStorage.
The communication uses the postMessage API.
"""

from jupyterlite_core.addons.base import BaseAddon

PATCH = """
        // Capture and save Operaton API information sent by Operaton Plugin API
        window.addEventListener('message', function(ev) {
          if (window.location.toString().startsWith(ev.origin)) {
            const env = {};
            for (const key of Object.keys(ev.data)) {
              env['OPERATON_' + key.replace('Api', '_API').replace('Token', '_TOKEN').toUpperCase()] = key.endsWith('Api') ? ev.origin + ev.data[key] : ev.data[key];
            }
            window.localStorage.setItem('env', JSON.stringify(env));
          }
        });
        window.parent.postMessage('ready');
"""


class OperatonAddon(BaseAddon):
    """Patch index.html for Operaton plugin."""

    __all__ = ["post_build"]

    def __init__(self, manager, *args, **kwargs):
        kwargs["parent"] = manager
        kwargs["manager"] = manager
        super().__init__(*args, **kwargs)

    def post_build(self, manager):
        """Yield doit tasks to patch index.html files."""
        paths = list(manager.output_dir.glob("*/index.html"))
        yield dict(
            name="patch:index.html",
            doc="ensure index.html has Operaton patch",
            file_dep=[*paths],
            actions=[(self.patch, [paths])],
            targets=[*[f"{path}#operaton" for path in paths]],
        )

    def patch(self, paths):
        """Patch index.html for Operaton plugin."""
        for path in paths:
            index_html = path.read_text()
            if PATCH in index_html:
                continue
            # Find the location after config-utils.js is loaded
            match = index_html.find("config-utils.js")
            match = match + index_html[match:].find(");") if match > -1 else -1
            if match > -1:
                match += len(");")
                path.write_text(
                    index_html[0:match] + PATCH + index_html[match:]
                )
