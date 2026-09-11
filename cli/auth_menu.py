"""
cli/auth_menu.py
==================

WHAT THIS FILE IS FOR:
The CLI screens for logging in, registering a new account (as Super Administrator,
Vehicle Owner/Driver, or Customer), and the self-service password reset flow -
matching the menu wireframes agreed in docs/assignment-1-nepal-car-rental-system-cli-spec.
"""

import config
from cli.common import print_header, print_divider, read_input, read_menu_choice, show_error, show_success, CancelOperation
from services import auth_service


def login_screen():
    """
    Shows the login screen. Returns the logged-in User object on success, or None
    if the user chose to go back (FR2).
    """
    print_header("USER LOGIN")
    try:
        username = read_input("Enter Username", "Type the username you registered with.")
        password = read_input("Enter Password", "Type your password. Type C to cancel.")
    except CancelOperation:
        return None

    try:
        user = auth_service.login(username, password)
    except ValueError as error:
        show_error(str(error))
        return None

    show_success(f"Login successful!\n\nWelcome, {user.role_label()}.")
    return user


def forgot_password_screen():
    """The simulated self-service password-reset flow (FR3)."""
    print_header("PASSWORD RESET")
    try:
        username = read_input("Enter Username")
        reset_keyword = read_input("Enter reset keyword", "Ask your administrator for the reset keyword.")
        new_password = read_input("Enter New Password")
        confirm_password = read_input("Confirm New Password")
    except CancelOperation:
        return

    try:
        auth_service.reset_own_password(username, reset_keyword, new_password, confirm_password)
    except ValueError as error:
        show_error(str(error))
        return

    show_success(f"Password successfully changed for '{username}'.\n\nPlease login again.")


def register_screen():
    """Shows the "choose registration type" menu, then runs the chosen sub-flow.

    FIX (requested by Anish): every registration keyword is now shown in plain,
    copy-pasteable text right here, up front, for all 3 roles at once - instead
    of only being revealed one at a time via the "H" help command inside each
    flow. The individual flow below also repeats its own single keyword right
    next to its prompt, so it's still visible at the exact moment it's needed.
    """
    print_header("USER REGISTRATION")
    print("Registration keywords (type the matching one at the end of that form):")
    print(f"  1. Super Administrator ..... {config.ADMIN_KEYWORD}")
    print(f"  2. Vehicle Owner / Driver .. {config.VEHICLE_OWNER_DRIVER_KEYWORD}")
    print(f"  3. Customer ................ {config.CUSTOMER_KEYWORD}")
    print()
    print("Choose registration type:\n")
    print("1. Super Administrator")
    print("2. Vehicle Owner / Driver")
    print("3. Customer")
    print("0. Back\n")
    choice = read_menu_choice()

    if choice == "1":
        _register_admin_flow()
    elif choice == "2":
        _register_owner_driver_flow()
    elif choice == "3":
        _register_customer_flow()
    elif choice == "0":
        return
    else:
        show_error("Invalid input. Please enter a number from the available menu options.")


def _register_admin_flow():
    # Every field below is REQUIRED (services/auth_service.py rejects an empty
    # value for all of them) - labelled explicitly here so it's clear on
    # screen, rather than only discovered after an error message. A short
    # "e.g. ..." example is added wherever the expected format isn't obvious
    # from the field name alone.
    print_header("SUPER ADMINISTRATOR REGISTRATION")
    print(f"(Administrator keyword for this form: {config.ADMIN_KEYWORD})\n")
    try:
        full_name = read_input("Full Name (required)")
        username = read_input("Username (required)")
        email = read_input("Email (required, e.g. name@gmail.com)")
        phone = read_input("Phone (required, e.g. 9800000000)")
        password = read_input("Password (required)")
        keyword = read_input(f"Enter Administrator Keyword (required - type: {config.ADMIN_KEYWORD})",
                              f"The Super Administrator keyword is: {config.ADMIN_KEYWORD}")
    except CancelOperation:
        return

    try:
        auth_service.register_admin(username, password, full_name, email, phone, keyword)
    except ValueError as error:
        show_error(str(error))
        return

    # FIX (reported bug): this message now (a) always clearly says whether the
    # registration succeeded, (b) greets the person by name and echoes back
    # their username so there is no doubt WHICH account was just created, and
    # (c) - via show_success() itself, see cli/common.py - holds the screen
    # with "Press Enter to continue..." so it can never scroll away unseen
    # behind the welcome menu's next redraw, which is what made it look like
    # nothing had happened at all before this fix.
    show_success(
        f"Thank you, {full_name}! Your Super Administrator account has been created "
        f"successfully.\n\nUsername : {username}\n"
        f"You can now go back and log in with this username and your password."
    )


