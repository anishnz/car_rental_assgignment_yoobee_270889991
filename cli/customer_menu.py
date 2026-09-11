"""
cli/customer_menu.py
======================

WHAT THIS FILE IS FOR:
The full dashboard shown to a logged-in Customer: browsing/searching vehicles,
booking one, joining a waitlist, viewing "my bookings", making a payment, and
changing password. This is the file that ties together vehicle_service,
booking_service, waitlist_service, and payment_service for the Customer role.
"""

from cli.common import (
    print_header, print_divider, read_input, read_menu_choice,
    confirm_yes_no, show_error, show_success, pause, CancelOperation,
)
from services import vehicle_service, booking_service, waitlist_service, payment_service, auth_service
from utils import validators
from utils.formatters import format_currency, format_table

_MENU_HELP = (
    "Pick a number from the menu to run that action. Type 0 at this menu to log "
    "out and return to the welcome screen. Inside a form, type C to cancel that "
    "form and come back here, or H to see help for the field you are on."
)


def run(customer):
    """
    The Customer dashboard loop. `customer` is a models.user.Customer instance
    (built by services/auth_service.login()). Runs until the customer chooses to
    log out (0).
    """
    while True:
        print_header(f"CUSTOMER DASHBOARD - {customer.full_name}")
        print("1. Browse Available Vehicles")
        print("2. Search Vehicles")
        print("3. Book a Vehicle")
        print("4. My Bookings")
        print("5. Make a Payment")
        print("6. Join a Vehicle's Waitlist")
        print("7. Change My Password")
        print("0. Logout\n")
        choice = read_menu_choice()

        if choice == "1":
            _browse_available_vehicles()
        elif choice == "2":
            _search_vehicles()
        elif choice == "3":
            _book_a_vehicle(customer)
        elif choice == "4":
            _my_bookings(customer)
        elif choice == "5":
            _make_a_payment(customer)
        elif choice == "6":
            _join_waitlist(customer)
        elif choice == "7":
            _change_password(customer)
        elif choice == "0":
            print(f"\nGoodbye, {customer.full_name}. Logging out...\n")
            return
        elif choice.upper() == "H":
            print(_MENU_HELP)
        else:
            show_error("Invalid input. Please enter a number from the available menu options.")


def _vehicle_table_rows(vehicles):
    """Shared helper: turns a list of Vehicle objects into table rows for display."""
    return [
        [v.vehicle_id, v.display_name(), v.vehicle_type, v.seats,
         format_currency(v.daily_rate), v.status]
        for v in vehicles
    ]


_VEHICLE_HEADERS = ["ID", "Vehicle", "Type", "Seats", "Daily Rate", "Status"]


def _browse_available_vehicles():
    print_header("AVAILABLE VEHICLES")
    vehicles = vehicle_service.list_available_vehicles()
    print(format_table(_VEHICLE_HEADERS, _vehicle_table_rows(vehicles)))
    pause()


def _search_vehicles():
    print_header("SEARCH VEHICLES")
    try:
        keyword = read_input("Search by brand, model, or registration number")
    except CancelOperation:
        return
    vehicles = vehicle_service.search_vehicles(keyword)
    print(format_table(_VEHICLE_HEADERS, _vehicle_table_rows(vehicles)))
    pause()


