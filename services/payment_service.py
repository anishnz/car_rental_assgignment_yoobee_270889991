"""
services/payment_service.py
=============================

WHAT THIS FILE IS FOR:
Recording simulated payments against a booking (FR18). As noted throughout this
project's documentation, there is NO real payment gateway anywhere - this simply
records that a payment happened, so the system's data (and reports) reflect it.
"""

from datetime import date

from database.db_connection import DatabaseConnection
from models.payment import Payment
from utils import validators


def record_payment(booking_id: int, amount, method: str, status: str) -> Payment:
    """Records a payment against an existing booking."""
    amount = validators.validate_positive_number(amount, "Payment amount")
    method = validators.validate_choice(method, list(Payment.VALID_METHODS), "Payment method")
    status = validators.validate_choice(status, list(Payment.VALID_STATUSES), "Payment status")

    db = DatabaseConnection.get_instance()
    booking_row = db.fetch_one("SELECT 1 FROM bookings WHERE booking_id = ?", (booking_id,))
    if booking_row is None:
        raise ValueError(f"Booking with ID {booking_id} was not found.")

    cursor = db.execute(
        """INSERT INTO payments (booking_id, amount, payment_date, method, status)
           VALUES (?, ?, ?, ?, ?)""",
        (booking_id, amount, date.today().isoformat(), method, status),
    )
    row = db.fetch_one("SELECT * FROM payments WHERE payment_id = ?", (cursor.lastrowid,))
    return Payment.from_row(row)


def list_payments_for_booking(booking_id: int) -> list:
    """Returns every payment recorded against one booking."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all("SELECT * FROM payments WHERE booking_id = ? ORDER BY payment_id", (booking_id,))
    return [Payment.from_row(row) for row in rows]


def list_all_payments() -> list:
    """Admin-only: every payment in the system (FR19)."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all("SELECT * FROM payments ORDER BY payment_id DESC")
    return [Payment.from_row(row) for row in rows]
