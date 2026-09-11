"""
models/booking.py
==================

WHAT THIS FILE IS FOR:
Defines the Booking class: the central object in this system, connecting a
Customer, a Vehicle, an optional driver, and the calculated cost together.

WHY THE COST CALCULATION LIVES HERE (and not in the CLI or the database layer):
calculate_cost() is a pure function of the booking's own data (days, distance, daily
rate, driver rate) - it doesn't need the database or the screen, so it belongs on
the Booking object itself. This is ENCAPSULATION: the rule for "how much does this
booking cost" lives in exactly one place, next to the data it uses, instead of being
copied into every menu screen that happens to show a price.

STATUS TRANSITIONS (confirm/cancel/complete): these methods only change
`self.status` and validate that the change makes sense (e.g. you cannot complete a
booking that was already cancelled) - they do not touch the database themselves.
services/booking_service.py calls these methods AND THEN saves the new status to the
database, keeping "what changes are allowed" (here) separate from "how it's saved"
(there).
"""

from datetime import date


class Booking:
    """Represents one row from the `bookings` table as a Python object."""

    VALID_STATUSES = ("PENDING", "CONFIRMED", "ACTIVE", "COMPLETED", "CANCELLED", "REJECTED")

    def __init__(self, booking_id, customer_id, vehicle_id, driver_id, pickup_date,
                 return_date, driver_required, distance_km, rate_per_km_applied,
                 total_amount, status):
        self.booking_id = booking_id
        self.customer_id = customer_id
        self.vehicle_id = vehicle_id
        self.driver_id = driver_id
        self.pickup_date = pickup_date  # a datetime.date
        self.return_date = return_date  # a datetime.date
        self.driver_required = bool(driver_required)
        self.distance_km = distance_km
        self.rate_per_km_applied = rate_per_km_applied
        self.total_amount = total_amount
        self.status = status

    @classmethod
    def from_row(cls, row):
        """Builds a Booking object from one sqlite3.Row, parsing the stored text
        dates back into real datetime.date objects."""
        return cls(
            booking_id=row["booking_id"], customer_id=row["customer_id"],
            vehicle_id=row["vehicle_id"], driver_id=row["driver_id"],
            pickup_date=date.fromisoformat(row["pickup_date"]),
            return_date=date.fromisoformat(row["return_date"]),
            driver_required=row["driver_required"], distance_km=row["distance_km"],
            rate_per_km_applied=row["rate_per_km_applied"],
            total_amount=row["total_amount"], status=row["status"],
        )

    @property
    def number_of_days(self) -> int:
        """How many days this booking covers (return date minus pickup date)."""
        return (self.return_date - self.pickup_date).days

    @staticmethod
    def calculate_cost(number_of_days: int, daily_vehicle_rate: float, distance_km: float,
                        rate_per_km: float, driver_required: bool,
                        daily_driver_rate: float = 0) -> float:
        """
        Implements the agreed pricing formula (see docs/01_requirements_analysis.md
        BR3/BR3a):

            Total Cost = (Days x Daily Vehicle Rate)
                       + (Distance in km x Rate per km)
                       + (Days x Driver Daily Rate, only if a driver is requested)

        Kept as a @staticmethod (does not need `self`) because it is a pure
        calculation that only depends on the values passed in - useful on its own,
        and easy to test in isolation (see tests/test_booking_cost.py).
        """
        vehicle_cost = number_of_days * daily_vehicle_rate
        distance_cost = distance_km * rate_per_km
        driver_cost = (number_of_days * daily_driver_rate) if driver_required else 0
        return vehicle_cost + distance_cost + driver_cost

    def confirm(self):
        """Admin approves a PENDING booking, moving it to CONFIRMED."""
        if self.status != "PENDING":
            raise ValueError(f"Cannot confirm a booking that is currently {self.status}.")
        self.status = "CONFIRMED"

    def reject(self):
        """Admin rejects a PENDING booking - the vehicle becomes available again."""
        if self.status != "PENDING":
            raise ValueError(f"Cannot reject a booking that is currently {self.status}.")
        self.status = "REJECTED"

    def cancel(self):
        """Customer or admin cancels a booking that has not finished yet."""
        if self.status in ("COMPLETED", "CANCELLED", "REJECTED"):
            raise ValueError(f"Cannot cancel a booking that is already {self.status}.")
        self.status = "CANCELLED"

    def complete(self):
        """Marks a booking as finished (the vehicle has been returned)."""
        if self.status not in ("CONFIRMED", "ACTIVE"):
            raise ValueError(f"Cannot complete a booking that is currently {self.status}.")
        self.status = "COMPLETED"

    def frees_up_vehicle(self) -> bool:
        """
        Whether reaching this booking's CURRENT status means the vehicle it used
        should go back to AVAILABLE. Used by services/booking_service.py right
        after cancel()/reject()/complete() to decide whether to update the vehicle
        and trigger the waitlist notification.
        """
        return self.status in ("CANCELLED", "REJECTED", "COMPLETED")
