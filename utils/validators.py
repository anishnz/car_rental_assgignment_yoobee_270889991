"""
utils/validators.py
====================

WHAT THIS FILE IS FOR:
Every place in this project that reads a value typed by a user (a date, an email, a
price, a name...) checks it using one of the functions below, instead of every menu
screen re-inventing its own checking logic. Keeping validation in one shared file
means the same rule is applied everywhere, and it is easy to test on its own
(see tests/test_validators.py).

HOW THESE FUNCTIONS SIGNAL A PROBLEM (the Python concept demonstrated):
Every validator either returns a clean, converted value (for example, a real `date`
object instead of the raw typed text) or raises a `ValueError` with a clear message
explaining exactly what was wrong. Raising an exception is a deliberate choice here:
it lets the calling code use a single `try/except ValueError` around a whole group of
inputs, catch ANY validation problem in one place, and show the message straight to
the user - instead of writing a separate "if not valid: print error" check after
every single input.
"""

import re
from datetime import datetime, date

import config


DATE_FORMAT = "%Y-%m-%d"  # matches the YYYY-MM-DD convention agreed for this project

# A deliberately simple email pattern - it is NOT meant to catch every technically
# invalid email in existence, only obviously wrong input (missing "@", no domain,
# etc.), which is all an academic demo system needs.
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_non_empty(value: str, field_name: str) -> str:
    """Rejects an empty (or whitespace-only) string for a required field."""
    if value is None or not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")
    return value.strip()


def validate_email(value: str) -> str:
    """Rejects a string that does not look like a reasonable email address."""
    value = validate_non_empty(value, "Email")
    if not _EMAIL_PATTERN.match(value):
        raise ValueError("Invalid email format. Please enter a valid email address.")
    return value


def validate_phone(value: str) -> str:
    """
    Accepts digits, spaces, and the leading '+' some phone numbers use, and requires
    at least 7 digits overall - enough to catch obviously wrong input (letters, or a
    number that's far too short) without being overly strict about country formats.
    """
    value = validate_non_empty(value, "Phone number")
    digits_only = re.sub(r"[^0-9]", "", value)
    if not re.match(r"^\+?[0-9 ]+$", value) or len(digits_only) < 7:
        raise ValueError("Invalid phone number. Please enter digits only (7+ digits).")
    return value


def validate_date(value: str, field_name: str = "Date") -> date:
    """
    Converts a "YYYY-MM-DD" string into a real Python `date` object, or raises a
    ValueError explaining the expected format if the text does not match.
    """
    value = validate_non_empty(value, field_name)
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format, e.g. 2026-09-20.")


def validate_date_range(pickup_str: str, return_str: str) -> tuple:
    """
    Validates a pickup/return date pair together: both must be valid dates (FR11),
    AND the return date must be strictly after the pickup date. Returns the two
    parsed `date` objects so the caller doesn't have to re-parse them.
    """
    pickup_date = validate_date(pickup_str, "Pickup date")
    return_date = validate_date(return_str, "Return date")
    if return_date <= pickup_date:
        raise ValueError("Return date must be after the pickup date.")
    return pickup_date, return_date


def validate_positive_number(value: str, field_name: str) -> float:
    """Converts text to a number and rejects zero or negative values."""
    value = validate_non_empty(value, field_name)
    try:
        number = float(value)
    except ValueError:
        raise ValueError(f"{field_name} must be a number.")
    if number <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return number


def validate_non_negative_number(value: str, field_name: str) -> float:
    """Like validate_positive_number, but allows exactly zero (e.g. 0 km distance)."""
    value = validate_non_empty(value, field_name)
    try:
        number = float(value)
    except ValueError:
        raise ValueError(f"{field_name} must be a number.")
    if number < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return number


def validate_year(value: str) -> int:
    """Rejects a vehicle year that is obviously wrong (too old, or in the future)."""
    value = validate_non_empty(value, "Year")
    try:
        year = int(value)
    except ValueError:
        raise ValueError("Year must be a whole number, e.g. 2022.")
    current_year = date.today().year
    if year < 1980 or year > current_year + 1:
        raise ValueError(f"Year must be between 1980 and {current_year + 1}.")
    return year


def validate_positive_int(value: str, field_name: str) -> int:
    """Converts text to a whole number and rejects zero or negative values."""
    value = validate_non_empty(value, field_name)
    try:
        number = int(value)
    except ValueError:
        raise ValueError(f"{field_name} must be a whole number.")
    if number <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return number


def validate_choice(value: str, valid_choices: list, field_name: str = "Choice") -> str:
    """Rejects a value that isn't one of a fixed set of allowed options."""
    value = validate_non_empty(value, field_name)
    if value not in valid_choices:
        options = ", ".join(valid_choices)
        raise ValueError(f"{field_name} must be one of: {options}.")
    return value
