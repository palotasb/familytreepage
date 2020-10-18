from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional, Tuple


@dataclass
class Date:
    text: str

    def order_key(self) -> date:
        return date.max

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[Date], str]:
        date_c, rest = DateCalendar.parse(text)
        if date_c:
            return date_c, rest

        date_approx, rest = DateApprox.parse(text)
        if date_approx:
            return date_approx, rest

        date_range, rest = DateRange.parse(text)
        if date_range:
            return date_range, rest

        # else:
        return None, text


@dataclass
class DateCalendar(Date):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateCalendar], str]:
        date, rest = DateCalendarGregorian.parse(text)
        if date:
            return date, rest
        else:
            return None, text


@dataclass
class DateCalendarWithEscape(DateCalendar):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateCalendarWithEscape], str]:
        return None, text


def _parse_year(text: str) -> Tuple[Optional[int], str]:
    match = re.match(r"\d\d\d\d?", text)  # 3-4 digits per GEDCOM spec
    if match:
        return int(match.group()), text[match.end() :]
    else:
        return None, text


assert _parse_year("") == (None, "")
assert _parse_year("12") == (None, "12")
assert _parse_year("123") == (123, "")
assert _parse_year(" 123") == (None, " 123")
assert _parse_year("123x") == (123, "x")


def _parse_day(text: str) -> Tuple[Optional[int], str]:
    match = re.match(r"\d\d?", text)  # 1-2 digits per GEDCOM spec
    if match:
        return int(match.group()), text[match.end() :]
    else:
        return None, text


def _consume(text: str, expected: str) -> Tuple[Optional[str], str]:
    n = len(expected)
    if text[0:n] == expected:
        return expected, text[n:]
    else:
        return None, text


def _parse_space(text: str) -> Tuple[Optional[str], str]:
    return _consume(text, " ")


class Month(Enum):
    JAN = "JAN"
    FEB = "FEB"
    MAR = "MAR"
    APR = "APR"
    MAY = "MAY"
    JUN = "JUN"
    JUL = "JUL"
    AUG = "AUG"
    SEP = "SEP"
    OCT = "OCT"
    NOV = "NOV"
    DEC = "DEC"

    def __int__(self) -> int:
        for index, month in enumerate(Month, 1):
            if month == self:
                return index
        assert False, "uncreachable"

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[Month], str]:
        try:
            return Month(text[0:3]), text[3:]
        except:
            return None, text


assert int(Month.JAN) == 1
assert int(Month.DEC) == 12


def _success(*items) -> bool:
    return all(map(lambda item: item is not None, items))


@dataclass
class DateCalendarGregorian(DateCalendarWithEscape):
    year: Optional[int]
    month: Optional[Month]
    day: Optional[int]

    def order_key(self) -> date:
        return date(
            self.year or date.max.year,
            int(self.month) if self.month else 1,
            self.day or 1,
        )

    def __str__(self) -> str:
        return f"{self.year or '–'}. {int(self.month) if self.month else '–'}. {self.day or '–'}."

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateCalendarGregorian], str]:
        # [ <YEAR> [ + space + <BEFORE_COMMON_ERA> ]
        # | <MONTH> + space + <YEAR>
        # | <DAY> + space + <MONTH> + space + <YEAR>
        # | <DAY> + space + <MONTH>
        # | <MONTH> + space + <DUAL_STYLE_YEAR>
        # | <DAY> + space + <MONTH> + space + <DUAL_STYLE_YEAR>
        # ]

        # <YEAR> [ + space + <BEFORE_COMMON_ERA> ]
        year, rest = _parse_year(text)
        if year:
            return cls(text=text, year=year, month=None, day=None), rest

        # TODO <YEAR> [ + space + <BEFORE_COMMON_ERA> ]

        # <MONTH> + space + <YEAR>
        month, rest = Month.parse(text)
        space, rest = _parse_space(rest)
        year, rest = _parse_year(rest)
        if _success(month, space, year):
            return cls(text=text, year=year, month=month, day=None), rest

        # <DAY> + space + <MONTH> + space + <YEAR>
        day, rest = _parse_day(text)
        space1, rest = _parse_space(rest)
        month, rest = Month.parse(rest)
        space2, rest = _parse_space(rest)
        year, rest = _parse_year(rest)
        if _success(day, space1, month, space2, year):
            return cls(text=text, year=year, month=month, day=day), rest

        # <DAY> + space + <MONTH>
        day, rest = _parse_day(text)
        space, rest = _parse_space(rest)
        month, rest = Month.parse(rest)
        if _success(day, space, month):
            return cls(text=text, year=None, month=month, day=day), rest

        # TODO <MONTH> + space + <DUAL_STYLE_YEAR>

        # TODO <DAY> + space + <MONTH> + space + <DUAL_STYLE_YEAR>

        return None, text


@dataclass
class DateCalendarJulian(DateCalendarWithEscape):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateCalendarJulian], str]:
        return None, text


