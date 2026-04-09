"""Tests for pykal.cal — focused on non-trivial logic."""
from __future__ import annotations

import datetime

import pytest

from pykal.cal import PyKal, _build_public_holidays, west_easter


# ---------------------------------------------------------------------------
# west_easter
# ---------------------------------------------------------------------------

class TestWestEaster:
    # Reference dates verified against https://www.timeanddate.com/holidays/
    @pytest.mark.parametrize("year, expected", [
        (2020, datetime.date(2020,  4, 12)),
        (2021, datetime.date(2021,  4,  4)),
        (2022, datetime.date(2022,  4, 17)),
        (2023, datetime.date(2023,  4,  9)),
        (2024, datetime.date(2024,  3, 31)),
        (2025, datetime.date(2025,  4, 20)),
        (2026, datetime.date(2026,  4,  5)),
        # Earliest possible Easter: March 22
        (1818, datetime.date(1818,  3, 22)),
        # Latest possible Easter: April 25
        (1943, datetime.date(1943,  4, 25)),
    ])
    def test_known_dates(self, year: int, expected: datetime.date) -> None:
        assert west_easter(year) == expected

    def test_rejects_non_int(self) -> None:
        with pytest.raises(TypeError):
            west_easter("2026")  # type: ignore[arg-type]

    def test_rejects_pre_gregorian(self) -> None:
        with pytest.raises(ValueError):
            west_easter(1582)


# ---------------------------------------------------------------------------
# _build_public_holidays
# ---------------------------------------------------------------------------

class TestBuildPublicHolidays:
    def test_no_duplicate_dates(self) -> None:
        # Use 2025: in 2026 St. Nikolaus (Dec 6) coincidentally falls on the
        # 2nd Advent Sunday — a real overlap, not a code bug.
        holidays = _build_public_holidays(2025)
        dates = [h.date for h in holidays]
        assert len(dates) == len(set(dates)), "duplicate holiday dates found"

    def test_all_dates_in_year(self) -> None:
        holidays = _build_public_holidays(2026)
        for h in holidays:
            assert h.date.year == 2026, f"{h.name} has date outside 2026: {h.date}"

    def test_erntedank_is_sunday(self) -> None:
        for year in range(2020, 2030):
            holidays = _build_public_holidays(year)
            erntedank = next(h for h in holidays if h.name == "Erntedank")
            assert erntedank.date.weekday() == 6, f"Erntedank is not Sunday in {year}"

    def test_muttertag_is_sunday(self) -> None:
        for year in range(2020, 2030):
            holidays = _build_public_holidays(year)
            muttertag = next(h for h in holidays if h.name == "Muttertag")
            assert muttertag.date.weekday() == 6, f"Muttertag is not Sunday in {year}"

    def test_easter_dependent_holidays_relative_offsets(self) -> None:
        year = 2026
        easter = west_easter(year)
        holidays = {h.name: h.date for h in _build_public_holidays(year)}
        assert holidays["Ostermontag"] == easter + datetime.timedelta(days=1)
        assert holidays["Christi Himmelfahrt"] == easter + datetime.timedelta(days=39)
        assert holidays["Pfingstmontag"] == easter + datetime.timedelta(days=50)
        assert holidays["Fronleichnam"] == easter + datetime.timedelta(days=60)


# ---------------------------------------------------------------------------
# PyKal schedule construction
# ---------------------------------------------------------------------------

class TestPyKalSchedule:
    def test_schedule_has_twelve_months(self) -> None:
        kal = PyKal(2026)
        assert len(kal.schedule) == 12

    def test_each_month_has_correct_day_count(self) -> None:
        import calendar as cal_module
        kal = PyKal(2026)
        for month_idx, days in enumerate(kal.schedule):
            expected = cal_module.monthrange(2026, month_idx + 1)[1]
            assert len(days) == expected, f"month {month_idx + 1}: expected {expected} days"

    def test_public_holidays_applied(self) -> None:
        kal = PyKal(2026)
        # Neujahr is January 1st and is an official holiday
        new_year = kal.schedule[0][0]  # Jan 1
        assert new_year.is_public_holiday

    def test_public_holidays_not_applied_to_unofficial(self) -> None:
        kal = PyKal(2026)
        # Silvester (Dec 31) is in the list but is_official=False
        silvester = kal.schedule[11][30]  # Dec 31
        assert not silvester.is_public_holiday

    def test_public_holiday_events_added(self) -> None:
        kal = PyKal(2026)
        new_year = kal.schedule[0][0]
        summaries = [e.summary for e in new_year.events]
        assert any("Neujahr" in s for s in summaries)


# ---------------------------------------------------------------------------
# PyKal ICS / CSV parsing
# ---------------------------------------------------------------------------

class TestPyKalParsing:
    def test_parse_birthday_csv(self, tmp_path) -> None:
        csv_content = "1980-04-15\tMax Mustermann\tTrue\n1990-12-01\tErika Muster\tFalse\n"
        csv_file = tmp_path / "birthdays.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        kal = PyKal(2026)
        kal.parse_birthday_csv_file(csv_file)

        april_15 = kal.schedule[3][14]  # April 15
        assert any("Max Mustermann" in e.summary for e in april_15.birthdays)
        assert any(e.status is True for e in april_15.birthdays)

        dec_1 = kal.schedule[11][0]  # Dec 1
        assert any("Erika Muster" in e.summary for e in dec_1.birthdays)
        assert any(e.status is False for e in dec_1.birthdays)

    def test_parse_name_day_csv(self, tmp_path) -> None:
        csv_content = "01-15\tFelix\n04-23\tGeorg\n"
        csv_file = tmp_path / "names.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        kal = PyKal(2026)
        kal.parse_name_day_csv_file(csv_file)

        jan_15 = kal.schedule[0][14]
        assert any("Felix" in e.summary for e in jan_15.events)

    def test_parse_event_csv_missing_file_is_silent(self, tmp_path) -> None:
        kal = PyKal(2026)
        # Should not raise, just log a warning
        kal.parse_event_csv_file(tmp_path / "nonexistent.csv")

    def test_parse_ics_file_missing_is_silent(self, tmp_path) -> None:
        kal = PyKal(2026)
        kal.parse_ics_file(tmp_path / "nonexistent.ics", category="holiday")
