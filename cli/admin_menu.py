"""
cli/admin_menu.py
====================

WHAT THIS FILE IS FOR:
The full dashboard shown to a logged-in Super Administrator: the most powerful
role in the system. Covers user management (masked list + reset-any-password),
approving/rejecting new Vehicle Owner/Driver registrations, viewing the whole
vehicle fleet, managing every booking's lifecycle, recording/viewing payments,
system statistics, changing the system-wide rate-per-km, and the special "00 Reset
Test Data" command.

WHY "00" IS HANDLED HERE (not in cli/common.py's read_menu_choice):
"00" only makes sense for a Super Administrator, at the top level of their own
dashboard - it is deliberately NOT a universal command handled inside
read_menu_choice()/read_input(), so that no other role or screen can accidentally
trigger a full data wipe.
"""

from cli.common import (
    print_header, print_divider, read_input, read_menu_choice,
    confirm_yes_no, show_error, show_success, pause, CancelOperation,
)
from services import admin_service, vehicle_service, booking_service, payment_service, auth_service
from utils import validators
from utils.formatters import format_currency, format_table, mask_password

_MENU_HELP = (
    "Pick a number from the menu to run that action. Type 0 at this menu to log "
    "out and return to the welcome screen, or 00 to reset all demo data back to "
    "its original starting state (you will be asked to confirm first). Inside a "
    "form, type C to cancel that form and come back here, or H for field help."
)


def run(admin):
    """The Super Administrator dashboard loop. Runs until the admin logs out (0)."""
    while True:
        print_header("SUPER ADMINISTRATOR DASHBOARD")
        print("1. Manage Users (view + reset password)")
        print("2. Pending Registrations (approve / reject)")
        print("3. View All Vehicles")
        print("4. Manage Bookings")
        print("5. Record a Payment")
        print("6. View All Payments")
        print("7. System Statistics")
        print("8. Set Rate per KM")
        print("9. Change My Password")
        print("0.  Logout")
        print("00. Reset Test Data\n")
        choice = read_menu_choice()

        if choice == "1":
            _manage_users(admin)
        elif choice == "2":
            _pending_registrations(admin)
        elif choice == "3":
            _view_all_vehicles()
        elif choice == "4":
            _manage_bookings()
        elif choice == "5":
            _record_payment()
        elif choice == "6":
            _view_all_payments()
        elif choice == "7":
            _system_statistics(admin)
        elif choice == "8":
            _set_rate_per_km()
        elif choice == "9":
            _change_password(admin)
        elif choice == "0":
            print("\nGoodbye, Super Administrator. Logging out...\n")
            return
        elif choice == "00":
            _reset_test_data(admin)
        elif choice.upper() == "H":
            print(_MENU_HELP)
        else:
            show_error("Invalid input. Please enter a number from the available menu options.")


def _manage_users(admin):
    """
    Shows every account with its role/status and a fixed masked password
    placeholder (FR4a - real password hashes are never shown, and can never be
    turned back into the original password anyway), then offers to reset one
    user's password (FR4b).
    """
    print_header("MANAGE USERS")
    users = admin_service.list_all_users(admin)
    rows = [[u["username"], u["role"], u["status"], mask_password()] for u in users]
    print(format_table(["Username", "Role", "Status", "Password"], rows))

    if confirm_yes_no("\nWould you like to reset a user's password?"):
        _reset_user_password(admin)
    else:
        pause()


def _reset_user_password(admin):
    """
    The admin-only "reset any user's password" action. The admin may either type a
    specific new password, or leave it blank to have a random temporary one
    generated - either way, the new PLAIN-TEXT password is shown exactly once so
    the admin can pass it on, and only its hash is stored anywhere after that.
    """
    try:
        target_username = read_input("Enter the username whose password you want to reset")
        new_password = read_input(
            "Enter a new password (or leave blank to auto-generate one)",
            "Leaving this blank generates a random temporary password for the user.",
        )
    except CancelOperation:
        return

    try:
        new_password_or_none = new_password if new_password else None
        generated_password = auth_service.admin_reset_user_password(admin, target_username, new_password_or_none)
    except (ValueError, PermissionError) as error:
        show_error(str(error))
        return

    show_success(
        f"Password for '{target_username}' has been reset.\n\n"
        f"New password (shown once - please pass it on securely): {generated_password}"
    )


