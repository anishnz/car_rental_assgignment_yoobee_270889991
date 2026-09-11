"""
cli/public_menu.py
=====================

WHAT THIS FILE IS FOR:
The very first screen anyone sees when the program starts (the "Welcome Screen").
Lets a not-yet-logged-in person log in, register a new account, browse available
vehicles/car types/rental information WITHOUT logging in (a "Guest" capability -
see FR1/FR7), or read the About screen. Once someone logs in successfully, this is
also what DISPATCHES them to the correct role dashboard (Admin/Owner/Customer)
using Python's `isinstance()` - a small, practical use of polymorphism: this
function does not need a big if/elif chain checking `user.role == "..."` strings;
it simply asks "what kind of object is this?" and routes accordingly.
"""

from cli.common import print_header, print_divider, read_menu_choice, show_error, pause
from cli import auth_menu, about_screen, admin_menu, owner_menu, customer_menu
from models.user import Admin, VehicleOwnerDriver, Customer
from services import vehicle_service
from utils.formatters import format_currency, format_table
import config

_MENU_HELP = (
    "Pick a number from the menu below. You do not need an account to browse "
    "vehicles, car types, or rental information - only to log in or book a car. "
    "Type 0 to exit the program from this screen."
)


def run():
    """
    The main welcome-screen loop. This is the function main.py calls to start the
    whole CLI. Returns only when the user chooses to exit (0).
    """
    while True:
        print_header(config.PROJECT_NAME)
        print("1. Login")
        print("2. Register")
        print("3. View Available Vehicles")
        print("4. View Vehicles by Car Type")
        print("5. View Rental Information")
        print("6. About This Project")
        print("0. Exit\n")
        choice = read_menu_choice()

        if choice == "1":
            _login_and_dispatch()
        elif choice == "2":
            auth_menu.register_screen()
        elif choice == "3":
            _view_available_vehicles()
        elif choice == "4":
            _view_vehicles_by_type()
        elif choice == "5":
            _view_rental_information()
        elif choice == "6":
            about_screen.show_about_screen()
        elif choice == "0":
            print("\nThank you for using " + config.PROJECT_NAME + ". Goodbye!\n")
            return
        elif choice.upper() == "H":
            print(_MENU_HELP)
        else:
            show_error("Invalid input. Please enter a number from the available menu options.")


def _login_and_dispatch():
    """
    Runs the login screen, and - if it succeeds - hands control to the correct
    role dashboard until that user logs out, then returns here to the welcome
    screen. If login fails or is cancelled, auth_menu.login_screen() returns None
    and this simply falls back to showing the welcome menu again.
    """
    user = auth_menu.login_screen()
    if user is None:
        return

    # POLYMORPHISM / DISPATCH: rather than checking `user.role == "ADMIN"` (a
    # fragile string comparison repeated everywhere), we ask what concrete User
    # subclass this object actually is, and hand it to the matching dashboard.
    if isinstance(user, Admin):
        admin_menu.run(user)
    elif isinstance(user, VehicleOwnerDriver):
        owner_menu.run(user)
    elif isinstance(user, Customer):
        customer_menu.run(user)
    else:
        show_error("This account's role is not recognised by the system.")


def _view_available_vehicles():
    print_header("AVAILABLE VEHICLES")
    vehicles = vehicle_service.list_available_vehicles()
    rows = [
        [v.vehicle_id, v.display_name(), v.vehicle_type, v.seats, format_currency(v.daily_rate)]
        for v in vehicles
    ]
    print(format_table(["ID", "Vehicle", "Type", "Seats", "Daily Rate"], rows))
    print("\nLogin or register as a Customer to book one of these vehicles.")
    pause()


def _view_vehicles_by_type():
    print_header("VEHICLES BY CAR TYPE")
    print(f"Available types: {', '.join(vehicle_service.VALID_TYPES)}\n")
    vehicle_type = input("Enter a car type: ").strip()
    vehicles = vehicle_service.list_vehicles_by_type(vehicle_type)
    rows = [
        [v.vehicle_id, v.display_name(), v.seats, format_currency(v.daily_rate)]
        for v in vehicles
    ]
    print(format_table(["ID", "Vehicle", "Seats", "Daily Rate"], rows))
    pause()


def _view_rental_information():
    """A static information screen explaining how renting works, the pricing
    formula, and the universal navigation commands - useful for a first-time
    guest before they decide to register (FR - rental information)."""
    print_header("RENTAL INFORMATION")
    print("How renting works:")
    print("  1. Register as a Customer (or login if you already have an account).")
    print("  2. Browse the available vehicles and choose one that suits you.")
    print("  3. Provide your pickup date, return date, and estimated distance (km).")
    print("  4. Choose whether you need a driver as well.")
    print("  5. Your booking is created as PENDING until an administrator confirms it.")
    print_divider()
    print("Pricing formula:")
    print("  Total Cost = (Days x Daily Vehicle Rate)")
    print("             + (Distance in km x Rate per km)")
    print("             + (Days x Driver Daily Rate, only if a driver is requested)")
    print(f"  All prices are shown in {config.CURRENCY_SYMBOL} (New Zealand Dollars).")
    print_divider()
    print("Navigation, from any prompt in this program:")
    print("  0      Back / Logout / Exit")
    print("  00     Reset test data (Super Administrator dashboard only)")
    print("  H      Show help for the current field")
    print("  C      Cancel the current multi-step form")
    print("  Ctrl+C Safely exit the program at any time")
    pause()
