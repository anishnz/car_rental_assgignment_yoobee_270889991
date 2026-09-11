"""
tests/test_waitlist_notify.py
================================

WHAT THIS FILE IS FOR:
Automated tests for the Smart Waitlist + Auto-Notify feature (FR16/FR17) - the
custom Observer-pattern feature added to this project to demonstrate an extra
design pattern beyond what the assignment strictly requires. Covers joining a
waitlist, the FIFO notify-only-the-next-customer rule, and that a vehicle with an
empty waitlist notifies nobody (and does not error).
"""

from datetime import date

from models.vehicle import Vehicle
from models.waitlist import WaitlistEntry
from services import auth_service, booking_service, vehicle_service, waitlist_service


def test_join_waitlist_creates_an_unnotified_entry(clean_database):
    customer = auth_service.login("customer_sita", "Customer@123")
    waitlist_service.join_waitlist(customer, vehicle_id=2, requested_pickup_date=date(2026, 10, 1),
                                    requested_return_date=date(2026, 10, 5))

    entries = waitlist_service.list_waitlist_for_vehicle(2)
    matching = [e for e in entries if e.customer_name == "Sita Gurung"]
    assert len(matching) == 1
    assert matching[0].notified is False


def test_notify_next_in_waitlist_notifies_only_the_fifo_head(clean_database):
    # The seeded data already has customer_gita waitlisted for vehicle 2 (the
    # Tucson) - see database/seed_data.py. Add a SECOND, later waitlist entry for
    # the same vehicle, then confirm only the FIRST (oldest) one gets notified.
    customer_sita = auth_service.login("customer_sita", "Customer@123")
    waitlist_service.join_waitlist(customer_sita, vehicle_id=2, requested_pickup_date=date(2026, 10, 1),
                                    requested_return_date=date(2026, 10, 5))

    vehicle = vehicle_service.get_vehicle(2)
    message = waitlist_service.notify_next_in_waitlist(vehicle)

    assert message is not None
    assert "Gita Koirala" in message  # the seeded, earlier entry - not Sita's later one

    entries = waitlist_service.list_waitlist_for_vehicle(2)
    gita_entry = next(e for e in entries if e.customer_name == "Gita Koirala")
    sita_entry = next(e for e in entries if e.customer_name == "Sita Gurung")
    assert gita_entry.notified is True
    assert sita_entry.notified is False  # still waiting - not her turn yet


def test_notify_next_in_waitlist_returns_none_when_nobody_is_waiting(clean_database):
    # The Corolla (vehicle_id 1) has no waitlist entries in the seed data at all.
    vehicle = vehicle_service.get_vehicle(1)
    message = waitlist_service.notify_next_in_waitlist(vehicle)
    assert message is None


def test_cancelling_a_booking_triggers_the_observer_auto_notify(clean_database):
    # End-to-end check of the whole feature: cancelling booking #1 (the Tucson,
    # CONFIRMED, see database/seed_data.py) should free the vehicle AND
    # automatically notify Gita Koirala, who is already waitlisted for it -
    # exactly the behaviour demonstrated live in the CLI.
    booking_service.cancel_booking(1)

    entries = waitlist_service.list_waitlist_for_vehicle(2)
    gita_entry = next(e for e in entries if e.customer_name == "Gita Koirala")
    assert gita_entry.notified is True


def test_vehicle_notify_waitlist_calls_on_vehicle_available_on_every_observer_given():
    # A small, direct test of the Vehicle/Observer relationship itself (models/
    # vehicle.py + models/waitlist.py), without going through the database at
    # all - proving Vehicle.notify_waitlist() really does call
    # on_vehicle_available() on each observer handed to it, exactly once.
    vehicle = Vehicle(
        vehicle_id=99, owner_id=1, registration_no="TEST-001", brand="Toyota",
        model="Corolla", year=2022, vehicle_type="Sedan", seats=5,
        daily_rate=65.00, status="AVAILABLE",
    )
    entry = WaitlistEntry(
        waitlist_id=1, vehicle_id=99, customer_id=1, customer_name="Test Customer",
        requested_pickup_date="2026-10-01", requested_return_date="2026-10-05",
        created_at="2026-09-01", notified=0,
    )
    assert entry.notified is False

    vehicle.notify_waitlist([entry])

    assert entry.notified is True
    assert "Test Customer" in entry.last_notification_message
    assert "Toyota Corolla" in entry.last_notification_message
