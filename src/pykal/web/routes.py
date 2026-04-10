from __future__ import annotations

import csv
import datetime
import logging
import re
from pathlib import Path

import yaml
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from pykal.generate import load_config, load_pykal, run_generation

bp = Blueprint("main", __name__)


# ── Config helpers ────────────────────────────────────────────────────────────

def _config() -> tuple[dict, Path]:
    path: Path = current_app.config["PYKAL_CONFIG_PATH"]
    return load_config(path), path


def _save_config(cfg: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, sort_keys=False)


# ── CSV helpers ───────────────────────────────────────────────────────────────

def _read_birthday_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return [
            {"date": row[0], "name": row[1], "confirmed": row[2].strip().lower() == "true"}
            for row in csv.reader(f, delimiter="\t")
            if len(row) >= 3
        ]


def _write_birthday_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        for r in rows:
            w.writerow([r["date"], r["name"], str(r["confirmed"])])


def _read_event_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return [
            {"date": row[0], "summary": row[1]}
            for row in csv.reader(f, delimiter="\t")
            if len(row) >= 2
        ]


def _write_event_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        for r in rows:
            w.writerow([r["date"], r["summary"]])


# ── CSS color helpers ─────────────────────────────────────────────────────────

COLOR_CLASSES = [
    ("saturday",       "Saturday"),
    ("sunday",         "Sunday"),
    ("holiday",        "School holiday"),
    ("public_holiday", "Public holiday"),
    ("RM",             "Garbage: Restmüll"),
    ("PT",             "Garbage: Papiertonne"),
    ("GS",             "Garbage: Gelber Sack"),
    ("SM",             "Garbage: Schadstoffmobil"),
    ("BT",             "Garbage: Biotonne"),
]


def _read_css_colors(css: str) -> dict[str, str]:
    colors = {}
    for cls, _ in COLOR_CLASSES:
        m = re.search(
            rf'div\.{re.escape(cls)}\s*\{{[^}}]*background-color:\s*([^;}}]+)',
            css, re.DOTALL,
        )
        colors[cls] = m.group(1).strip() if m else ""
    return colors


