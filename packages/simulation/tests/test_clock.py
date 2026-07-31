from datetime import date

import pytest

from genesis_simulation.clock import advance_clock


def test_clock_crosses_month_year_and_leap_day() -> None:
    year = advance_clock(date(2200, 12, 31), 1)
    assert year.current_date == date(2201, 1, 1)
    assert year.month_changed is True
    assert year.year_changed is True

    leap = advance_clock(date(2204, 2, 28), 1)
    assert leap.current_date == date(2204, 2, 29)
    assert leap.month_changed is False
    assert leap.year_changed is False


def test_clock_rejects_non_positive_progression() -> None:
    with pytest.raises(ValueError, match="positive"):
        advance_clock(date(2200, 1, 1), 0)
