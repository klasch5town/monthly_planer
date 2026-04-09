# pykal

[![CI](https://github.com/klasch5town/monthly_planer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/klasch5town/monthly_planer/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://docs.astral.sh/uv/)
[![version](https://img.shields.io/badge/version-2.0.0-informational)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Generates a personal monthly HTML calendar as a set of HTML files — one per month. Events, school holidays, public holidays, birthdays, name days, and garbage collection schedules can be fed in via ICS and CSV files.

## Project layout

```
src/pykal/          Python package (cal, cli, html, icalendar modules)
data/
  common/           Static reference data (Namenstage.csv, stylesheet.css)
  <year>/           Year-specific ICS files (not versioned, downloaded from internet)
data/               Moon phase SVG images
tests/              pytest test suite
build/              Generated HTML output (not versioned)
perso/              Personal data — birthdays, events (not versioned, never commit)
doc/                Documentation and print setup screenshots
pykal.yaml          Configuration file
pyproject.toml      Package and dependency definition (managed with uv)
```

## Requirements

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) for environment and package management

## Setup

```bash
uv sync
```

## Usage

```bash
uv run pykal                        # use year from pykal.yaml
uv run pykal --year 2025            # override year
uv run pykal --year 2026 --verbose  # with info logging
uv run pykal --help                 # all options
```

The generated HTML files are written to `build/<year>/`.

## Configuration

All configuration lives in `pykal.yaml`:

```yaml
year: 2026

paths:
  data_dir: data      # root for ICS source files
  build_dir: build    # HTML output destination
  perso_dir: perso    # personal data (gitignored)

sources:
  name_days:         Namenstage.csv
  school_holidays:   "ferien_bayern_{year}.ics"
  public_holidays:   "feiertage_bayern_{year}.ics"
  garbage_collection: "Abfuhrkalender-<municipality>-{year}.ics"
  birthdays:         myGeburtstage.csv
```

### Obtaining ICS source files

- School holidays: https://www.schulferien.org/deutschland/ical/
- Public holidays: https://www.ferienwiki.de/exports/de
- Garbage collection: provided by your local waste disposal authority

Place the downloaded files in `data/<year>/`.

### Birthday CSV format

File lives in `perso/` (not versioned). Three tab-separated columns:

| Column | Content |
|--------|---------|
| 1 | Birthday date: `YYYY-MM-DD` |
| 2 | Name |
| 3 | Date confirmed: `True` / `False` |

If the year is uncertain, use `False` — pykal will append `??` to the age so you are not caught quoting the wrong number.

## Public holidays

Bavarian/Augsburg public holidays and notable days are calculated internally (no external ICS needed). Easter-dependent dates are computed for any year >= 1583.

## Printing

### From browser (recommended)

- Enable "Print Background Colors and Images" in your browser's print dialog
- Disable header/footer
- Firefox → print to file → open PDF → set A3 portrait
- Months with 31 days may need scaling to ~97%

### With Pandoc / LaTeX

A `template.latex` is provided in `data/common/` for Pandoc-based PDF generation. This does currently not work properly, but may be improved in future.

```bash
sudo apt-get install pandoc texlive lmodern
cd build/<year> && pandoc -c stylesheet.css -o ../../kalender_<year>.pdf *.html
```

## Development

Run the test suite:

```bash
uv run pytest
```

Tests cover Easter calculation, public holiday generation, ICS parsing, and CSV import. The CI pipeline runs on every push via GitHub Actions (`.github/workflows/ci.yml`).
