from __future__ import annotations

import logging
from importlib.metadata import version
from pathlib import Path

import click

from pykal.generate import load_config, run_generation


@click.command()
@click.version_option(version("pykal"))
@click.option("--year", type=int, default=None, help="Target year (overrides config).")
@click.option("--config", "config_path", default="pykal.yaml", show_default=True,
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help="Path to YAML configuration file.")
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable info logging.")
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging.")
def main(year: int | None, config_path: Path, verbose: bool, debug: bool) -> None:
    """Generate a personal HTML calendar."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)

    cfg = load_config(config_path)
    target_year: int = year or cfg["year"]
    run_generation(cfg, target_year, config_path.parent)