def _update_css_color(css: str, cls: str, color: str) -> str:
    return re.sub(
        rf'(div\.{re.escape(cls)}\s*\{{[^}}]*background-color:\s*)([^;}}]+)',
        lambda m: m.group(1) + color,
        css, flags=re.DOTALL,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@bp.route("/")
def dashboard():
    cfg, cfg_path = _config()
    year = cfg["year"]
    event_count = birthday_count = 0
    load_error = None
    try:
        kal = load_pykal(cfg, year, cfg_path.parent)
        for month_days in kal.schedule:
            for day in month_days:
                event_count += len(day.events)
                birthday_count += len(day.birthdays)
    except Exception as exc:
        load_error = str(exc)

    raw_sources = cfg.get("sources", {})
    sources = {k: v.format(year=year) if isinstance(v, str) else v for k, v in raw_sources.items()}
    build_dir = cfg_path.parent / cfg["paths"]["build_dir"] / str(year)

    return render_template(
        "dashboard.html",
        year=year,
        event_count=event_count,
        birthday_count=birthday_count,
        load_error=load_error,
        sources=sources,
        build_dir=build_dir,
    )


@bp.route("/generate", methods=["POST"])
def generate():
    cfg, cfg_path = _config()
    year = cfg["year"]
    try:
        run_generation(cfg, year, cfg_path.parent)
        flash(f"Calendar {year} generated successfully.", "success")
    except Exception as exc:
        flash(f"Generation failed: {exc}", "error")
    return redirect(url_for("main.dashboard"))


@bp.route("/events")
def events():
    cfg, cfg_path = _config()
    year = cfg["year"]
    all_events: list[dict] = []
    try:
        kal = load_pykal(cfg, year, cfg_path.parent)
        for month_idx, month_days in enumerate(kal.schedule):
            for day in month_days:
                date = datetime.date(year, month_idx + 1, day.day_of_month)
                for event in day.events:
                    all_events.append({"date": date, "summary": event.summary})
    except Exception as exc:
        flash(f"Could not load events: {exc}", "error")

    perso_dir = cfg_path.parent / cfg["paths"]["perso_dir"]
    custom_events = _read_event_csv(perso_dir / "events.csv")

    return render_template("events.html", year=year, all_events=all_events,
                           custom_events=custom_events)


@bp.route("/events/add", methods=["POST"])
def events_add():
    cfg, cfg_path = _config()
    csv_path = cfg_path.parent / cfg["paths"]["perso_dir"] / "events.csv"
    date = request.form.get("date", "").strip()
    summary = request.form.get("summary", "").strip()
    if date and summary:
        rows = _read_event_csv(csv_path)
        rows.append({"date": date, "summary": summary})
        rows.sort(key=lambda r: r["date"])
        _write_event_csv(csv_path, rows)
        flash("Event added.", "success")
    else:
        flash("Date and summary are required.", "error")
    return redirect(url_for("main.events"))


@bp.route("/events/<int:idx>/delete", methods=["POST"])
def events_delete(idx: int):
    cfg, cfg_path = _config()
    csv_path = cfg_path.parent / cfg["paths"]["perso_dir"] / "events.csv"
    rows = _read_event_csv(csv_path)
    if 0 <= idx < len(rows):
        rows.pop(idx)
        _write_event_csv(csv_path, rows)
        flash("Event deleted.", "success")
    return redirect(url_for("main.events"))


@bp.route("/birthdays")
def birthdays():
    cfg, cfg_path = _config()
    year = cfg["year"]
    birthdays_path = cfg_path.parent / cfg["paths"]["perso_dir"] / cfg["sources"]["birthdays"]
    rows = _read_birthday_csv(birthdays_path)
    for r in rows:
        try:
            birth = datetime.date.fromisoformat(r["date"])
            age = year - birth.year
            r["age"] = str(age) if r["confirmed"] else f"{age} ??"
        except ValueError:
            r["age"] = "?"
    return render_template("birthdays.html", year=year, birthdays=rows)


@bp.route("/birthdays/add", methods=["POST"])
def birthdays_add():
    cfg, cfg_path = _config()
    birthdays_path = cfg_path.parent / cfg["paths"]["perso_dir"] / cfg["sources"]["birthdays"]
    date = request.form.get("date", "").strip()
    name = request.form.get("name", "").strip()
    confirmed = request.form.get("confirmed") == "on"
    if date and name:
        rows = _read_birthday_csv(birthdays_path)
        rows.append({"date": date, "name": name, "confirmed": confirmed})
        rows.sort(key=lambda r: r["date"][5:])  # sort by MM-DD
        _write_birthday_csv(birthdays_path, rows)
        flash(f"Birthday for {name} added.", "success")
    else:
        flash("Date and name are required.", "error")
    return redirect(url_for("main.birthdays"))


@bp.route("/birthdays/<int:idx>/edit", methods=["GET", "POST"])
def birthdays_edit(idx: int):
    cfg, cfg_path = _config()
    birthdays_path = cfg_path.parent / cfg["paths"]["perso_dir"] / cfg["sources"]["birthdays"]
    rows = _read_birthday_csv(birthdays_path)
    if idx < 0 or idx >= len(rows):
        flash("Birthday not found.", "error")
        return redirect(url_for("main.birthdays"))
    if request.method == "POST":
        date = request.form.get("date", "").strip()
        name = request.form.get("name", "").strip()
        confirmed = request.form.get("confirmed") == "on"
        if date and name:
            rows[idx] = {"date": date, "name": name, "confirmed": confirmed}
            _write_birthday_csv(birthdays_path, rows)
            flash(f"Birthday for {name} updated.", "success")
            return redirect(url_for("main.birthdays"))
        flash("Date and name are required.", "error")
    return render_template("birthday_edit.html", idx=idx, row=rows[idx])


@bp.route("/birthdays/<int:idx>/delete", methods=["POST"])
def birthdays_delete(idx: int):
    cfg, cfg_path = _config()
    birthdays_path = cfg_path.parent / cfg["paths"]["perso_dir"] / cfg["sources"]["birthdays"]
    rows = _read_birthday_csv(birthdays_path)
    if 0 <= idx < len(rows):
        name = rows[idx]["name"]
        rows.pop(idx)
        _write_birthday_csv(birthdays_path, rows)
        flash(f"Birthday for {name} deleted.", "success")
    return redirect(url_for("main.birthdays"))


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    cfg, cfg_path = _config()
    css_path = cfg_path.parent / cfg["paths"]["data_dir"] / "common" / "stylesheet.css"
    css_text = css_path.read_text(encoding="utf-8")
    colors = _read_css_colors(css_text)

    if request.method == "POST":
        cfg["year"] = int(request.form.get("year", cfg["year"]))
        cfg["paths"]["data_dir"] = request.form.get("data_dir", cfg["paths"]["data_dir"])
        cfg["paths"]["build_dir"] = request.form.get("build_dir", cfg["paths"]["build_dir"])
        cfg["paths"]["perso_dir"] = request.form.get("perso_dir", cfg["paths"]["perso_dir"])
        for key in cfg.get("sources", {}):
            if key in request.form:
                cfg["sources"][key] = request.form[key]
        _save_config(cfg, cfg_path)

        for cls, _ in COLOR_CLASSES:
            new_color = request.form.get(f"color_{cls}", "").strip()
            if new_color:
                css_text = _update_css_color(css_text, cls, new_color)
        css_path.write_text(css_text, encoding="utf-8")

        flash("Settings saved.", "success")
        return redirect(url_for("main.settings"))

    return render_template("settings.html", cfg=cfg, color_classes=COLOR_CLASSES, colors=colors)