@dataclass
class DateCalendarHebrew(DateCalendarWithEscape):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateCalendarHebrew], str]:
        return None, text


@dataclass
class DateCalendarFrenchRevolutionary(DateCalendarWithEscape):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateCalendarFrenchRevolutionary], str]:
        return None, text


@dataclass
class DatePeriod(Date):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DatePeriod], str]:
        return None, text


@dataclass
class DatePeriodFrom(DatePeriod):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DatePeriodFrom], str]:
        return None, text


@dataclass
class DatePeriodTo(DatePeriod):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DatePeriodTo], str]:
        return None, text


@dataclass
class DatePeriodFromTo(DatePeriod):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DatePeriodFromTo], str]:
        return None, text


@dataclass
class DateRange(Date):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateRange], str]:
        date_before, rest = DateRangeBefore.parse(text)
        if date_before:
            return date_before, rest

        date_after, rest = DateRangeAfter.parse(text)
        if date_after:
            return date_after, rest

        date_between, rest = DateRangeBetween.parse(text)
        if date_between:
            return date_between, rest

        # else:
        return None, text


@dataclass
class DateRangeBefore(DateRange):
    date: DateCalendar

    def order_key(self) -> date:
        return self.date.order_key()

    def __str__(self) -> str:
        return f"< {self.date}"

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateRangeBefore], str]:
        bef, rest = _consume(text, "BEF ")
        date, rest = DateCalendar.parse(rest)
        if _success(bef, date):
            assert isinstance(date, DateCalendar)
            return cls(text=text, date=date), rest

        # else:
        return None, text


@dataclass
class DateRangeAfter(DateRange):
    date: DateCalendar

    def order_key(self) -> date:
        return self.date.order_key()

    def __str__(self) -> str:
        return f"{self.date} <"

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateRangeAfter], str]:
        aft, rest = _consume(text, "AFT ")
        date, rest = DateCalendar.parse(rest)
        if _success(aft, date):
            assert isinstance(date, DateCalendar)
            return cls(text=text, date=date), rest

        # else:
        return None, text


@dataclass
class DateRangeBetween(DateRange):
    date_1: DateCalendar
    date_2: DateCalendar

    def order_key(self) -> date:
        a = self.date_1.order_key()
        b = self.date_2.order_key()
        return a + (b - a) // 2

    def __str__(self) -> str:
        return f"{self.date_1} < ? < {self.date_2}"

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateRangeBetween], str]:
        bet, rest = _consume(text, "BET ")
        date_1, rest = DateCalendar.parse(rest)
        and_, rest = _consume(rest, " AND ")
        date_2, rest = DateCalendar.parse(rest)
        if _success(bet, date_1, and_, date_2):
            assert isinstance(date_1, DateCalendar)
            assert isinstance(date_2, DateCalendar)
            return cls(text=text, date_1=date_1, date_2=date_2), rest

        # else:
        return None, text


@dataclass
class DateApprox(Date):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateApprox], str]:
        date_abt, rest = DateApproxAbout.parse(text)
        if date_abt:
            return date_abt, rest

        date_calc, rest = DateApproxCalculated.parse(text)
        if date_calc:
            return date_calc, rest

        date_est, rest = DateApproxEstimated.parse(text)
        if date_est:
            return date_est, rest

        # else:
        return None, text


@dataclass
class DateApproxAbout(DateApprox):
    date: DateCalendar

    def order_key(self) -> date:
        return self.date.order_key()

    def __str__(self) -> str:
        return f"~ {self.date}"

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateApproxAbout], str]:
        abt, rest = _consume(text, "ABT ")
        date, rest = DateCalendar.parse(rest)
        if _success(abt, date):
            assert isinstance(date, DateCalendar)
            return cls(text=text, date=date), rest

        # else:
        return None, text


@dataclass
class DateApproxCalculated(DateApprox):
    date: DateCalendar

    def order_key(self) -> date:
        return self.date.order_key()

    def __str__(self) -> str:
        return f"+/- {self.date}"

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateApproxCalculated], str]:
        cal, rest = _consume(text, "CAL ")
        date, rest = DateCalendar.parse(rest)
        if _success(cal, date):
            assert isinstance(date, DateCalendar)
            return cls(text=text, date=date), rest

        # else:
        return None, text


@dataclass
class DateApproxEstimated(DateApprox):
    date: DateCalendar

    def order_key(self) -> date:
        return self.date.order_key()

    def __str__(self) -> str:
        return f"est. ~ {self.date}"

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateApproxEstimated], str]:
        est, rest = _consume(text, "EST ")
        date, rest = DateCalendar.parse(rest)
        if _success(est, date):
            assert isinstance(date, DateCalendar)
            return cls(text=text, date=date), rest

        # else:
        return None, text


@dataclass
class DateInterpreted(Date):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DateInterpreted], str]:
        return None, text


@dataclass
class DatePhrase(Date):
    pass

    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[DatePhrase], str]:
        return None, text
