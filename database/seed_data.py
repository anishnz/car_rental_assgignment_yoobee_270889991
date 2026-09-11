"""
database/seed_data.py
======================

WHAT THIS FILE IS FOR:
Inserts the realistic sample dataset described in docs/02_seed_data_plan.md, the very
first time the program is run against a fresh (empty) database. This means Anish -
and the marker - always have a fully working system to explore immediately, without
manually registering accounts or adding vehicles first.

WHY WE CHECK "IS THE DATABASE EMPTY?" FIRST:
seed_if_empty() only inserts data when the `users` table has zero rows. This makes
it safe to call every time the program starts: on the very first run it seeds the
data, and on every later run it does nothing (because real data - including
anything Anish adds by hand while testing - already exists). The "00 Reset Test
Data" admin action (see services/admin_service.py) is what wipes everything and
calls this function again, deliberately, when a fresh demo set is wanted.
"""

from datetime import date

import config
from utils.security import hash_password


def seed_if_empty(db):
    """Seeds the full demo dataset only if the users table is currently empty."""
    existing = db.fetch_one("SELECT COUNT(*) AS total FROM users")
    if existing["total"] > 0:
        return  # already has data - do nothing, so we never overwrite real records

    _seed_settings(db)
    user_ids = _seed_users(db)
    owner_ids = _seed_owner_driver_profiles(db, user_ids)
    customer_ids = _seed_customer_profiles(db, user_ids)
    vehicle_ids = _seed_vehicles(db, owner_ids)
    booking_ids = _seed_bookings(db, customer_ids, vehicle_ids, owner_ids)
    _seed_payments(db, booking_ids)
    _seed_waitlist(db, vehicle_ids, customer_ids)


def _seed_settings(db):
    """Seeds the one system-wide setting this project currently uses: rate_per_km."""
    db.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?)",
        ("rate_per_km", str(config.DEFAULT_RATE_PER_KM)),
    )


def _seed_users(db):
    """
    Creates the 6 demo accounts from docs/02_seed_data_plan.md section 1, and
    returns their new user_id values in a dictionary keyed by username so the
    later seeding functions can link customer/owner profiles back to them.
    """
    demo_accounts = [
        ("admin_ncrs", "Admin@123", "ADMIN", "ACTIVE"),
        ("owner_ram", "Owner@123", "OWNER_DRIVER", "APPROVED"),
        ("owner_hari", "Owner@123", "OWNER_DRIVER", "PENDING"),   # left pending on purpose - demos FR4
        ("driver_bikash", "Driver@123", "OWNER_DRIVER", "APPROVED"),
        ("customer_sita", "Customer@123", "CUSTOMER", "ACTIVE"),
        ("customer_gita", "Customer@123", "CUSTOMER", "ACTIVE"),
    ]
    user_ids = {}
    for username, plain_password, role, status in demo_accounts:
        cursor = db.execute(
            "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, ?, ?)",
            (username, hash_password(plain_password), role, status),
        )
        user_ids[username] = cursor.lastrowid
    return user_ids


def _seed_owner_driver_profiles(db, user_ids):
    """Creates the vehicle_owners_drivers profile row for each OWNER_DRIVER account."""
    profiles = [
        ("owner_ram", "Ram Sharma", "9800000001", "ram.sharma@example.com",
         "NP-LIC-1001", "2028-01-01", 0.00),
        ("owner_hari", "Hari Thapa", "9800000002", "hari.thapa@example.com",
         "NP-LIC-1002", "2027-06-01", 0.00),
        ("driver_bikash", "Bikash Rai", "9800000003", "bikash.rai@example.com",
         "NP-LIC-1003", "2027-12-01", 60.00),
    ]
    owner_ids = {}
    for username, full_name, phone, email, licence_no, licence_expiry, daily_rate in profiles:
        user_id = user_ids[username]
        # status mirrors the linked user's approval status (kept in sync at seed time;
        # services/admin_service.py updates both together when admin approves someone)
        status = "APPROVED" if username != "owner_hari" else "PENDING"
        cursor = db.execute(
            """INSERT INTO vehicle_owners_drivers
               (user_id, full_name, phone, email, licence_no, licence_expiry, daily_driver_rate, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, full_name, phone, email, licence_no, licence_expiry, daily_rate, status),
        )
        owner_ids[username] = cursor.lastrowid
    return owner_ids


def _seed_customer_profiles(db, user_ids):
    """Creates the customers profile row for each CUSTOMER account."""
    profiles = [
        ("customer_sita", "Sita Gurung", "9811111111", "sita.gurung@example.com",
         "Kathmandu, Nepal", "NP-DL-2001"),
        ("customer_gita", "Gita Koirala", "9822222222", "gita.koirala@example.com",
         "Pokhara, Nepal", "NP-DL-2002"),
    ]
    customer_ids = {}
    for username, full_name, phone, email, address, licence_no in profiles:
        user_id = user_ids[username]
        cursor = db.execute(
            """INSERT INTO customers (user_id, full_name, phone, email, address, licence_no)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, full_name, phone, email, address, licence_no),
        )
        customer_ids[username] = cursor.lastrowid
    return customer_ids


