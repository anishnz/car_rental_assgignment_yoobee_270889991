"""
tests/test_booking_conflict.py
=================================

WHAT THIS FILE IS FOR:
Automated tests for the booking availability/conflict-detection logic in
services/booking_service.py (FR12, BR2) - the rule that stops the same vehicle
being double-booked for overlapping dates. These tests DO need a database (real
rows to check overlaps against), so every test here takes the `clean_database`
fixture from tests/conftest.py as a parameter (even though the test body itself
only needs the fixture's SIDE EFFECT of pointing the app at a fresh, seeded
database - it does not need to use the RentalSystem object the fixture yields).
"""

from datetime import date

import pytest

from services import auth_service, booking_service, vehicle_service


def _login_as_sita():
    """Small helper: logs in as the seeded customer_sita account, used by several
    tests below that need a real Customer object to create a booking with."""
    return auth_service.login("customer_sita", "Customer@123")


def test_check_vehicle_availability_true_for_free_dates(clean_database):
    # The seeded Corolla (vehicle_id 1) only has a COMPLETED booking in early
    # August 2026 - completely different, non-overlapping dates should be free.
    available = booking_service.check_vehicle_availability(1, date(2027, 1, 1), date(2027, 1, 5))
    assert available is True


def test_check_vehicle_availability_false_for_overlapping_dates(clean_database):
    # The seeded Tucson (vehicle_id 2) has a CONFIRMED booking 2026-09-20 to
    # 2026-09-23 (see database/seed_data.py) - a request overlapping any part of
    # that range must be reported as NOT available.
    available = booking_service.check_vehicle_availability(2, date(2026, 9, 21), date(2026, 9, 22))
    assert available is False


def test_create_booking_rejects_overlapping_dates_with_a_clear_message(clean_database):
    customer = _login_as_sita()
    with pytest.raises(ValueError, match="already booked"):
        booking_service.create_booking(
            customer, vehicle_id=2, pickup_date_str="2026-09-21", return_date_str="2026-09-22",
            distance_km_str="50", driver_required=False,
        )


def test_create_booking_succeeds_for_genuinely_free_dates(clean_database):
    customer = _login_as_sita()
    booking = booking_service.create_booking(
        customer, vehicle_id=2, pickup_date_str="2027-01-10", return_date_str="2027-01-12",
        distance_km_str="60", driver_required=False,
    )
    assert booking.status == "PENDING"
    assert booking.total_amount == (2 * 90.00) + (60 * 5.00)

    # Creating the booking should also mark the vehicle BOOKED, so nobody else
    # can take the exact same slot while it awaits admin approval.
    vehicle = vehicle_service.get_vehicle(2)
    assert vehicle.status == "BOOKED"


def test_create_booking_back_to_back_dates_do_not_conflict(clean_database):
    # A booking that starts exactly on the day another one returns should NOT be
    # treated as an overlap (a car can be picked up the same day it is dropped
    # off) - this is what the strict "<" (rather than "<=") comparison in
    # _has_overlapping_booking() is specifically for.
    customer = _login_as_sita()
    booking = booking_service.create_booking(
        customer, vehicle_id=2, pickup_date_str="2026-09-23", return_date_str="2026-09-25",
        distance_km_str="40", driver_required=False,
    )
    assert booking.status == "PENDING"


def test_cancelling_a_booking_frees_the_vehicle_again(clean_database):
    customer = _login_as_sita()
    booking = booking_service.create_booking(
        customer, vehicle_id=1, pickup_date_str="2027-02-01", return_date_str="2027-02-03",
        distance_km_str="20", driver_required=False,
    )
    booking_service.cancel_booking(booking.booking_id)

    vehicle = vehicle_service.get_vehicle(1)
    assert vehicle.status == "AVAILABLE"

    cancelled_booking = booking_service.get_booking(booking.booking_id)
    assert cancelled_booking.status == "CANCELLED"
