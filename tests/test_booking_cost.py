"""
tests/test_booking_cost.py
=============================

WHAT THIS FILE IS FOR:
Automated tests for Booking.calculate_cost() (models/booking.py) - the pricing
formula agreed for this project (BR3/BR3a):

    Total Cost = (Days x Daily Vehicle Rate)
               + (Distance in km x Rate per km)
               + (Days x Driver Daily Rate, only if a driver is requested)

Because calculate_cost() is a @staticmethod that only depends on the values
passed in (no database, no other object state), it can be tested completely in
isolation - exactly the kind of function unit tests are best at catching bugs in.
"""

from datetime import date

import pytest

from models.booking import Booking


def test_calculate_cost_without_a_driver():
    # 3 days x $65/day = $195, plus 80km x $5/km = $400 -> $595 total, no driver cost.
    total = Booking.calculate_cost(
        number_of_days=3, daily_vehicle_rate=65.00, distance_km=80,
        rate_per_km=5.00, driver_required=False,
    )
    assert total == 595.00


def test_calculate_cost_with_a_driver():
    # Matches Booking A from docs/02_seed_data_plan.md: 3 days x $90 = $270,
    # plus 150km x $5/km = $750, plus 3 days x $60/day driver = $180 -> $1200.
    total = Booking.calculate_cost(
        number_of_days=3, daily_vehicle_rate=90.00, distance_km=150,
        rate_per_km=5.00, driver_required=True, daily_driver_rate=60.00,
    )
    assert total == 1200.00


def test_calculate_cost_ignores_driver_rate_when_driver_not_required():
    # Even if a daily_driver_rate is passed in, it must be ignored entirely when
    # driver_required is False - this guards against a bug where the driver cost
    # is added by mistake just because a rate happened to be supplied.
    total = Booking.calculate_cost(
        number_of_days=2, daily_vehicle_rate=65.00, distance_km=80,
        rate_per_km=5.00, driver_required=False, daily_driver_rate=60.00,
    )
    assert total == (2 * 65.00) + (80 * 5.00)


def test_calculate_cost_with_zero_distance():
    # A customer estimating 0 km should simply drop the distance term to zero,
    # not raise an error or behave unexpectedly.
    total = Booking.calculate_cost(
        number_of_days=1, daily_vehicle_rate=100.00, distance_km=0,
        rate_per_km=5.00, driver_required=False,
    )
    assert total == 100.00


def test_number_of_days_property():
    booking = Booking(
        booking_id=1, customer_id=1, vehicle_id=1, driver_id=None,
        pickup_date=date(2026, 9, 20), return_date=date(2026, 9, 23),
        driver_required=0, distance_km=150, rate_per_km_applied=5.00,
        total_amount=1200.00, status="CONFIRMED",
    )
    assert booking.number_of_days == 3


def test_booking_status_transitions_confirm_then_complete():
    booking = Booking(
        booking_id=1, customer_id=1, vehicle_id=1, driver_id=None,
        pickup_date=date(2026, 9, 20), return_date=date(2026, 9, 23),
        driver_required=0, distance_km=150, rate_per_km_applied=5.00,
        total_amount=1200.00, status="PENDING",
    )
    booking.confirm()
    assert booking.status == "CONFIRMED"
    assert booking.frees_up_vehicle() is False

    booking.complete()
    assert booking.status == "COMPLETED"
    assert booking.frees_up_vehicle() is True


def test_booking_cannot_confirm_a_booking_that_is_not_pending():
    booking = Booking(
        booking_id=1, customer_id=1, vehicle_id=1, driver_id=None,
        pickup_date=date(2026, 9, 20), return_date=date(2026, 9, 23),
        driver_required=0, distance_km=150, rate_per_km_applied=5.00,
        total_amount=1200.00, status="CANCELLED",
    )
    with pytest.raises(ValueError):
        booking.confirm()
