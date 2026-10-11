from datetime import date

from occasions import next_occurrence, days_until


def test_non_recurring_future_date_returns_itself():
    assert next_occurrence(date(2026, 12, 1), False, date(2026, 10, 8)) == date(2026, 12, 1)


def test_non_recurring_past_date_returns_none():
    assert next_occurrence(date(2026, 3, 1), False, date(2026, 10, 8)) is None


def test_recurring_date_later_this_year():
    assert next_occurrence(date(1999, 12, 1), True, date(2026, 10, 8)) == date(2026, 12, 1)


def test_recurring_date_already_passed_rolls_to_next_year():
    assert next_occurrence(date(1999, 3, 1), True, date(2026, 10, 8)) == date(2027, 3, 1)


def test_occasion_today_counts_as_today():
    assert next_occurrence(date(1999, 10, 8), True, date(2026, 10, 8)) == date(2026, 10, 8)


def test_leap_day_falls_back_in_non_leap_year():
    assert next_occurrence(date(2000, 2, 29), True, date(2027, 1, 1)) == date(2027, 3, 1)


def test_leap_day_kept_in_leap_year():
    assert next_occurrence(date(2000, 2, 29), True, date(2028, 1, 1)) == date(2028, 2, 29)


def test_days_until_counts_forward():
    assert days_until(date(2026, 10, 15), date(2026, 10, 8)) == 7


def test_days_until_is_zero_on_the_day():
    assert days_until(date(2026, 10, 8), date(2026, 10, 8)) == 0

def test_leap_day_in_current_non_leap_year_after_fallback_date():
    assert next_occurrence(date(2000, 2, 29), True, date(2027, 6, 1)) == date(2028, 2, 29)