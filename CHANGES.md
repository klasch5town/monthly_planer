# Revision History

## 2.0.0 — 2026-04-10

### New Features
- Web interface (`pykal-web`) — Flask/Jinja2 multi-page app with dashboard, events, birthdays, and settings pages
- Dashboard triggers HTML calendar generation and shows live data source status
- Birthdays page: add, edit, delete entries in `perso/` CSV directly from the browser
- Events page: browse all loaded events; add and delete custom one-off events
- Settings page: edit year, paths, ICS source file assignments, and calendar colors
- Calendar colors are editable at stylesheet level via color pickers in the settings page

### Changes
- Complete project rewrite to modern Python package layout (`src/` layout, `pyproject.toml`, `uv`)
- HTML calendar pages now rendered via Jinja2 templates instead of a custom tag-builder
- Configuration moved from hardcoded values into `pykal.yaml`
- Command-line interface replaced with Click (`pykal` entry point)
- Generation logic extracted into `generate.py`, shared by CLI and web interface
- Moon phase images integrated into calendar output
- Public and notable holidays for Bavaria/Augsburg calculated internally (no external ICS needed)
- `perso/` and `build/` directories excluded from version control

### Fixes
- GitHub Actions CI workflow aligned with renamed default branch (`main`)

---

## 1.x

Initial development versions. Learning project — no structured release history recorded.
