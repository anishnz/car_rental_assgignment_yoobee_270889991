"""
cli/owner_menu.py
====================

WHAT THIS FILE IS FOR:
The full dashboard shown to a logged-in Vehicle Owner/Driver: managing their own
fleet (add/update/delete vehicles), checking who is waitlisted for their vehicles,
and changing their password. Every action here is scoped to vehicles this specific
owner actually owns - an owner can never edit or delete someone else's vehicle,
even by guessing an ID.
"""

from cli.common import (
    print_header, print_divider, read_input, read_menu_choice,
    confirm_yes_no, show_error, show_success, pause, CancelOperation,
)
from services import vehicle_service, waitlist_service, auth_service
from utils import validators
from utils.formatters import format_currency, format_table

_MENU_HELP = (
    "Pick a number from the menu to run that action. Type 0 at this menu to log "
    "out and return to the welcome screen. Inside a form, type C to cancel that "
    "form and come back here, or H to see help for the field you are on."
)


def run(owner):
    """
    The Vehicle Owner/Driver dashboard loop. `owner` is a
    models.user.VehicleOwnerDriver instance. Runs until the owner logs out (0).
    """
    while True:
        print_header(f"OWNER / DRIVER DASHBOARD - {owner.full_name}")
        print("1. View My Vehicles")
        print("2. Add a New Vehicle")
        print("3. Update a Vehicle's Daily Rate")
        print("4. Update a Vehicle's Status")
        print("5. Delete a Vehicle")
        print("6. View Waitlist for One of My Vehicles")
        print("7. Change My Password")
        print("0. Logout\n")
        choice = read_menu_choice()

        if choice == "1":
            _view_my_vehicles(owner)
        elif choice == "2":
            _add_vehicle(owner)
        elif choice == "3":
            _update_rate(owner)
        elif choice == "4":
            _update_status(owner)
        elif choice == "5":
            _delete_vehicle(owner)
        elif choice == "6":
            _view_waitlist(owner)
        elif choice == "7":
            _change_password(owner)
        elif choice == "0":
            print(f"\nGoodbye, {owner.full_name}. Logging out...\n")
            return
        elif choice.upper() == "H":
            print(_MENU_HELP)
        else:
            show_error("Invalid input. Please enter a number from the available menu options.")


def _vehicle_rows(vehicles):
    return [
        [v.vehicle_id, v.display_name(), v.registration_no, v.vehicle_type,
         v.seats, format_currency(v.daily_rate), v.status]
        for v in vehicles
    ]


_VEHICLE_HEADERS = ["ID", "Vehicle", "Registration No.", "Type", "Seats", "Daily Rate", "Status"]


def _view_my_vehicles(owner):
    print_header("MY VEHICLES")
    vehicles = vehicle_service.list_vehicles_owned_by(owner.owner_driver_id)
    if not vehicles:
        print("(you have not listed any vehicles yet)")
    else:
        print(format_table(_VEHICLE_HEADERS, _vehicle_rows(vehicles)))
    pause()


def _get_own_vehicle_or_error(owner, vehicle_id):
    """
    Shared ownership check: fetches a vehicle by ID and confirms it actually
    belongs to this owner before letting any update/delete action touch it.
    Returns the Vehicle object, or None (after showing an error) if the ID does
    not exist at all, OR it exists but belongs to a different owner.
    """
    try:
        vehicle = vehicle_service.get_vehicle(vehicle_id)
    except ValueError as error:
        show_error(str(error))
        return None
    if vehicle.owner_id != owner.owner_driver_id:
        show_error("That vehicle does not belong to your account.")
        return None
    return vehicle


def _add_vehicle(owner):
    print_header("ADD A NEW VEHICLE")
    print(f"Allowed vehicle types: {', '.join(vehicle_service.VALID_TYPES)}\n")
    try:
        registration_no = read_input("Registration Number")
        brand = read_input("Brand")
        model = read_input("Model")
        year = read_input("Year")
        vehicle_type = read_input("Vehicle Type")
        seats = read_input("Number of Seats")
        daily_rate = read_input("Daily Rate")
    except CancelOperation:
        return

    try:
        vehicle_id = vehicle_service.add_vehicle(
            owner.owner_driver_id, registration_no, brand, model, year,
            vehicle_type, seats, daily_rate,
        )
    except ValueError as error:
        show_error(str(error))
        return

    show_success(f"Vehicle added successfully with ID {vehicle_id}.")


