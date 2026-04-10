from __future__ import annotations

import logging
from pathlib import Path

import yaml

from pykal.cal import PyKal


def load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_pykal(cfg: dict, year: int, config_base: Path) -> PyKal:
    """Load all data sources and return a populated PyKal instance."""
    data_dir = config_base / cfg["paths"]["data_dir"]
    perso_dir = config_base / cfg["paths"]["perso_dir"]
    common_dir = data_dir / "common"
    year_dir = data_dir / str(year)
    prev_year_dir = data_dir / str(year - 1)
    sources = cfg["sources"]

    kal = PyKal(year)
    kal.parse_name_day_csv_file(common_dir / sources["name_days"])
    prev_holidays = prev_year_dir / sources["school_holidays"].format(year=year - 1)
    kal.parse_ics_file(prev_holidays, category="holiday", day_offset=-1)
    kal.parse_ics_file(
        year_dir / sources["school_holidays"].format(year=year),
        category="holiday", day_offset=-1,
    )
    kal.parse_ics_file(
        year_dir / sources["public_holidays"].format(year=year),
        category="holiday",
    )
    kal.parse_ics_file(
        year_dir / sources["garbage_collection"].format(year=year),
        category="garbage",
    )
    kal.parse_birthday_csv_file(perso_dir / sources["birthdays"])
    return kal


def run_generation(cfg: dict, year: int, config_base: Path) -> None:
    """Generate HTML calendar files for the given year."""
    data_dir = config_base / cfg["paths"]["data_dir"]
    build_dir = config_base / cfg["paths"]["build_dir"]
    common_dir = data_dir / "common"

    kal = load_pykal(cfg, year, config_base)
    kal.save_to_html(build_dir, common_dir)
    logging.info("Calendar generated in %s", build_dir / str(year))
