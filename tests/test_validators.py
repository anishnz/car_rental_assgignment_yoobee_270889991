"""
tests/test_validators.py
===========================

WHAT THIS FILE IS FOR:
Automated tests for utils/validators.py - the functions every user-typed value in
this project passes through. These tests need NO database at all (validators are
pure functions of their input), so none of them use the clean_database fixture.

WHY WE TEST BOTH "GOOD" AND "BAD" INPUT:
A validator has really done its job only if it does two things correctly: accept
and correctly convert good input, AND reject bad input with a clear error. Testing
only the happy path would miss bugs where, for example, a negative number or an
empty string slips through unnoticed - exactly the kind of bug validators exist to
prevent.
"""

from datetime import date

import pytest

from utils import validators


def test_validate_non_empty_accepts_and_trims_text():
    assert validators.validate_non_empty("  Anish  ", "Name") == "Anish"


def test_validate_non_empty_rejects_blank_text():
    with pytest.raises(ValueError):
        validators.validate_non_empty("   ", "Name")


def test_validate_email_accepts_a_reasonable_address():
    assert validators.validate_email("anish@example.com") == "anish@example.com"


@pytest.mark.parametrize("bad_email", ["not-an-email", "missing-domain@", "@missing-local.com", ""])
def test_validate_email_rejects_obviously_wrong_addresses(bad_email):
    with pytest.raises(ValueError):
        validators.validate_email(bad_email)


def test_validate_phone_accepts_a_reasonable_number():
    assert validators.validate_phone("+64 21 123 4567") == "+64 21 123 4567"


@pytest.mark.parametrize("bad_phone", ["123", "not-a-number", ""])
def test_validate_phone_rejects_too_short_or_non_numeric(bad_phone):
    with pytest.raises(ValueError):
        validators.validate_phone(bad_phone)


def test_validate_date_parses_a_correct_date():
    assert validators.validate_date("2026-09-20") == date(2026, 9, 20)


@pytest.mark.parametrize("bad_date", ["20-09-2026", "2026/09/20", "not-a-date", ""])
def test_validate_date_rejects_wrong_format(bad_date):
    with pytest.raises(ValueError):
        validators.validate_date(bad_date)


def test_validate_date_range_accepts_return_after_pickup():
    pickup, ret = validators.validate_date_range("2026-09-20", "2026-09-23")
    assert pickup == date(2026, 9, 20)
    assert ret == date(2026, 9, 23)


def test_validate_date_range_rejects_return_on_or_before_pickup():
    with pytest.raises(ValueError):
        validators.validate_date_range("2026-09-20", "2026-09-20")
    with pytest.raises(ValueError):
        validators.validate_date_range("2026-09-20", "2026-09-19")


def test_validate_positive_number_accepts_a_positive_value():
    assert validators.validate_positive_number("65.50", "Daily rate") == 65.50


@pytest.mark.parametrize("bad_value", ["0", "-5", "not-a-number", ""])
def test_validate_positive_number_rejects_zero_negative_or_non_numeric(bad_value):
    with pytest.raises(ValueError):
        validators.validate_positive_number(bad_value, "Daily rate")


def test_validate_non_negative_number_accepts_zero():
    assert validators.validate_non_negative_number("0", "Distance") == 0.0


def test_validate_non_negative_number_rejects_negative():
    with pytest.raises(ValueError):
        validators.validate_non_negative_number("-1", "Distance")


def test_validate_year_accepts_a_reasonable_year():
    assert validators.validate_year("2022") == 2022


@pytest.mark.parametrize("bad_year", ["1899", "3000", "not-a-year"])
def test_validate_year_rejects_out_of_range_or_non_numeric(bad_year):
    with pytest.raises(ValueError):
        validators.validate_year(bad_year)


def test_validate_positive_int_accepts_a_whole_number():
    assert validators.validate_positive_int("5", "Seats") == 5


@pytest.mark.parametrize("bad_value", ["0", "-2", "4.5", "five"])
def test_validate_positive_int_rejects_zero_negative_fraction_or_text(bad_value):
    with pytest.raises(ValueError):
        validators.validate_positive_int(bad_value, "Seats")


def test_validate_choice_accepts_a_listed_option():
    assert validators.validate_choice("Sedan", ["Sedan", "SUV"], "Vehicle type") == "Sedan"


def test_validate_choice_rejects_an_unlisted_option():
    with pytest.raises(ValueError):
        validators.validate_choice("Spaceship", ["Sedan", "SUV"], "Vehicle type")
