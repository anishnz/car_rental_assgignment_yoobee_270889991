"""
services/admin_service.py
============================

WHAT THIS FILE IS FOR:
Administrator-only actions that don't belong more specifically in one of the other
service files: approving/rejecting new registrations, viewing the masked user list,
basic system statistics/reports, and the "00 Reset Test Data" action.
"""

from database.db_connection import DatabaseConnection
from database.schema import init_database
from database.seed_data import seed_if_empty
from models.user import Admin


def _require_admin(acting_user):
    if not isinstance(acting_user, Admin):
        raise PermissionError("This action is restricted to the Super Administrator.")


def list_pending_registration_requests() -> list:
    """Returns every Vehicle Owner/Driver account still waiting for approval (FR - pending registrations)."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all(
        """SELECT vod.owner_driver_id, vod.full_name, u.username
           FROM vehicle_owners_drivers vod
           JOIN users u ON u.user_id = vod.user_id
           WHERE vod.status = 'PENDING'
           ORDER BY vod.owner_driver_id"""
    )
    return rows


def approve_registration(acting_user, owner_driver_id: int):
    """Approves a pending Vehicle Owner/Driver registration (FR4) - both the profile
    row AND the linked user account are updated together, so the account can log in."""
    _require_admin(acting_user)
    db = DatabaseConnection.get_instance()
    profile = db.fetch_one(
        "SELECT user_id FROM vehicle_owners_drivers WHERE owner_driver_id = ?", (owner_driver_id,)
    )
    if profile is None:
        raise ValueError(f"No pending registration found with ID {owner_driver_id}.")
    db.execute(
        "UPDATE vehicle_owners_drivers SET status = 'APPROVED' WHERE owner_driver_id = ?",
        (owner_driver_id,),
    )
    db.execute("UPDATE users SET status = 'APPROVED' WHERE user_id = ?", (profile["user_id"],))


def reject_registration(acting_user, owner_driver_id: int):
    """Rejects a pending Vehicle Owner/Driver registration."""
    _require_admin(acting_user)
    db = DatabaseConnection.get_instance()
    profile = db.fetch_one(
        "SELECT user_id FROM vehicle_owners_drivers WHERE owner_driver_id = ?", (owner_driver_id,)
    )
    if profile is None:
        raise ValueError(f"No pending registration found with ID {owner_driver_id}.")
    db.execute(
        "UPDATE vehicle_owners_drivers SET status = 'REJECTED' WHERE owner_driver_id = ?",
        (owner_driver_id,),
    )
    db.execute("UPDATE users SET status = 'REJECTED' WHERE user_id = ?", (profile["user_id"],))


def list_all_users(acting_user) -> list:
    """
    Returns every user account (username, role, status) for the Admin "Manage
    Users" screen (FR4a). Deliberately does NOT return password_hash at all - the
    CLI always shows a fixed masked placeholder instead (see
    utils.formatters.mask_password()), since a hash can never be turned back into
    the original password anyway.
    """
    _require_admin(acting_user)
    db = DatabaseConnection.get_instance()
    return db.fetch_all("SELECT username, role, status FROM users ORDER BY user_id")


def get_system_statistics(acting_user) -> dict:
    """A handful of basic counts/totals for the Admin "System Statistics" screen (FR19)."""
    _require_admin(acting_user)
    db = DatabaseConnection.get_instance()

    def count(query, params=()):
        return db.fetch_one(query, params)["total"]

    return {
        "total_customers": count("SELECT COUNT(*) AS total FROM customers"),
        "total_vehicles": count("SELECT COUNT(*) AS total FROM vehicles"),
        "available_vehicles": count("SELECT COUNT(*) AS total FROM vehicles WHERE status = 'AVAILABLE'"),
        "pending_bookings": count("SELECT COUNT(*) AS total FROM bookings WHERE status = 'PENDING'"),
        "active_bookings": count("SELECT COUNT(*) AS total FROM bookings WHERE status = 'ACTIVE'"),
        "completed_bookings": count("SELECT COUNT(*) AS total FROM bookings WHERE status = 'COMPLETED'"),
        "total_revenue_paid": db.fetch_one(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM payments WHERE status = 'PAID'"
        )["total"],
        "waitlist_entries_waiting": count("SELECT COUNT(*) AS total FROM waitlist WHERE notified = 0"),
    }


def reset_test_data(acting_user):
    """
    The "00 Reset Test Data" action (restricted to Super Administrator - BR5).
    Wipes every table and re-runs the seed script, so the system returns to exactly
    the starting demo dataset described in docs/02_seed_data_plan.md. The CLI is
    responsible for asking the required Yes/No confirmation BEFORE calling this.
    """
    _require_admin(acting_user)
    db = DatabaseConnection.get_instance()
    for table in ("payments", "waitlist", "bookings", "vehicles",
                  "vehicle_owners_drivers", "customers", "users", "settings"):
        db.execute(f"DELETE FROM {table}")
    init_database(db)
    seed_if_empty(db)
