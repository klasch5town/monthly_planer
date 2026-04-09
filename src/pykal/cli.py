from __future__ import annotations

import logging
from importlib.metadata import version
from pathlib import Path

import click
import yaml

from pykal.cal import PyKal


def _load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


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

    cfg = _load_config(config_path)

    target_year: int = year or cfg["year"]

    # Resolve directories relative to the config file location
    base = config_path.parent
    data_dir = base / cfg["paths"]["data_dir"]
    build_dir = base / cfg["paths"]["build_dir"]
    perso_dir = base / cfg["paths"]["perso_dir"]
    common_dir = data_dir / "common"
    year_dir = data_dir / str(target_year)
    prev_year_dir = data_dir / str(target_year - 1)

    sources = cfg["sources"]

    kal = PyKal(target_year)
    kal.parse_name_day_csv_file(common_dir / sources["name_days"])
    # Previous year school holidays cover Christmas holidays in January
    prev_holidays = prev_year_dir / sources["school_holidays"].format(year=target_year - 1)
    kal.parse_ics_file(prev_holidays, category="holiday", day_offset=-1)
    kal.parse_ics_file(
        year_dir / sources["school_holidays"].format(year=target_year),
        category="holiday", day_offset=-1,
    )
    kal.parse_ics_file(
        year_dir / sources["public_holidays"].format(year=target_year),
        category="holiday",
    )
    kal.parse_ics_file(
        year_dir / sources["garbage_collection"].format(year=target_year),
        category="garbage",
    )
    birthdays_file = perso_dir / sources["birthdays"]
    kal.parse_birthday_csv_file(birthdays_file)

    kal.save_to_html(build_dir, common_dir)
