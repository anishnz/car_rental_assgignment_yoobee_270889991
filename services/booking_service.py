"""
services/booking_service.py
=============================

WHAT THIS FILE IS FOR:
The heart of the whole system: creating a booking (with availability/conflict
checking and automatic cost calculation), and moving a booking through its
lifecycle (PENDING -> CONFIRMED/REJECTED -> ACTIVE -> COMPLETED, or CANCELLED at
various points). Whenever a booking's status change means the vehicle is now free
again, this file is also what triggers the Smart Waitlist auto-notify feature.
"""

from database.db_connection import DatabaseConnection
from models.booking import Booking
from models.vehicle import Vehicle
from services import vehicle_service, waitlist_service
from utils import validators


def get_current_rate_per_km() -> float:
    """
    Reads the system-wide rate-per-km setting from the database (FR13a) - NEVER
    hard-coded, so an admin's change to it takes effect on the very next booking
    with no code changes required.
    """
    db = DatabaseConnection.get_instance()
    row = db.fetch_one("SELECT value FROM settings WHERE key = 'rate_per_km'")
    if row is None:
        raise ValueError("System is missing its rate_per_km setting - this should never happen.")
    return float(row["value"])


def set_rate_per_km(new_rate) -> float:
    """Admin-only: updates the system-wide rate per km (FR13a)."""
    new_rate = validators.validate_positive_number(new_rate, "Rate per km")
    db = DatabaseConnection.get_instance()
    db.execute("UPDATE settings SET value = ? WHERE key = 'rate_per_km'", (str(new_rate),))
    return new_rate


def _has_overlapping_booking(db, vehicle_id: int, pickup_date, return_date,
                              exclude_booking_id: int = None) -> bool:
    """
    The core availability-check algorithm (FR12, BR2): two date ranges [p1, r1] and
    [p2, r2] overlap exactly when p1 < r2 AND p2 < r1 - this is the standard test
    for "do these two ranges share any day at all". Only PENDING/CONFIRMED/ACTIVE
    bookings block a new one; a CANCELLED/REJECTED/COMPLETED booking no longer
    holds the vehicle.
    """
    query = """
        SELECT 1 FROM bookings
        WHERE vehicle_id = ?
          AND status IN ('PENDING', 'CONFIRMED', 'ACTIVE')
          AND pickup_date < ?
          AND ? < return_date
    """
    params = [vehicle_id, return_date.isoformat(), pickup_date.isoformat()]
    if exclude_booking_id is not None:
        query += " AND booking_id != ?"
        params.append(exclude_booking_id)
    return db.fetch_one(query, tuple(params)) is not None


def check_vehicle_availability(vehicle_id: int, pickup_date, return_date) -> bool:
    """Public helper the CLI can call BEFORE attempting to create a booking, so the
    customer can be offered the waitlist immediately if the vehicle is busy."""
    db = DatabaseConnection.get_instance()
    vehicle = vehicle_service.get_vehicle(vehicle_id)
    if vehicle.status == "MAINTENANCE":
        return False
    return not _has_overlapping_booking(db, vehicle_id, pickup_date, return_date)


def create_booking(customer, vehicle_id: int, pickup_date_str: str, return_date_str: str,
                    distance_km_str: str, driver_required: bool, driver_id: int = None):
    """
    Creates a new booking (FR10-FR13). Validates dates, checks for conflicts,
    calculates the total cost using the current rate per km, and inserts the
    booking as PENDING (awaiting admin approval) - immediately marking the vehicle
    BOOKED so no one else can take the same slot while it waits for approval.

    Raises ValueError with a clear message for any problem: invalid dates,
    unavailable vehicle, etc.
    """
    pickup_date, return_date = validators.validate_date_range(pickup_date_str, return_date_str)
    distance_km = validators.validate_non_negative_number(distance_km_str, "Distance (km)")

    db = DatabaseConnection.get_instance()
    vehicle = vehicle_service.get_vehicle(vehicle_id)

    if vehicle.status == "MAINTENANCE":
        raise ValueError("This vehicle is currently under maintenance and cannot be booked.")
    if _has_overlapping_booking(db, vehicle_id, pickup_date, return_date):
        raise ValueError(
            "Sorry! This vehicle is already booked during the selected dates. "
            "Please choose another vehicle or another date, or join the waitlist."
        )

    daily_driver_rate = 0
    if driver_required:
        if driver_id is None:
            raise ValueError("A driver is required but no driver was selected.")
        driver_row = db.fetch_one(
            "SELECT daily_driver_rate, status FROM vehicle_owners_drivers WHERE owner_driver_id = ?",
            (driver_id,),
        )
        if driver_row is None:
            raise ValueError("Selected driver was not found.")
        if driver_row["status"] != "AVAILABLE" and driver_row["status"] != "APPROVED":
            raise ValueError("Selected driver is not currently available.")
        daily_driver_rate = driver_row["daily_driver_rate"]

    number_of_days = (return_date - pickup_date).days
    rate_per_km = get_current_rate_per_km()
    total_amount = Booking.calculate_cost(
        number_of_days, vehicle.daily_rate, distance_km, rate_per_km,
        driver_required, daily_driver_rate,
    )

    cursor = db.execute(
        """INSERT INTO bookings
           (customer_id, vehicle_id, driver_id, pickup_date, return_date, driver_required,
            distance_km, rate_per_km_applied, total_amount, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')""",
        (customer.customer_id, vehicle_id, driver_id if driver_required else None,
         pickup_date.isoformat(), return_date.isoformat(), int(driver_required),
         distance_km, rate_per_km, total_amount),
    )
    vehicle_service.update_vehicle_status(vehicle_id, "BOOKED")

    booking_row = db.fetch_one("SELECT * FROM bookings WHERE booking_id = ?", (cursor.lastrowid,))
    return Booking.from_row(booking_row)