def _register_owner_driver_flow():
    # Every field below is REQUIRED, including the daily driver rate - it must
    # still be typed even when it's just "0" (meaning "I only list vehicles,
    # I don't drive for hire"); it is not something you can leave blank.
    print_header("VEHICLE OWNER / DRIVER REGISTRATION")
    print(f"(Registration keyword for this form: {config.VEHICLE_OWNER_DRIVER_KEYWORD})\n")
    try:
        full_name = read_input("Full Name (required)")
        username = read_input("Username (required)")
        phone = read_input("Phone (required, e.g. 9800000000)")
        email = read_input("Email (required, e.g. name@gmail.com)")
        licence_no = read_input("Driving Licence Number (required, e.g. 345678-AKL)")
        licence_expiry = read_input("Licence Expiry Date (required, format YYYY-MM-DD, e.g. 2028-06-30)")
        daily_driver_rate = read_input(
            "Daily rate if hired as a driver (required - enter 0 if you only list vehicles)"
        )
        password = read_input("Password (required)")
        keyword = read_input(
            f"Enter Registration Keyword (required - type: {config.VEHICLE_OWNER_DRIVER_KEYWORD})",
            f"The Vehicle Owner/Driver keyword is: {config.VEHICLE_OWNER_DRIVER_KEYWORD}",
        )
    except CancelOperation:
        return

    try:
        auth_service.register_owner_driver(
            username, password, full_name, phone, email, licence_no,
            licence_expiry, daily_driver_rate, keyword,
        )
    except ValueError as error:
        show_error(str(error))
        return

    show_success(
        f"Thank you, {full_name}! Your Vehicle Owner / Driver account has been "
        f"created successfully.\n\nUsername : {username}\n"
        f"Your account is waiting for administrator approval - you will be able "
        f"to log in once it is approved."
    )


def _register_customer_flow():
    # Every field below is REQUIRED (services/auth_service.py rejects an empty
    # value for all of them) - this project has no optional fields in any of
    # the 3 registration forms at the moment, so every prompt says so plainly.
    print_header("CUSTOMER REGISTRATION")
    print(f"(Customer keyword for this form: {config.CUSTOMER_KEYWORD})\n")
    try:
        full_name = read_input("Full Name (required)")
        username = read_input("Username (required)")
        email = read_input("Email (required, e.g. name@gmail.com)")
        phone = read_input("Phone (required, e.g. 9800000000)")
        address = read_input("Address (required, e.g. Kathmandu, Nepal)")
        licence_no = read_input("Driving Licence Number (required, e.g. 345678-AKL)")
        password = read_input("Password (required)")
        keyword = read_input(f"Enter Customer Keyword (required - type: {config.CUSTOMER_KEYWORD})",
                              f"The Customer keyword is: {config.CUSTOMER_KEYWORD}")
    except CancelOperation:
        return

    try:
        auth_service.register_customer(
            username, password, full_name, phone, email, address, licence_no, keyword,
        )
    except ValueError as error:
        show_error(str(error))
        return

    show_success(
        f"Thank you, {full_name}! Your Customer account has been created "
        f"successfully.\n\nUsername : {username}\n"
        f"You can now go back and log in to search for and book available vehicles."
    )