def _pending_registrations(admin):
    print_header("PENDING VEHICLE OWNER / DRIVER REGISTRATIONS")
    pending = admin_service.list_pending_registration_requests()
    if not pending:
        print("(there are no pending registrations right now)")
        pause()
        return

    rows = [[p["owner_driver_id"], p["full_name"], p["username"]] for p in pending]
    print(format_table(["Owner/Driver ID", "Full Name", "Username"], rows))

    try:
        owner_driver_id_str = read_input("\nEnter the Owner/Driver ID to approve or reject (or C to cancel)")
    except CancelOperation:
        return

    try:
        owner_driver_id = validators.validate_positive_int(owner_driver_id_str, "Owner/Driver ID")
    except ValueError as error:
        show_error(str(error))
        return

    decision = confirm_yes_no("Approve this registration? (No = reject it)")
    try:
        if decision:
            admin_service.approve_registration(admin, owner_driver_id)
            show_success("Registration approved. The account can now log in.")
        else:
            admin_service.reject_registration(admin, owner_driver_id)
            show_success("Registration rejected.")
    except ValueError as error:
        show_error(str(error))


def _view_all_vehicles():
    print_header("ALL VEHICLES")
    vehicles = vehicle_service.list_all_vehicles()
    rows = [
        [v.vehicle_id, v.display_name(), v.registration_no, v.vehicle_type,
         v.seats, format_currency(v.daily_rate), v.status]
        for v in vehicles
    ]
    print(format_table(["ID", "Vehicle", "Registration No.", "Type", "Seats", "Daily Rate", "Status"], rows))

    if confirm_yes_no("\nWould you like to change a vehicle's status (e.g. put it under maintenance)?"):
        _admin_update_vehicle_status()
    else:
        pause()


def _admin_update_vehicle_status():
    print(f"\nAllowed statuses: {', '.join(vehicle_service.VALID_STATUSES)}")
    try:
        vehicle_id_str = read_input("Enter the Vehicle ID")
        new_status = read_input("Enter the new status")
    except CancelOperation:
        return

    try:
        vehicle_id = validators.validate_positive_int(vehicle_id_str, "Vehicle ID")
        vehicle_service.update_vehicle_status(vehicle_id, new_status.upper())
    except ValueError as error:
        show_error(str(error))
        return

    show_success("Vehicle status updated successfully.")


def _manage_bookings():
    """
    Lets the admin browse bookings (optionally filtered by status) and move one
    through its lifecycle: confirm/reject a PENDING booking, or cancel/complete a
    CONFIRMED/ACTIVE one. Every status change is delegated to booking_service,
    which also takes care of freeing the vehicle and firing the waitlist
    auto-notify when appropriate.
    """
    print_header("MANAGE BOOKINGS")
    print("1. View All Bookings")
    print("2. View Bookings by Status")
    print("0. Back\n")
    choice = read_menu_choice()

    if choice == "1":
        bookings = booking_service.list_all_bookings()
    elif choice == "2":
        try:
            status = read_input(
                "Enter status (PENDING / CONFIRMED / ACTIVE / COMPLETED / CANCELLED / REJECTED)"
            )
        except CancelOperation:
            return
        bookings = booking_service.list_bookings_by_status(status.upper())
    elif choice == "0":
        return
    else:
        show_error("Invalid input. Please enter a number from the available menu options.")
        return

    if not bookings:
        print("(no bookings to show)")
        pause()
        return

    rows = [
        [b.booking_id, b.customer_id, b.vehicle_id, b.pickup_date, b.return_date,
         format_currency(b.total_amount), b.status]
        for b in bookings
    ]
    print(format_table(["ID", "Customer ID", "Vehicle ID", "Pickup", "Return", "Total", "Status"], rows))

    if confirm_yes_no("\nWould you like to update one of these bookings?"):
        _update_booking_status()
    else:
        pause()


