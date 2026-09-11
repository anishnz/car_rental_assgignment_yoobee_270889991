"""
models/payment.py
==================

WHAT THIS FILE IS FOR:
Defines the Payment class - a simple, mostly-data class representing one simulated
payment record against a booking (see FR18). There is no real payment gateway
involved anywhere in this project (see the "Out of scope" list in the requirements
document) - this class only records that a payment happened, for how much, by what
method, and with what status.
"""


class Payment:
    """Represents one row from the `payments` table as a Python object."""

    VALID_METHODS = ("CASH", "CARD", "BANK_TRANSFER")
    VALID_STATUSES = ("PENDING", "PARTIAL", "PAID")

    def __init__(self, payment_id, booking_id, amount, payment_date, method, status):
        self.payment_id = payment_id
        self.booking_id = booking_id
        self.amount = amount
        self.payment_date = payment_date
        self.method = method
        self.status = status

    @classmethod
    def from_row(cls, row):
        """Builds a Payment object from one sqlite3.Row returned by the database."""
        return cls(
            payment_id=row["payment_id"], booking_id=row["booking_id"],
            amount=row["amount"], payment_date=row["payment_date"],
            method=row["method"], status=row["status"],
        )
