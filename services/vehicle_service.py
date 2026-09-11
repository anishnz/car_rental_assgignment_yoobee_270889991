"""
services/vehicle_service.py
=============================

WHAT THIS FILE IS FOR:
All vehicle CRUD (Create, Read, Update, Delete) operations, plus searching and
browsing. This is the only place in the project that reads or writes the
`vehicles` table directly.
"""

from database.db_connection import DatabaseConnection
from models.vehicle import Vehicle
from utils import validators

VALID_TYPES = ("Sedan", "SUV", "Hatchback", "Van", "Jeep", "Electric Vehicle", "Luxury Car")
VALID_STATUSES = ("AVAILABLE", "BOOKED", "RENTED", "MAINTENANCE")


def list_all_vehicles() -> list:
    """Returns every vehicle in the fleet, as a list of Vehicle objects."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all("SELECT * FROM vehicles ORDER BY vehicle_id")
    return [Vehicle.from_row(row) for row in rows]


def list_available_vehicles() -> list:
    """Returns only vehicles currently AVAILABLE - what a Guest/Customer browses (FR7)."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all("SELECT * FROM vehicles WHERE status = 'AVAILABLE' ORDER BY vehicle_id")
    return [Vehicle.from_row(row) for row in rows]


def list_vehicles_by_type(vehicle_type: str) -> list:
    """Returns available vehicles of one car type (used by the "View Car Types" menu)."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all(
        "SELECT * FROM vehicles WHERE vehicle_type = ? AND status = 'AVAILABLE' ORDER BY vehicle_id",
        (vehicle_type,),
    )
    return [Vehicle.from_row(row) for row in rows]


def list_vehicles_owned_by(owner_driver_id: int) -> list:
    """Returns the vehicles owned by one specific Vehicle Owner/Driver account."""
    db = DatabaseConnection.get_instance()
    rows = db.fetch_all(
        "SELECT * FROM vehicles WHERE owner_id = ? ORDER BY vehicle_id", (owner_driver_id,)
    )
    return [Vehicle.from_row(row) for row in rows]


def search_vehicles(keyword: str) -> list:
    """Simple keyword search across brand, model, and registration number (FR - search)."""
    db = DatabaseConnection.get_instance()
    pattern = f"%{keyword}%"
    rows = db.fetch_all(
        """SELECT * FROM vehicles
           WHERE brand LIKE ? OR model LIKE ? OR registration_no LIKE ?
           ORDER BY vehicle_id""",
        (pattern, pattern, pattern),
    )
    return [Vehicle.from_row(row) for row in rows]


def get_vehicle(vehicle_id: int) -> Vehicle:
    """Fetches one vehicle by ID, or raises ValueError if it does not exist."""
    db = DatabaseConnection.get_instance()
    row = db.fetch_one("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
    if row is None:
        raise ValueError(f"Vehicle with ID {vehicle_id} was not found.")
    return Vehicle.from_row(row)


def add_vehicle(owner_id, registration_no, brand, model, year, vehicle_type, seats, daily_rate):
    """Adds a new vehicle to the fleet (FR5). Validates every field first."""
    registration_no = validators.validate_non_empty(registration_no, "Registration number")
    brand = validators.validate_non_empty(brand, "Brand")
    model = validators.validate_non_empty(model, "Model")
    year = validators.validate_year(year)
    vehicle_type = validators.validate_choice(vehicle_type, list(VALID_TYPES), "Vehicle type")
    seats = validators.validate_positive_int(seats, "Number of seats")
    daily_rate = validators.validate_positive_number(daily_rate, "Daily rate")

    db = DatabaseConnection.get_instance()
    existing = db.fetch_one("SELECT 1 FROM vehicles WHERE registration_no = ?", (registration_no,))
    if existing is not None:
        raise ValueError(f"A vehicle with registration '{registration_no}' already exists.")

    cursor = db.execute(
        """INSERT INTO vehicles (owner_id, registration_no, brand, model, year,
                                  vehicle_type, seats, daily_rate, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'AVAILABLE')""",
        (owner_id, registration_no, brand, model, year, vehicle_type, seats, daily_rate),
    )
    return cursor.lastrowid


def update_vehicle_rate(vehicle_id: int, new_daily_rate):
    """Updates a vehicle's daily rental rate (part of FR5's "update" capability)."""
    new_daily_rate = validators.validate_positive_number(new_daily_rate, "Daily rate")
    db = DatabaseConnection.get_instance()
    get_vehicle(vehicle_id)  # raises ValueError if it doesn't exist
    db.execute("UPDATE vehicles SET daily_rate = ? WHERE vehicle_id = ?", (new_daily_rate, vehicle_id))


def update_vehicle_status(vehicle_id: int, new_status: str):
    """
    Updates a vehicle's status. This is called constantly by the booking workflow
    (BOOKED when a booking is made, AVAILABLE again once it's cancelled/completed,
    etc.) as well as directly by an admin/owner marking a vehicle under MAINTENANCE.
    """
    new_status = validators.validate_choice(new_status, list(VALID_STATUSES), "Vehicle status")
    db = DatabaseConnection.get_instance()
    get_vehicle(vehicle_id)
    db.execute("UPDATE vehicles SET status = ? WHERE vehicle_id = ?", (new_status, vehicle_id))


def delete_vehicle(vehicle_id: int):
    """Removes a vehicle from the fleet (FR5)."""
    db = DatabaseConnection.get_instance()
    get_vehicle(vehicle_id)
    active_booking = db.fetch_one(
        """SELECT 1 FROM bookings WHERE vehicle_id = ?
           AND status IN ('PENDING', 'CONFIRMED', 'ACTIVE')""",
        (vehicle_id,),
    )
    if active_booking is not None:
        raise ValueError("Cannot delete a vehicle that has an active or pending booking.")
    db.execute("DELETE FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
