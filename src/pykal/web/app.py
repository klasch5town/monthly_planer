from __future__ import annotations

from pathlib import Path

import click
from flask import Flask


def create_app(config_path: Path) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = "pykal-dev-secret"
    app.config["PYKAL_CONFIG_PATH"] = config_path.resolve()

    from pykal.web.routes import bp
    app.register_blueprint(bp)

    return app


@click.command()
@click.option("--config", "config_path", default="pykal.yaml", show_default=True,
              type=click.Path(dir_okay=False, path_type=Path),
              help="Path to YAML configuration file.")
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind to.")
@click.option("--port", default=5000, show_default=True, help="Port to listen on.")
@click.option("--debug", is_flag=True, default=False, help="Enable Flask debug mode.")
def serve(config_path: Path, host: str, port: int, debug: bool) -> None:
    """Start the pykal web interface."""
    app = create_app(config_path)
    app.run(host=host, port=port, debug=debug)
