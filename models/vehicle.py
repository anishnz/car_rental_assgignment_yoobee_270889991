"""
models/vehicle.py
==================

WHAT THIS FILE IS FOR:
Defines the Vehicle class, and its role as the "Subject" half of the Observer
pattern used by the Smart Waitlist + Auto-Notify feature (see models/observer.py for
the "Observer" half, and models/waitlist.py for the concrete observer class).

HOW THE SUBJECT SIDE WORKS HERE:
In a classic Observer pattern example, the Subject keeps its list of observers in
memory for as long as the program runs. This project's vehicles, however, are
recreated from database rows each time they are needed (not kept alive in memory
between menu screens) - so instead of holding a permanent Python list of observer
objects, `notify_waitlist()` is handed the list of currently-waiting observers by
the caller (services/waitlist_service.py fetches them from the `waitlist` table
right before calling this method). This is a deliberate, realistic adaptation of the
pattern to a database-backed application, while keeping the same core idea: the
Vehicle does not need to know anything about WHO is waiting or WHY - it simply loops
through whoever is handed to it and calls their on_vehicle_available() method.
"""


class Vehicle:
    """Represents one row from the `vehicles` table as a Python object."""

    def __init__(self, vehicle_id, owner_id, registration_no, brand, model, year,
                 vehicle_type, seats, daily_rate, status):
        self.vehicle_id = vehicle_id
        self.owner_id = owner_id
        self.registration_no = registration_no
        self.brand = brand
        self.model = model
        self.year = year
        self.vehicle_type = vehicle_type
        self.seats = seats
        self.daily_rate = daily_rate
        self.status = status

    @classmethod
    def from_row(cls, row):
        """Builds a Vehicle object from one sqlite3.Row returned by the database."""
        return cls(
            vehicle_id=row["vehicle_id"], owner_id=row["owner_id"],
            registration_no=row["registration_no"], brand=row["brand"],
            model=row["model"], year=row["year"], vehicle_type=row["vehicle_type"],
            seats=row["seats"], daily_rate=row["daily_rate"], status=row["status"],
        )

    def display_name(self) -> str:
        """A short, human-readable name for this vehicle, e.g. "Toyota Corolla"."""
        return f"{self.brand} {self.model}"

    def is_available(self) -> bool:
        """Whether this vehicle can currently be booked."""
        return self.status == "AVAILABLE"

    def notify_waitlist(self, observers: list):
        """
        The "notify observers" step of the Observer pattern: calls
        on_vehicle_available(self) on every observer in the list handed to us. Each
        observer (a WaitlistEntry - see models/waitlist.py) decides for itself what
        that notification actually looks like; this Vehicle does not need to know.
        """
        for observer in observers:
            observer.on_vehicle_available(self)
