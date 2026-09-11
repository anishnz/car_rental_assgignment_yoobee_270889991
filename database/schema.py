"""
database/schema.py
===================

WHAT THIS FILE IS FOR:
Defines every table the Nepal Car Rental System needs, and the function that
creates them the first time the program runs. This is the Python equivalent of a
".sql" database setup script - written as a Python string so it can be executed
directly through our DatabaseConnection class with no extra tools required.

WHY "CREATE TABLE IF NOT EXISTS":
Every table is created with "IF NOT EXISTS", so running this function is SAFE to do
every single time the program starts: on the very first run it creates all the
tables from nothing, and on every run after that it does nothing (because the tables
already exist), rather than raising an error or wiping existing data.
"""

_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        username       TEXT UNIQUE NOT NULL,
        password_hash  TEXT NOT NULL,
        role           TEXT NOT NULL CHECK (role IN ('ADMIN', 'OWNER_DRIVER', 'CUSTOMER')),
        status         TEXT NOT NULL DEFAULT 'ACTIVE'
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS customers (
        customer_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER UNIQUE NOT NULL REFERENCES users(user_id),
        full_name    TEXT NOT NULL,
        phone        TEXT,
        email        TEXT,
        address      TEXT,
        licence_no   TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS vehicle_owners_drivers (
        owner_driver_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id             INTEGER UNIQUE NOT NULL REFERENCES users(user_id),
        full_name           TEXT NOT NULL,
        phone               TEXT,
        email               TEXT,
        licence_no          TEXT,
        licence_expiry      TEXT,
        daily_driver_rate   REAL NOT NULL DEFAULT 0,
        status              TEXT NOT NULL DEFAULT 'PENDING'
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS vehicles (
        vehicle_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id         INTEGER REFERENCES vehicle_owners_drivers(owner_driver_id),
        registration_no  TEXT UNIQUE NOT NULL,
        brand            TEXT NOT NULL,
        model            TEXT NOT NULL,
        year             INTEGER NOT NULL,
        vehicle_type     TEXT NOT NULL,
        seats            INTEGER NOT NULL,
        daily_rate       REAL NOT NULL,
        status           TEXT NOT NULL DEFAULT 'AVAILABLE'
            CHECK (status IN ('AVAILABLE', 'BOOKED', 'RENTED', 'MAINTENANCE'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bookings (
        booking_id            INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id           INTEGER NOT NULL REFERENCES customers(customer_id),
        vehicle_id            INTEGER NOT NULL REFERENCES vehicles(vehicle_id),
        driver_id             INTEGER REFERENCES vehicle_owners_drivers(owner_driver_id),
        pickup_date           TEXT NOT NULL,
        return_date           TEXT NOT NULL,
        driver_required       INTEGER NOT NULL DEFAULT 0,
        distance_km           REAL NOT NULL DEFAULT 0,
        rate_per_km_applied   REAL NOT NULL,
        total_amount          REAL NOT NULL,
        status                TEXT NOT NULL DEFAULT 'PENDING'
            CHECK (status IN ('PENDING', 'CONFIRMED', 'ACTIVE', 'COMPLETED', 'CANCELLED', 'REJECTED'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
        payment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id    INTEGER NOT NULL REFERENCES bookings(booking_id),
        amount        REAL NOT NULL,
        payment_date  TEXT NOT NULL,
        method        TEXT NOT NULL CHECK (method IN ('CASH', 'CARD', 'BANK_TRANSFER')),
        status        TEXT NOT NULL CHECK (status IN ('PENDING', 'PARTIAL', 'PAID'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS waitlist (
        waitlist_id            INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id             INTEGER NOT NULL REFERENCES vehicles(vehicle_id),
        customer_id            INTEGER NOT NULL REFERENCES customers(customer_id),
        requested_pickup_date  TEXT NOT NULL,
        requested_return_date  TEXT NOT NULL,
        created_at             TEXT NOT NULL,
        notified               INTEGER NOT NULL DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS settings (
        key    TEXT PRIMARY KEY,
        value  TEXT NOT NULL
    );
    """,
]


def init_database(db):
    """
    Creates every table listed above if it does not already exist. `db` is a
    DatabaseConnection instance (see database/db_connection.py). Called once, right
    when the program starts (see services/rental_system.py).
    """
    for statement in _SCHEMA_STATEMENTS:
        db.execute(statement)
