"""
services/waitlist_service.py
==============================

WHAT THIS FILE IS FOR:
Everything to do with the Smart Waitlist + Auto-Notify feature (FR16/FR17): letting
a customer join a vehicle's waitlist, and triggering the Observer-pattern
notification when that vehicle becomes available again.

HOW THIS TIES INTO THE OBSERVER PATTERN:
models/vehicle.py's Vehicle.notify_waitlist() is the "Subject" side of the pattern -
it just loops through whatever observers it is handed. THIS file is what actually
builds that list of observers (by reading the `waitlist` table) and hands it to the
vehicle at the right moment. In other words: the database's `waitlist` table IS the
persisted form of "who is currently observing this vehicle" - see the comment in
models/vehicle.py for why that's a reasonable adaptation of the classic pattern to a
database-backed application.
"""

from datetime import date

from database.db_connection import DatabaseConnection
from models.vehicle import Vehicle
from models.waitlist import WaitlistEntry


def join_waitlist(customer, vehicle_id: int, requested_pickup_date, requested_return_date):
    """
    Adds a customer to a vehicle's waitlist (FR16) - normally called right after
    booking_service.create_booking() has rejected the same request as a date
    conflict, so the customer is offered this instead.
    """
    db = DatabaseConnection.get_instance()
    db.execute(
        """INSERT INTO waitlist
           (vehicle_id, customer_id, requested_pickup_date, requested_return_date, created_at, notified)
           VALUES (?, ?, ?, ?, ?, 0)""",
        (vehicle_id, customer.customer_id, requested_pickup_date.isoformat(),
         requested_return_date.isoformat(), date.today().isoformat()),
    )


def _load_unnotified_observers(db, vehicle_id: int) -> list:
    """
    Loads every not-yet-notified WaitlistEntry for one vehicle, in FIFO order
    (oldest request first - `created_at ASC`), joined with the customer's name so
    the notification message can address them by name.
    """
    rows = db.fetch_all(
        """SELECT w.*, c.full_name AS customer_name
           FROM waitlist w
           JOIN customers c ON c.customer_id = w.customer_id
           WHERE w.vehicle_id = ? AND w.notified = 0
           ORDER BY w.created_at ASC""",
        (vehicle_id,),
    )
    return [WaitlistEntry.from_row(row, row["customer_name"]) for row in rows]


def notify_next_in_waitlist(vehicle):
    """
    The "notify" step of the Observer pattern (FR17): when a vehicle's status has
    just changed to AVAILABLE, this notifies only the NEXT customer in that
    vehicle's FIFO queue (not everyone at once - the vehicle is only free for one
    rental at a time), then marks that one entry as notified in the database so
    they are not notified again later.

    `vehicle` is a models.vehicle.Vehicle instance. Returns the notification
    message that was produced, or None if nobody was waiting.
    """
    db = DatabaseConnection.get_instance()
    observers = _load_unnotified_observers(db, vehicle.vehicle_id)
    if not observers:
        return None

    next_observer = observers[0]  # FIFO - the earliest still-unnotified request
    vehicle.notify_waitlist([next_observer])  # Subject notifies exactly this one Observer

    db.execute(
        "UPDATE waitlist SET notified = 1 WHERE waitlist_id = ?",
        (next_observer.waitlist_id,),
    )
    return next_observer.last_notification_message


def list_waitlist_for_vehicle(vehicle_id: int) -> list:
    """Returns every waitlist entry (notified or not) for one vehicle, for admin/owner viewing."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all(
        """SELECT w.*, c.full_name AS customer_name
           FROM waitlist w JOIN customers c ON c.customer_id = w.customer_id
           WHERE w.vehicle_id = ? ORDER BY w.created_at ASC""",
        (vehicle_id,),
    )
    return [WaitlistEntry.from_row(row, row["customer_name"]) for row in rows]