def _seed_vehicles(db, owner_ids):
    """Creates the 10-vehicle fleet from docs/02_seed_data_plan.md section 2."""
    ram = owner_ids["owner_ram"]
    fleet = [
        ("BA 01 PA 1234", "Toyota", "Corolla", 2022, "Sedan", 5, 65.00, ram, "AVAILABLE"),
        ("BA 02 PA 5678", "Hyundai", "Tucson", 2023, "SUV", 5, 90.00, ram, "BOOKED"),
        ("BA 03 PA 8888", "Suzuki", "Swift", 2021, "Hatchback", 5, 55.00, ram, "AVAILABLE"),
        ("BA 04 PA 2222", "Toyota", "Hiace", 2020, "Van", 12, 110.00, None, "MAINTENANCE"),
        ("BA 05 PA 3333", "Mahindra", "Bolero", 2022, "Jeep", 7, 85.00, ram, "AVAILABLE"),
        ("BA 06 PA 4444", "Hyundai", "Kona Electric", 2023, "Electric Vehicle", 5, 100.00, ram, "AVAILABLE"),
        ("BA 07 PA 5555", "Toyota", "Land Cruiser Prado", 2023, "Luxury Car", 7, 180.00, ram, "AVAILABLE"),
        ("BA 08 PA 6666", "Kia", "Sportage", 2022, "SUV", 5, 95.00, ram, "AVAILABLE"),
        ("BA 09 PA 7777", "Suzuki", "Alto", 2020, "Hatchback", 4, 45.00, ram, "AVAILABLE"),
        ("BA 10 PA 9999", "Mahindra", "Scorpio", 2021, "Jeep", 7, 88.00, ram, "RENTED"),
    ]
    vehicle_ids = {}
    for registration_no, brand, model, year, vtype, seats, rate, owner_id, status in fleet:
        cursor = db.execute(
            """INSERT INTO vehicles
               (owner_id, registration_no, brand, model, year, vehicle_type, seats, daily_rate, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (owner_id, registration_no, brand, model, year, vtype, seats, rate, status),
        )
        vehicle_ids[registration_no] = cursor.lastrowid
    return vehicle_ids


def _seed_bookings(db, customer_ids, vehicle_ids, owner_ids):
    """
    Creates the 3 bookings from docs/02_seed_data_plan.md section 5, with the cost
    already worked out using the same formula BookingService uses:
        total = (days x daily_rate) + (distance_km x rate_per_km) + (days x driver_rate)
    """
    rate_per_km = config.DEFAULT_RATE_PER_KM
    bookings = []

    # Booking A - CONFIRMED, Tucson, with driver_bikash, 3 days, 150km
    tucson_days = 3
    tucson_cost = (tucson_days * 90.00) + (150 * rate_per_km) + (tucson_days * 60.00)
    bookings.append((
        "A", customer_ids["customer_sita"], vehicle_ids["BA 02 PA 5678"], owner_ids["driver_bikash"],
        "2026-09-20", "2026-09-23", 1, 150, rate_per_km, tucson_cost, "CONFIRMED",
    ))

    # Booking B - COMPLETED, Corolla, no driver, 2 days, 80km
    corolla_days = 2
    corolla_cost = (corolla_days * 65.00) + (80 * rate_per_km)
    bookings.append((
        "B", customer_ids["customer_sita"], vehicle_ids["BA 01 PA 1234"], None,
        "2026-08-01", "2026-08-03", 0, 80, rate_per_km, corolla_cost, "COMPLETED",
    ))

    # Booking C - ACTIVE, Scorpio, no driver, 6 days, 300km
    scorpio_days = 6
    scorpio_cost = (scorpio_days * 88.00) + (300 * rate_per_km)
    bookings.append((
        "C", customer_ids["customer_gita"], vehicle_ids["BA 10 PA 9999"], None,
        "2026-09-08", "2026-09-14", 0, 300, rate_per_km, scorpio_cost, "ACTIVE",
    ))

    booking_ids = {}
    for label, customer_id, vehicle_id, driver_id, pickup, ret, driver_required, distance, rate, total, status in bookings:
        cursor = db.execute(
            """INSERT INTO bookings
               (customer_id, vehicle_id, driver_id, pickup_date, return_date, driver_required,
                distance_km, rate_per_km_applied, total_amount, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (customer_id, vehicle_id, driver_id, pickup, ret, driver_required, distance, rate, total, status),
        )
        booking_ids[label] = cursor.lastrowid
    return booking_ids


def _seed_payments(db, booking_ids):
    """Creates the 3 payments from docs/02_seed_data_plan.md section 7."""
    payments = [
        (booking_ids["A"], 1200.00, "2026-09-15", "CARD", "PAID"),
        (booking_ids["B"], 530.00, "2026-08-01", "CASH", "PAID"),
        (booking_ids["C"], 2028.00, "2026-09-08", "BANK_TRANSFER", "PARTIAL"),
    ]
    for booking_id, amount, payment_date, method, status in payments:
        db.execute(
            """INSERT INTO payments (booking_id, amount, payment_date, method, status)
               VALUES (?, ?, ?, ?, ?)""",
            (booking_id, amount, payment_date, method, status),
        )


def _seed_waitlist(db, vehicle_ids, customer_ids):
    """
    Creates the 1 waitlist entry from docs/02_seed_data_plan.md section 6:
    customer_gita waiting for the Tucson, which customer_sita already has booked for
    overlapping dates. Completing/cancelling Booking A later is what triggers the
    Observer-pattern auto-notify for this entry.
    """
    db.execute(
        """INSERT INTO waitlist
           (vehicle_id, customer_id, requested_pickup_date, requested_return_date, created_at, notified)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (vehicle_ids["BA 02 PA 5678"], customer_ids["customer_gita"],
         "2026-09-21", "2026-09-24", date.today().isoformat(), 0),
    )