def _update_booking_status():
    print("\n1. Confirm a PENDING booking")
    print("2. Reject a PENDING booking")
    print("3. Cancel a booking")
    print("4. Complete a booking")
    print("0. Back\n")
    action = read_menu_choice()
    if action == "0":
        return
    if action not in ("1", "2", "3", "4"):
        show_error("Invalid input. Please enter a number from the available menu options.")
        return

    try:
        booking_id_str = read_input("Enter the Booking ID")
    except CancelOperation:
        return

    try:
        booking_id = validators.validate_positive_int(booking_id_str, "Booking ID")
        if action == "1":
            booking_service.confirm_booking(booking_id)
            message = "confirmed"
        elif action == "2":
            booking_service.reject_booking(booking_id)
            message = "rejected"
        elif action == "3":
            booking_service.cancel_booking(booking_id)
            message = "cancelled"
        else:
            booking_service.complete_booking(booking_id)
            message = "completed"
    except ValueError as error:
        show_error(str(error))
        return

    show_success(f"Booking #{booking_id} has been {message}.")


def _record_payment():
    print_header("RECORD A PAYMENT")
    try:
        booking_id_str = read_input("Enter the Booking ID")
        amount_str = read_input("Amount")
        method = read_input("Payment method (CASH / CARD / BANK_TRANSFER)")
        status = read_input("Payment status (PENDING / PARTIAL / PAID)")
    except CancelOperation:
        return

    try:
        booking_id = validators.validate_positive_int(booking_id_str, "Booking ID")
        payment = payment_service.record_payment(booking_id, amount_str, method.upper(), status.upper())
    except ValueError as error:
        show_error(str(error))
        return

    show_success(f"Payment #{payment.payment_id} of {format_currency(payment.amount)} recorded.")


def _view_all_payments():
    print_header("ALL PAYMENTS")
    payments = payment_service.list_all_payments()
    rows = [
        [p.payment_id, p.booking_id, format_currency(p.amount), p.payment_date, p.method, p.status]
        for p in payments
    ]
    print(format_table(["ID", "Booking ID", "Amount", "Date", "Method", "Status"], rows))
    pause()


def _system_statistics(admin):
    print_header("SYSTEM STATISTICS")
    stats = admin_service.get_system_statistics(admin)
    print(f"Total Customers          : {stats['total_customers']}")
    print(f"Total Vehicles           : {stats['total_vehicles']}")
    print(f"Available Vehicles       : {stats['available_vehicles']}")
    print(f"Pending Bookings         : {stats['pending_bookings']}")
    print(f"Active Bookings          : {stats['active_bookings']}")
    print(f"Completed Bookings       : {stats['completed_bookings']}")
    print(f"Total Revenue (Paid)     : {format_currency(stats['total_revenue_paid'])}")
    print(f"Waitlist Entries Waiting : {stats['waitlist_entries_waiting']}")
    pause()


def _set_rate_per_km():
    print_header("SET RATE PER KM")
    current_rate = booking_service.get_current_rate_per_km()
    print(f"Current rate: {format_currency(current_rate)} per km\n")
    try:
        new_rate_str = read_input("Enter the new rate per km")
    except CancelOperation:
        return

    try:
        new_rate = booking_service.set_rate_per_km(new_rate_str)
    except ValueError as error:
        show_error(str(error))
        return

    show_success(f"Rate per km updated to {format_currency(new_rate)}. This applies to all NEW bookings.")


def _change_password(admin):
    print_header("CHANGE MY PASSWORD")
    try:
        reset_keyword = read_input("Enter reset keyword", "Ask your administrator for the reset keyword.")
        new_password = read_input("Enter New Password")
        confirm_password = read_input("Confirm New Password")
    except CancelOperation:
        return

    try:
        auth_service.reset_own_password(admin.username, reset_keyword, new_password, confirm_password)
    except ValueError as error:
        show_error(str(error))
        return

    show_success("Password successfully changed.")


def _reset_test_data(admin):
    """The "00 Reset Test Data" command (BR5) - wipes and re-seeds the database,
    after an explicit Yes/No confirmation so it can never happen by accident."""
    print_header("RESET TEST DATA")
    print("This will DELETE all current data and restore the original demo dataset.")
    if not confirm_yes_no("Are you absolutely sure you want to continue?"):
        print("\nCancelled - no data was changed.\n")
        return

    admin_service.reset_test_data(admin)
    show_success("Test data has been reset to its original starting state.")
