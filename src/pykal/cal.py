from __future__ import annotations

import csv
import datetime
import logging
from calendar import Calendar
from pathlib import Path
from shutil import copy
from typing import NamedTuple

import ephem

from pykal.html import DivTag, HtmlFile, HtmlTag, RawDivTag
from pykal.icalendar import ICalEvent, ICalendar


def west_easter(year: int) -> datetime.date:
    """Return the date of Easter Sunday for the given year (Gregorian, >= 1583).

    Algorithm from: https://blog.ynfonatic.de/2023/01/28/calculating-the-date-of-easter-in-python.html
    """
    if not isinstance(year, int):
        raise TypeError("year must be an int")
    if year < 1583:
        raise ValueError("year must be >= 1583 (Gregorian calendar)")

    _, a = divmod(year, 19)
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f, _ = divmod(b + 8, 25)
    g, _ = divmod(b - f + 1, 3)
    _, h = divmod(19 * a + b - d - g + 15, 30)
    i, k = divmod(c, 4)
    _, ll = divmod(32 + 2 * e + 2 * i - h - k, 7)
    m, _ = divmod(a + 11 * h + 22 * ll, 451)
    n, p = divmod(h + ll - 7 * m + 114, 31)
    return datetime.date(year, n, p + 1)


class PublicHoliday(NamedTuple):
    date: datetime.date
    name: str
    is_official: bool  # True = red-letter day (gesetzlicher Feiertag)


def _build_public_holidays(year: int) -> list[PublicHoliday]:
    """Return the list of public and notable days for *year* (Bavaria / Augsburg region)."""
    easter = west_easter(year)
    christmas = datetime.date(year, 12, 25)
    # 4th Advent = last Sunday before or on Christmas
    advent4 = christmas - datetime.timedelta(days=(christmas.weekday() + 1) % 7)

    def d(month: int, day: int) -> datetime.date:
        return datetime.date(year, month, day)

    def e_offset(days: int) -> datetime.date:
        return easter + datetime.timedelta(days=days)

    # Erntedank: first Sunday in October
    oct1 = d(10, 1)
    erntedank = oct1 + datetime.timedelta(days=(6 - oct1.weekday()) % 7)

    # Muttertag: second Sunday in May
    may1 = d(5, 1)
    muttertag = may1 + datetime.timedelta(days=(6 - may1.weekday()) % 7 + 7)

    return [
        PublicHoliday(e_offset(-48), "Rosenmontag",              False),
        PublicHoliday(e_offset(-47), "Fastnacht",                 False),
        PublicHoliday(e_offset(-46), "Aschermittwoch",            False),
        PublicHoliday(e_offset( -7), "Palmsonntag",               True),
        PublicHoliday(e_offset( -3), "Gründonnerstag",            False),
        PublicHoliday(e_offset( -2), "Karfreitag",                True),
        PublicHoliday(e_offset( -1), "Karsamstag",                False),
        PublicHoliday(e_offset(  0), "Ostersonntag",              True),
        PublicHoliday(e_offset(  1), "Ostermontag",               True),
        PublicHoliday(e_offset( 39), "Christi Himmelfahrt",       True),
        PublicHoliday(e_offset( 49), "Pfingstsonntag",            True),
        PublicHoliday(e_offset( 50), "Pfingstmontag",             True),
        PublicHoliday(e_offset( 60), "Fronleichnam",              True),
        PublicHoliday(d( 1,  1),     "Neujahr",                   True),
        PublicHoliday(d( 1,  6),     "Hl. Drei Könige",           True),
        PublicHoliday(d( 2,  2),     "Lichtmess",                 False),
        PublicHoliday(d( 2, 14),     "Valentinstag",              False),
        PublicHoliday(d( 5,  1),     "Tag der Arbeit",            True),
        PublicHoliday(d( 8,  8),     "Augsburger Friedensfest",   False),
        PublicHoliday(d( 8, 15),     "Mariä Himmelfahrt",         True),
        PublicHoliday(erntedank,     "Erntedank",                 False),
        PublicHoliday(d(11,  1),     "Allerheiligen",             True),
        PublicHoliday(d(11,  2),     "Allerseelen",               False),
        PublicHoliday(d(11, 11),     "St. Martin",                False),
        PublicHoliday(advent4 - datetime.timedelta(32), "Buß- und Bettag",  False),
        PublicHoliday(advent4 - datetime.timedelta(28), "Totensonntag",     False),
        PublicHoliday(advent4 - datetime.timedelta(21), "1. Advent",        False),
        PublicHoliday(d(12,  6),     "Nikolaus",                  False),
        PublicHoliday(advent4 - datetime.timedelta(14), "2. Advent",        False),
        PublicHoliday(advent4 - datetime.timedelta( 7), "3. Advent",        False),
        PublicHoliday(advent4,                          "4. Advent",        False),
        PublicHoliday(d(12, 24),     "Hl. Abend",                 False),
        PublicHoliday(d(12, 25),     "1. Weihnachtsfeiertag",     True),
        PublicHoliday(d(12, 26),     "2. Weihnachtsfeiertag",     True),
        PublicHoliday(d(12, 31),     "Silvester",                 False),
        PublicHoliday(muttertag,     "Muttertag",                 False),
    ]