def _book_a_vehicle(customer):
    """
    The full booking flow (FR10-FR13): shows available vehicles, collects the
    booking details, checks availability, calculates the cost, and creates the
    booking. If the requested dates conflict with an existing booking, offers to
    join that vehicle's waitlist instead (FR16).
    """
    print_header("BOOK A VEHICLE")
    vehicles = vehicle_service.list_available_vehicles()
    if not vehicles:
        show_error("There are no available vehicles right now. Please check back later.")
        return
    print(format_table(_VEHICLE_HEADERS, _vehicle_table_rows(vehicles)))

    try:
        vehicle_id_str = read_input("\nEnter the Vehicle ID you want to book")
        pickup_str = read_input("Pickup date (YYYY-MM-DD)")
        return_str = read_input("Return date (YYYY-MM-DD)")
        distance_str = read_input("Estimated distance for the trip (km)")
        driver_choice = read_input("Do you need a driver? (Y/N)")
    except CancelOperation:
        return

    try:
        vehicle_id = validators.validate_positive_int(vehicle_id_str, "Vehicle ID")
        driver_required = driver_choice.strip().upper() == "Y"
    except ValueError as error:
        show_error(str(error))
        return

    driver_id = None
    if driver_required:
        driver_id = _choose_driver()
        if driver_id is None:
            show_error("No driver was selected. Booking cancelled.")
            return

    try:
        pickup_date, return_date = validators.validate_date_range(pickup_str, return_str)
    except ValueError as error:
        show_error(str(error))
        return

    if not booking_service.check_vehicle_availability(vehicle_id, pickup_date, return_date):
        show_error(
            "Sorry! This vehicle is not available for the selected dates.\n"
            "You can join its waitlist from the main menu (option 6) to be "
            "notified automatically when it becomes free."
        )
        if confirm_yes_no("Would you like to join the waitlist for this vehicle now?"):
            waitlist_service.join_waitlist(customer, vehicle_id, pickup_date, return_date)
            show_success("You have been added to the waitlist for this vehicle.")
        return

    try:
        booking = booking_service.create_booking(
            customer, vehicle_id, pickup_str, return_str, distance_str,
            driver_required, driver_id,
        )
    except ValueError as error:
        show_error(str(error))
        return

    show_success(
        f"Booking #{booking.booking_id} created successfully!\n\n"
        f"Status         : {booking.status} (awaiting administrator confirmation)\n"
        f"Number of days : {booking.number_of_days}\n"
        f"Total cost     : {format_currency(booking.total_amount)}"
    )


def _choose_driver():
    """Shows the list of available drivers and lets the customer pick one by ID.
    Returns the chosen owner_driver_id, or None if there was nothing to choose."""
    drivers = booking_service.list_available_drivers()
    if not drivers:
        show_error("No drivers are currently available.")
        return None

    print("\nAvailable drivers:")
    rows = [[d["owner_driver_id"], d["full_name"], format_currency(d["daily_driver_rate"])] for d in drivers]
    print(format_table(["Driver ID", "Full Name", "Daily Rate"], rows))

    try:
        driver_id_str = read_input("Enter the Driver ID you want to hire")
    except CancelOperation:
        return None

    try:
        return validators.validate_positive_int(driver_id_str, "Driver ID")
    except ValueError as error:
        show_error(str(error))
        return None


def _my_bookings(customer):
    """Shows every booking belonging to this customer, and offers to cancel one."""
    print_header("MY BOOKINGS")
    bookings = booking_service.list_bookings_for_customer(customer.customer_id)
    if not bookings:
        print("(you have no bookings yet)")
        pause()
        return

    rows = []
    for booking in bookings:
        # A vehicle can (rarely) be deleted later by its owner once every booking
        # against it is finished (see vehicle_service.delete_vehicle()) - so this
        # is guarded rather than assumed to always succeed, to avoid crashing a
        # customer's own booking history over a vehicle that no longer exists.
        try:
            vehicle_name = vehicle_service.get_vehicle(booking.vehicle_id).display_name()
        except ValueError:
            vehicle_name = "(vehicle no longer in system)"
        rows.append([
            booking.booking_id, vehicle_name, booking.pickup_date,
            booking.return_date, booking.distance_km,
            format_currency(booking.total_amount), booking.status,
        ])
    print(format_table(
        ["ID", "Vehicle", "Pickup", "Return", "Distance (km)", "Total", "Status"], rows
    ))

    if confirm_yes_no("\nWould you like to cancel one of these bookings?"):
        try:
            booking_id_str = read_input("Enter the Booking ID to cancel")
            booking_id = validators.validate_positive_int(booking_id_str, "Booking ID")
        except (CancelOperation, ValueError) as error:
            if isinstance(error, ValueError):
                show_error(str(error))
            return
        try:
            booking_service.cancel_booking(booking_id)
        except ValueError as error:
            show_error(str(error))
            return
        show_success(f"Booking #{booking_id} has been cancelled.")
    else:
        pause()