def _update_rate(owner):
    print_header("UPDATE A VEHICLE'S DAILY RATE")
    try:
        vehicle_id_str = read_input("Enter the Vehicle ID")
        new_rate_str = read_input("Enter the new daily rate")
    except CancelOperation:
        return

    try:
        vehicle_id = validators.validate_positive_int(vehicle_id_str, "Vehicle ID")
    except ValueError as error:
        show_error(str(error))
        return

    if _get_own_vehicle_or_error(owner, vehicle_id) is None:
        return

    try:
        vehicle_service.update_vehicle_rate(vehicle_id, new_rate_str)
    except ValueError as error:
        show_error(str(error))
        return

    show_success("Daily rate updated successfully.")


def _update_status(owner):
    print_header("UPDATE A VEHICLE'S STATUS")
    print(f"Allowed statuses: {', '.join(vehicle_service.VALID_STATUSES)}\n")
    try:
        vehicle_id_str = read_input("Enter the Vehicle ID")
        new_status = read_input("Enter the new status")
    except CancelOperation:
        return

    try:
        vehicle_id = validators.validate_positive_int(vehicle_id_str, "Vehicle ID")
    except ValueError as error:
        show_error(str(error))
        return

    if _get_own_vehicle_or_error(owner, vehicle_id) is None:
        return

    try:
        vehicle_service.update_vehicle_status(vehicle_id, new_status.upper())
    except ValueError as error:
        show_error(str(error))
        return

    show_success("Vehicle status updated successfully.")


def _delete_vehicle(owner):
    print_header("DELETE A VEHICLE")
    try:
        vehicle_id_str = read_input("Enter the Vehicle ID to delete")
    except CancelOperation:
        return

    try:
        vehicle_id = validators.validate_positive_int(vehicle_id_str, "Vehicle ID")
    except ValueError as error:
        show_error(str(error))
        return

    vehicle = _get_own_vehicle_or_error(owner, vehicle_id)
    if vehicle is None:
        return

    if not confirm_yes_no(f"Are you sure you want to delete {vehicle.display_name()} ({vehicle.registration_no})?"):
        return

    try:
        vehicle_service.delete_vehicle(vehicle_id)
    except ValueError as error:
        show_error(str(error))
        return

    show_success("Vehicle deleted successfully.")


def _view_waitlist(owner):
    print_header("WAITLIST FOR ONE OF MY VEHICLES")
    try:
        vehicle_id_str = read_input("Enter the Vehicle ID")
    except CancelOperation:
        return

    try:
        vehicle_id = validators.validate_positive_int(vehicle_id_str, "Vehicle ID")
    except ValueError as error:
        show_error(str(error))
        return

    if _get_own_vehicle_or_error(owner, vehicle_id) is None:
        return

    entries = waitlist_service.list_waitlist_for_vehicle(vehicle_id)
    if not entries:
        print("(no one is currently waitlisted for this vehicle)")
    else:
        rows = [
            [e.waitlist_id, e.customer_name, e.requested_pickup_date,
             e.requested_return_date, "Yes" if e.notified else "No"]
            for e in entries
        ]
        print(format_table(["ID", "Customer", "Requested Pickup", "Requested Return", "Notified"], rows))
    pause()


def _change_password(owner):
    print_header("CHANGE MY PASSWORD")
    try:
        reset_keyword = read_input("Enter reset keyword", "Ask your administrator for the reset keyword.")
        new_password = read_input("Enter New Password")
        confirm_password = read_input("Confirm New Password")
    except CancelOperation:
        return

    try:
        auth_service.reset_own_password(owner.username, reset_keyword, new_password, confirm_password)
    except ValueError as error:
        show_error(str(error))
        return

    show_success("Password successfully changed.")