class Day:
    WEEKDAY_NAMES = (None, "Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")

    def __init__(self, weekday: int, day_of_month: int, calendar_week: int) -> None:
        self.weekday = weekday  # 1=Mo … 7=So (ISO)
        self.weekday_string = self.WEEKDAY_NAMES[weekday]
        self.day_of_month = day_of_month
        self.calendar_week = calendar_week
        self.events: list[ICalEvent] = []
        self.birthdays: list[ICalEvent] = []
        self.is_holiday = False        # school holiday
        self.is_public_holiday = False # red-letter day
        self.garbage_collection = ""

    def add_event(self, event: ICalEvent) -> None:
        self.events.append(event)

    def add_birthday(self, event: ICalEvent) -> None:
        self.birthdays.append(event)


_GARBAGE_ABBREV: dict[str, str] = {
    "": "",
    "Restmüll": "RM",
    "Gelber": "GS",
    "Papiertonne": "PT",
    "Schadstoffmobil": "SM",
    "Biotonne": "BT",
}

_MONTH_NAMES = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)


class PyKal:
    """Calendar generator for a single year."""

    def __init__(self, year: int) -> None:
        self.year = year
        # schedule[month_idx][day_idx] — month_idx 0=Jan, day_idx 0=1st
        self.schedule: list[list[Day]] = self._build_schedule()
        self._apply_public_holidays()

    # ------------------------------------------------------------------
    # Schedule construction
    # ------------------------------------------------------------------

    def _build_schedule(self) -> list[list[Day]]:
        cal = Calendar()
        schedule = []
        for month in range(1, 13):
            days = []
            for week in cal.monthdatescalendar(self.year, month):
                for date in week:
                    if date.month == month:
                        iso = date.isocalendar()
                        days.append(Day(iso[2], date.day, iso[1]))
            schedule.append(days)
        return schedule

    def _apply_public_holidays(self) -> None:
        for holiday in _build_public_holidays(self.year):
            if holiday.date.year != self.year:
                continue
            day = self.schedule[holiday.date.month - 1][holiday.date.day - 1]
            day.is_public_holiday = holiday.is_official
            event = ICalEvent()
            event.set_date_start(holiday.date.strftime("%Y%m%d"))
            event.set_summary(holiday.name)
            day.add_event(event)

    # ------------------------------------------------------------------
    # Data import
    # ------------------------------------------------------------------

    def parse_ics_file(
        self,
        file_path: Path | str,
        category: str = "",
        day_offset: int = 0,
    ) -> None:
        logging.info("parsing ICS: %s", file_path)
        cal = ICalendar(file_path)
        cal.read(day_offset)
        for event in cal.event_list:
            if category:
                event.set_categories(category)
            if event.date_end is None:
                event.date_end = event.date_start
            date = event.date_start
            while date is not None and date <= event.date_end:
                if date.year != self.year:
                    date += datetime.timedelta(days=1)
                    continue
                day = self.schedule[date.month - 1][date.day - 1]
                if event.categories == "holiday":
                    day.is_holiday = True
                elif event.categories == "garbage":
                    day.garbage_collection = event.summary.split()[0]
                    break  # garbage spans are treated as single-day
                else:
                    day.add_event(event)
                date += datetime.timedelta(days=1)
            logging.debug("%s: %s", event.date_start, event.summary)

    def parse_birthday_csv_file(self, file_path: Path | str) -> None:
        with open(file_path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter="\t", quotechar='"')
            for row in reader:
                if len(row) < 3:
                    continue
                event = ICalEvent()
                event.set_date_start(row[0].replace("-", ""))
                event.set_summary("GT: " + row[1])
                event.set_status(row[2].strip().lower() == "true")
                self._add_birthday(event)

    def parse_name_day_csv_file(self, file_path: Path | str) -> None:
        with open(file_path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter="\t", quotechar='"')
            for row in reader:
                event = ICalEvent()
                event.set_date_start(f"{self.year}" + row[0].replace("-", ""))
                event.set_summary("NT: " + row[1])
                self._add_event(event)

    def parse_event_csv_file(self, file_path: Path | str) -> None:
        try:
            with open(file_path, encoding="utf-8", newline="") as f:
                reader = csv.reader(f, delimiter="\t", quotechar='"')
                for row in reader:
                    event = ICalEvent()
                    event.set_date_start(row[0].replace("-", ""))
                    event.set_summary(row[1])
                    self._add_event(event)
        except OSError:
            logging.warning("could not open event file: %s", file_path)

    def _add_event(self, event: ICalEvent) -> None:
        if event.date_start and event.date_start.year == self.year:
            self.schedule[event.date_start.month - 1][event.date_start.day - 1].add_event(event)

    def _add_birthday(self, event: ICalEvent) -> None:
        if event.date_start:
            self.schedule[event.date_start.month - 1][event.date_start.day - 1].add_birthday(event)

    # ------------------------------------------------------------------
    # Moon phase
    # ------------------------------------------------------------------

    def _moon_phase_img(self, month: int, day_of_month: int) -> str:
        today = datetime.date(self.year, month, day_of_month)
        yesterday = today - datetime.timedelta(days=1)

        moon_today = ephem.Moon(today.strftime("%Y/%m/%d"))
        phase_today = int(moon_today.moon_phase * 15) + 1

        moon_yesterday = ephem.Moon(yesterday.strftime("%Y/%m/%d"))
        phase_yesterday = int(moon_yesterday.moon_phase * 15) + 1

        phase = phase_today if phase_today >= phase_yesterday else 30 - phase_today
        phase = min(max(phase, 1), 30)
        return f'<img src="moon_phase_{phase:02d}.svg"/>'

    # ------------------------------------------------------------------
    # HTML output
    # ------------------------------------------------------------------

    def save_to_html(self, build_dir: Path, data_common_dir: Path) -> None:
        year_build_dir = build_dir / str(self.year)
        year_build_dir.mkdir(parents=True, exist_ok=True)

        # Copy moon phase SVGs so the build folder is self-contained
        # (required for pandoc PDF generation and browser use without a server)
        for svg in data_common_dir.parent.glob("moon_phase_*.svg"):
            copy(svg, year_build_dir)

        for month_idx, month_days in enumerate(self.schedule):
            month_name = _MONTH_NAMES[month_idx]
            title = f"{month_name}_{self.year}"
            html_file = HtmlFile(title, year_build_dir)
            html_file.add_tag(HtmlTag("h1", title))

            for day in month_days:
                day_tag = DivTag(css_class="day")

                # Weekday label
                weekday_class = "week_day"
                if day.weekday == 6:
                    day_tag.add_class("saturday")
                elif day.weekday == 7:
                    day_tag.add_class("sunday")
                if day.is_public_holiday:
                    weekday_class += " public_holiday"
                day_tag.add_sub_tag(DivTag(day.weekday_string or "", weekday_class))

                # Day-of-month number
                dom_class = "day_of_month"
                if day.is_holiday:
                    dom_class += " holiday"
                day_tag.add_sub_tag(DivTag(str(day.day_of_month), dom_class))

                # Moon phase image (raw HTML, not escaped)
                moon_html = self._moon_phase_img(month_idx + 1, day.day_of_month)
                day_tag.add_sub_tag(RawDivTag(moon_html, "meta_info"))

                # Calendar week (shown on Mondays only)
                kw_text = f"KW{day.calendar_week}" if day.weekday == 1 else ""
                day_tag.add_sub_tag(DivTag(kw_text, "calendar_week"))

                # Birthdays
                birthday_block = DivTag(css_class="birthday_block")
                for event in day.birthdays:
                    summary = event.summary + event.get_age_string(self.year)
                    birthday_block.add_sub_tag(DivTag(summary, "birthday"))
                day_tag.add_sub_tag(birthday_block)

                # Events
                event_block = DivTag(css_class="event_block")
                for event in day.events:
                    event_block.add_sub_tag(DivTag(event.summary, "event"))
                day_tag.add_sub_tag(event_block)

                # Garbage collection
                abbrev = _GARBAGE_ABBREV.get(day.garbage_collection, "")
                garbage_class = "garbage"
                if abbrev:
                    garbage_class += " " + abbrev
                day_tag.add_sub_tag(DivTag(abbrev, garbage_class))

                html_file.add_tag(day_tag)

            html_file.save()

        copy(data_common_dir / "stylesheet.css", year_build_dir)
        logging.info("saved HTML calendar to %s", year_build_dir)
