from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True, slots=True)
class ClockAdvance:
    previous_date: date
    current_date: date
    days: int
    month_changed: bool
    year_changed: bool


def advance_clock(current_date: date, days: int) -> ClockAdvance:
    if days <= 0:
        raise ValueError("days must be positive")
    advanced = current_date + timedelta(days=days)
    return ClockAdvance(
        previous_date=current_date,
        current_date=advanced,
        days=days,
        month_changed=(current_date.year, current_date.month) != (advanced.year, advanced.month),
        year_changed=current_date.year != advanced.year,
    )
