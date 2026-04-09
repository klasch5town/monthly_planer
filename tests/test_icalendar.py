"""Tests for pykal.icalendar — ICS parsing logic."""
from __future__ import annotations

import datetime

import pytest

from pykal.icalendar import ICalEvent, ICalendar


# ---------------------------------------------------------------------------
# ICalEvent
# ---------------------------------------------------------------------------

class TestICalEvent:
    def test_set_date_start(self) -> None:
        event = ICalEvent()
        event.set_date_start("20260415")
        assert event.date_start == datetime.date(2026, 4, 15)

    def test_shift_event(self) -> None:
        event = ICalEvent()
        event.set_date_start("20260415")
        event.set_date_end("20260417")
        event.shift_event(-1)
        assert event.date_start == datetime.date(2026, 4, 14)
        assert event.date_end == datetime.date(2026, 4, 16)

    def test_get_age_string_known_status(self) -> None:
        event = ICalEvent()
        event.set_date_start("19800415")
        event.set_status(True)
        age_str = event.get_age_string(2026)
        assert "46 J" in age_str
        assert "??" not in age_str

    def test_get_age_string_unknown_status(self) -> None:
        event = ICalEvent()
        event.set_date_start("19800415")
        event.set_status(False)
        age_str = event.get_age_string(2026)
        assert "??" in age_str


# ---------------------------------------------------------------------------
# ICalendar file parsing
# ---------------------------------------------------------------------------

_MINIMAL_ICS = """\
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20260401
DTEND:20260403
SUMMARY:Test Event
END:VEVENT
END:VCALENDAR
"""

_MULTI_EVENT_ICS = """\
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20260601
SUMMARY:June Event
END:VEVENT
BEGIN:VEVENT
DTSTART;TZID=Europe/Berlin:20261201T000000
DTEND;TZID=Europe/Berlin:20261202T000000
SUMMARY:December Event
END:VEVENT
END:VCALENDAR
"""


class TestICalendar:
    def test_reads_single_event(self, tmp_path) -> None:
        f = tmp_path / "test.ics"
        f.write_text(_MINIMAL_ICS, encoding="utf-8")
        cal = ICalendar(f)
        cal.read()
        assert len(cal.event_list) == 1
        assert cal.event_list[0].summary == "Test Event"
        assert cal.event_list[0].date_start == datetime.date(2026, 4, 1)
        assert cal.event_list[0].date_end == datetime.date(2026, 4, 3)

    def test_reads_multiple_events(self, tmp_path) -> None:
        f = tmp_path / "multi.ics"
        f.write_text(_MULTI_EVENT_ICS, encoding="utf-8")
        cal = ICalendar(f)
        cal.read()
        assert len(cal.event_list) == 2
        summaries = {e.summary for e in cal.event_list}
        assert "June Event" in summaries
        assert "December Event" in summaries

    def test_day_offset_applied(self, tmp_path) -> None:
        f = tmp_path / "test.ics"
        f.write_text(_MINIMAL_ICS, encoding="utf-8")
        cal = ICalendar(f)
        cal.read(day_offset=-1)
        # DTEND was 20260403, shifted by -1 → 20260402
        assert cal.event_list[0].date_end == datetime.date(2026, 4, 2)

    def test_missing_file_returns_empty(self, tmp_path) -> None:
        cal = ICalendar(tmp_path / "nonexistent.ics")
        cal.read()
        assert cal.event_list == []

    def test_dtend_defaults_to_dtstart_when_missing(self, tmp_path) -> None:
        ics = """\
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20260710
SUMMARY:No end date
END:VEVENT
END:VCALENDAR
"""
        f = tmp_path / "noend.ics"
        f.write_text(ics, encoding="utf-8")
        cal = ICalendar(f)
        cal.read()
        event = cal.event_list[0]
        assert event.date_end == event.date_start