def get_booking(booking_id: int) -> Booking:
    """Fetches one booking by ID, or raises ValueError if it does not exist."""
    db = DatabaseConnection.get_instance()
    row = db.fetch_one("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
    if row is None:
        raise ValueError(f"Booking with ID {booking_id} was not found.")
    return Booking.from_row(row)


def _save_booking_status(db, booking: Booking):
    db.execute("UPDATE bookings SET status = ? WHERE booking_id = ?", (booking.status, booking.booking_id))


def _free_up_vehicle_and_notify_waitlist(db, booking: Booking):
    """
    Shared clean-up step used by reject/cancel/complete: puts the vehicle (and its
    driver, if one was assigned) back to AVAILABLE, then triggers the Observer
    pattern's waitlist notification for that vehicle.
    """
    vehicle_service.update_vehicle_status(booking.vehicle_id, "AVAILABLE")
    if booking.driver_id is not None:
        db.execute(
            "UPDATE vehicle_owners_drivers SET status = 'APPROVED' WHERE owner_driver_id = ?",
            (booking.driver_id,),
        )
    vehicle_row = db.fetch_one("SELECT * FROM vehicles WHERE vehicle_id = ?", (booking.vehicle_id,))
    vehicle = Vehicle.from_row(vehicle_row)
    return waitlist_service.notify_next_in_waitlist(vehicle)


def confirm_booking(booking_id: int):
    """Admin approves a PENDING booking (FR14)."""
    db = DatabaseConnection.get_instance()
    booking = get_booking(booking_id)
    booking.confirm()
    _save_booking_status(db, booking)
    if booking.driver_id is not None:
        db.execute(
            "UPDATE vehicle_owners_drivers SET status = 'ASSIGNED' WHERE owner_driver_id = ?",
            (booking.driver_id,),
        )
    return booking


def reject_booking(booking_id: int):
    """Admin rejects a PENDING booking - vehicle becomes available again, waitlist is checked."""
    db = DatabaseConnection.get_instance()
    booking = get_booking(booking_id)
    booking.reject()
    _save_booking_status(db, booking)
    _free_up_vehicle_and_notify_waitlist(db, booking)
    return booking


def cancel_booking(booking_id: int):
    """Customer or admin cancels a booking (FR15) - vehicle becomes available again."""
    db = DatabaseConnection.get_instance()
    booking = get_booking(booking_id)
    booking.cancel()
    _save_booking_status(db, booking)
    _free_up_vehicle_and_notify_waitlist(db, booking)
    return booking


def complete_booking(booking_id: int):
    """Marks a booking COMPLETED once the vehicle has been returned (FR15)."""
    db = DatabaseConnection.get_instance()
    booking = get_booking(booking_id)
    booking.complete()
    _save_booking_status(db, booking)
    _free_up_vehicle_and_notify_waitlist(db, booking)
    return booking


def list_bookings_for_customer(customer_id: int) -> list:
    """Returns every booking belonging to one customer (FR - view my bookings), so a
    customer can never see another customer's private bookings (BR6)."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all(
        "SELECT * FROM bookings WHERE customer_id = ? ORDER BY booking_id DESC", (customer_id,)
    )
    return [Booking.from_row(row) for row in rows]


def list_all_bookings() -> list:
    """Admin-only: every booking in the system (FR19)."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all("SELECT * FROM bookings ORDER BY booking_id DESC")
    return [Booking.from_row(row) for row in rows]


def list_bookings_by_status(status: str) -> list:
    """Admin-only: bookings filtered to one status (e.g. all PENDING requests)."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all(
        "SELECT * FROM bookings WHERE status = ? ORDER BY booking_id", (status,)
    )
    return [Booking.from_row(row) for row in rows]


def list_available_drivers() -> list:
    """
    Returns every Vehicle Owner/Driver account currently free to be hired as a
    driver (status 'APPROVED' - i.e. approved by the admin and not currently
    assigned to another active booking, see confirm_booking()/complete_booking()
    which flip this status to 'ASSIGNED' and back). Used by the CLI's "Book a
    Vehicle" flow (FR13) to show the customer a pick-list of real drivers instead
    of asking them to type a raw ID blindly.
    """
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all(
        """SELECT owner_driver_id, full_name, daily_driver_rate
           FROM vehicle_owners_drivers
           WHERE status = 'APPROVED'
           ORDER BY owner_driver_id"""
    )
    return rows
