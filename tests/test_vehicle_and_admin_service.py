"""
tests/test_vehicle_and_admin_service.py
==========================================

WHAT THIS FILE IS FOR:
Automated tests for services/vehicle_service.py (fleet CRUD) and
services/admin_service.py (registration approval, masked user list, system
statistics, reset-test-data) - the remaining service-layer pieces not already
covered by the other test files.
"""

import pytest

from models.user import Admin
from services import admin_service, auth_service, vehicle_service
import config


def _login_as_admin():
    return auth_service.login("admin_ncrs", "Admin@123")


def test_add_vehicle_then_retrieve_it(clean_database):
    vehicle_id = vehicle_service.add_vehicle(
        owner_id=1, registration_no="TEST-9999", brand="Toyota", model="Yaris",
        year="2023", vehicle_type="Sedan", seats="5", daily_rate="70.00",
    )
    vehicle = vehicle_service.get_vehicle(vehicle_id)
    assert vehicle.display_name() == "Toyota Yaris"
    assert vehicle.status == "AVAILABLE"


def test_add_vehicle_rejects_a_duplicate_registration_number(clean_database):
    # BA 01 PA 1234 already exists in the seed data (the Corolla).
    with pytest.raises(ValueError, match="already exists"):
        vehicle_service.add_vehicle(
            owner_id=1, registration_no="BA 01 PA 1234", brand="Honda", model="Civic",
            year="2022", vehicle_type="Sedan", seats="5", daily_rate="60.00",
        )


def test_update_vehicle_rate_changes_the_stored_rate(clean_database):
    vehicle_service.update_vehicle_rate(1, "75.00")
    vehicle = vehicle_service.get_vehicle(1)
    assert vehicle.daily_rate == 75.00


def test_delete_vehicle_blocks_when_an_active_booking_exists(clean_database):
    # Vehicle 2 (Tucson) has a CONFIRMED booking in the seed data - it must not
    # be possible to delete it while that booking is still active/pending.
    with pytest.raises(ValueError, match="active or pending booking"):
        vehicle_service.delete_vehicle(2)


def test_delete_vehicle_succeeds_when_no_active_booking_exists(clean_database):
    # Vehicle 6 (Kona Electric) has no bookings referencing it at all in the seed
    # data, so deleting it should succeed cleanly.
    vehicle_service.delete_vehicle(6)
    with pytest.raises(ValueError, match="not found"):
        vehicle_service.get_vehicle(6)


def test_approve_registration_activates_the_pending_owner_driver(clean_database):
    admin = _login_as_admin()
    pending = admin_service.list_pending_registration_requests()
    hari = next(p for p in pending if p["username"] == "owner_hari")

    admin_service.approve_registration(admin, hari["owner_driver_id"])

    user = auth_service.login("owner_hari", "Owner@123")
    assert user.is_active() is True


def test_reject_registration_leaves_the_account_unable_to_login(clean_database):
    admin = _login_as_admin()
    pending = admin_service.list_pending_registration_requests()
    hari = next(p for p in pending if p["username"] == "owner_hari")

    admin_service.reject_registration(admin, hari["owner_driver_id"])

    with pytest.raises(ValueError):
        auth_service.login("owner_hari", "Owner@123")


def test_list_all_users_never_includes_password_hash(clean_database):
    admin = _login_as_admin()
    users = admin_service.list_all_users(admin)
    assert len(users) == 6  # the 6 seeded accounts
    for user_row in users:
        assert set(user_row.keys()) == {"username", "role", "status"}


def test_only_admin_can_list_all_users(clean_database):
    non_admin_customer = auth_service.login("customer_sita", "Customer@123")
    with pytest.raises(PermissionError):
        admin_service.list_all_users(non_admin_customer)


def test_get_system_statistics_reports_expected_seed_counts(clean_database):
    admin = _login_as_admin()
    stats = admin_service.get_system_statistics(admin)
    assert stats["total_customers"] == 2
    assert stats["total_vehicles"] == 10
    assert stats["waitlist_entries_waiting"] == 1


def test_reset_test_data_restores_the_original_seed_counts(clean_database):
    admin = _login_as_admin()
    vehicle_service.delete_vehicle(6)  # remove one vehicle to prove the reset undoes this

    admin_service.reset_test_data(admin)

    # After the reset, the freshly re-seeded database should look exactly like a
    # brand new run again - a NEW admin object must be fetched here because the
    # old `admin` User object's underlying account was just wiped and recreated.
    fresh_admin = _login_as_admin()
    stats = admin_service.get_system_statistics(fresh_admin)
    assert stats["total_vehicles"] == 10