def _make_a_payment(customer):
    """
    Records a simulated payment against one of the customer's own bookings (FR18).
    The payment status (PAID/PARTIAL) is worked out automatically by comparing the
    amount paid to the booking's total, rather than asking the customer to
    self-report it.
    """
    print_header("MAKE A PAYMENT")
    try:
        booking_id_str = read_input("Enter your Booking ID")
    except CancelOperation:
        return

    try:
        booking_id = validators.validate_positive_int(booking_id_str, "Booking ID")
        booking = booking_service.get_booking(booking_id)
    except ValueError as error:
        show_error(str(error))
        return

    if booking.customer_id != customer.customer_id:
        show_error("That booking does not belong to your account.")
        return

    already_paid = sum(
        p.amount for p in payment_service.list_payments_for_booking(booking_id) if p.status == "PAID"
    )
    outstanding = booking.total_amount - already_paid
    print(f"\nBooking total : {format_currency(booking.total_amount)}")
    print(f"Already paid  : {format_currency(already_paid)}")
    print(f"Outstanding   : {format_currency(outstanding)}\n")

    try:
        amount_str = read_input("Amount to pay now")
        method = read_input("Payment method (CASH / CARD / BANK_TRANSFER)")
    except CancelOperation:
        return

    try:
        # Validated here ONLY to decide PAID vs PARTIAL below - the raw text
        # (amount_str) is what actually gets passed to record_payment(), which
        # does its own validation from a string, same as every other caller.
        amount_for_status_check = validators.validate_positive_number(amount_str, "Payment amount")
    except ValueError as error:
        show_error(str(error))
        return

    status = "PAID" if (already_paid + amount_for_status_check) >= booking.total_amount else "PARTIAL"

    try:
        payment = payment_service.record_payment(booking_id, amount_str, method.upper(), status)
    except ValueError as error:
        show_error(str(error))
        return

    show_success(
        f"Payment of {format_currency(payment.amount)} recorded "
        f"({payment.method}, status: {payment.status})."
    )


def _join_waitlist(customer):
    print_header("JOIN A VEHICLE'S WAITLIST")
    try:
        vehicle_id_str = read_input("Enter the Vehicle ID you want to wait for")
        pickup_str = read_input("Your desired pickup date (YYYY-MM-DD)")
        return_str = read_input("Your desired return date (YYYY-MM-DD)")
    except CancelOperation:
        return

    try:
        vehicle_id = validators.validate_positive_int(vehicle_id_str, "Vehicle ID")
        vehicle_service.get_vehicle(vehicle_id)  # raises ValueError if it doesn't exist
        pickup_date, return_date = validators.validate_date_range(pickup_str, return_str)
    except ValueError as error:
        show_error(str(error))
        return

    waitlist_service.join_waitlist(customer, vehicle_id, pickup_date, return_date)
    show_success("You have been added to the waitlist. You will be notified here if you log in after it opens up.")


def _change_password(customer):
    """
    Lets a logged-in customer change their own password. Still goes through the
    same keyword-gated reset_own_password() function used by the "forgot password"
    screen (see services/auth_service.py) - this keeps password-changing logic in
    exactly one place, whether the customer is logged in or not.
    """
    print_header("CHANGE MY PASSWORD")
    try:
        reset_keyword = read_input("Enter reset keyword", "Ask your administrator for the reset keyword.")
        new_password = read_input("Enter New Password")
        confirm_password = read_input("Confirm New Password")
    except CancelOperation:
        return

    try:
        auth_service.reset_own_password(customer.username, reset_keyword, new_password, confirm_password)
    except ValueError as error:
        show_error(str(error))
        return

    show_success("Password successfully changed.")
