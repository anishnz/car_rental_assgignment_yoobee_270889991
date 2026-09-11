"""
models/waitlist.py
===================

WHAT THIS FILE IS FOR:
Defines WaitlistEntry, the concrete "Observer" in this project's Observer pattern
(see models/observer.py for the interface, models/vehicle.py for the "Subject").
Each WaitlistEntry represents one customer waiting for one specific vehicle to
become available again.
"""

from models.observer import Observer


class WaitlistEntry(Observer):
    """One row from the `waitlist` table, and the Observer that reacts when the
    vehicle it is watching becomes available again."""

    def __init__(self, waitlist_id, vehicle_id, customer_id, customer_name,
                 requested_pickup_date, requested_return_date, created_at, notified):
        self.waitlist_id = waitlist_id
        self.vehicle_id = vehicle_id
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.requested_pickup_date = requested_pickup_date
        self.requested_return_date = requested_return_date
        self.created_at = created_at
        self.notified = bool(notified)
        # This is where the actual notification message is stored after it fires,
        # so the CLI (or a test) can display/inspect exactly what was "sent".
        self.last_notification_message = None

    @classmethod
    def from_row(cls, row, customer_name: str):
        """Builds a WaitlistEntry from one sqlite3.Row plus the customer's name
        (joined in separately by the service layer, since the waitlist table itself
        only stores customer_id, not the name)."""
        return cls(
            waitlist_id=row["waitlist_id"], vehicle_id=row["vehicle_id"],
            customer_id=row["customer_id"], customer_name=customer_name,
            requested_pickup_date=row["requested_pickup_date"],
            requested_return_date=row["requested_return_date"],
            created_at=row["created_at"], notified=row["notified"],
        )

    def on_vehicle_available(self, vehicle):
        """
        This is the method the Observer interface requires us to implement. It is
        called automatically by Vehicle.notify_waitlist() once the vehicle this
        entry is waiting for becomes AVAILABLE again.

        The notification itself is SIMULATED (see NFR1/NFR2 - no real email/SMS,
        and no paid services): we build a clear message and print it to the
        console / write it to the notifications log. services/waitlist_service.py
        is responsible for then saving `notified = True` back to the database, so
        this same customer is not notified again for the same waitlist entry.
        """
        self.last_notification_message = (
            f"[WAITLIST NOTIFICATION] {self.customer_name}, the "
            f"{vehicle.display_name()} you were waiting for is now AVAILABLE! "
            f"You requested {self.requested_pickup_date} to {self.requested_return_date}."
        )
        print(self.last_notification_message)
        self.notified = True
        return self.last_notification_message
