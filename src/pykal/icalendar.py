from __future__ import annotations

import datetime
import logging
from pathlib import Path


class ICalEvent:
    def __init__(self) -> None:
        self.summary: str = ""
        self.categories: str = ""
        self.date_start: datetime.date | None = None
        self.date_end: datetime.date | None = None
        self.status: bool | None = None

    @staticmethod
    def _parse_date(date_string: str) -> datetime.date:
        return datetime.date(
            int(date_string[0:4]),
            int(date_string[4:6]),
            int(date_string[6:8]),
        )

    @staticmethod
    def _shift_date(date: datetime.date, day_offset: int) -> datetime.date:
        return date + datetime.timedelta(days=day_offset)

    def set_date_start(self, date_string: str) -> None:
        self.date_start = self._parse_date(date_string)

    def set_date_end(self, date_string: str) -> None:
        self.date_end = self._parse_date(date_string)

    def shift_event(self, day_offset: int) -> None:
        if self.date_start is not None:
            self.date_start = self._shift_date(self.date_start, day_offset)
        if self.date_end is not None:
            self.date_end = self._shift_date(self.date_end, day_offset)

    def set_categories(self, categories: str) -> None:
        self.categories = categories

    def set_summary(self, summary: str) -> None:
        self.summary = summary

    def set_status(self, status: bool) -> None:
        self.status = status

    def get_age_string(self, reference_year: int) -> str:
        if self.date_start is None:
            return ""
        age = (datetime.date(reference_year, 12, 31) - self.date_start).days // 365
        suffix = "" if self.status else " ??"
        return f"{age} J{suffix}"


class ICalendar:
    def __init__(self, file_path: Path | str) -> None:
        self.file_path = Path(file_path)
        self.event_list: list[ICalEvent] = []
        self._day_offset: int = 0
        self._current_item: str | None = None

        self._handlers: dict[str, object] = {
            "BEGIN": self._handle_begin,
            "END": self._handle_end,
            "VERSION": self._handle_version,
            "DTSTART": self._handle_event_start,
            "DTEND": self._handle_event_end,
            "CATEGORIES": self._handle_event_categories,
            "SUMMARY": self._handle_event_summary,
        }

    def read(self, day_offset: int = 0) -> None:
        self._day_offset = day_offset
        try:
            lines = self.file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            logging.warning("could not open: %s", self.file_path)
            return
        for line in lines:
            if line.strip():
                self._evaluate(line)

    def _evaluate(self, line: str) -> None:
        parts = line.split(":", 1)
        if len(parts) < 2:
            return
        tag_part, value = parts
        # Strip optional parameters (e.g. DTSTART;TZID=...)
        tag = tag_part.split(";", 1)[0]
        if tag in self._handlers:
            self._token_value = value
            self._handlers[tag]()

    def _handle_begin(self) -> None:
        self._current_item = self._token_value
        if "VEVENT" in self._token_value:
            self.event_list.append(ICalEvent())

    def _handle_end(self) -> None:
        if self._current_item == "VEVENT" and self.event_list:
            if self.event_list[-1].date_end is None:
                self.event_list[-1].date_end = self.event_list[-1].date_start
        self._current_item = None

    def _handle_version(self) -> None:
        pass  # version info not needed

    def _handle_event_start(self) -> None:
        date_str = self._token_value.split("T", 1)[0]
        if len(date_str) == 8 and self.event_list:
            self.event_list[-1].set_date_start(date_str)

    def _handle_event_end(self) -> None:
        date_str = self._token_value.split("T", 1)[0]
        if len(date_str) == 8 and self.event_list:
            self.event_list[-1].set_date_end(date_str)
            if self._day_offset != 0:
                self.event_list[-1].shift_event(self._day_offset)

    def _handle_event_categories(self) -> None:
        if self.event_list:
            self.event_list[-1].set_categories(self._token_value)

    def _handle_event_summary(self) -> None:
        if self.event_list:
            self.event_list[-1].set_summary(self._token_value)
