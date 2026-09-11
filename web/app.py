"""
web/app.py
===========

WHAT THIS FILE IS FOR:
A small Flask web application that gives the Nepal Car Rental System (NCRS) a
second, browser-based way to run - full CRUD (Create, Read, Update, Delete) for
vehicles, bookings, registrations, users, and payments, as simple HTML pages
with buttons and forms, in addition to the original command-line interface.

WHY THIS IS AN ADDITION, NOT A REPLACEMENT:
This file deliberately does NOT contain any business logic of its own. Every
single action below (logging in, registering, adding a vehicle, confirming a
booking, recording a payment...) calls the exact same functions in services/
that the CLI (cli/*.py) already calls, against the exact same database file.
That means:
  - The CLI keeps working exactly as it did before - nothing in cli/, services/,
    models/, database/, or utils/ business logic was changed to build this.
  - There is only ONE copy of every rule (validation, pricing formula, who is
    allowed to do what) anywhere in the whole project - here or in the CLI.
    Whoever runs the program, from a terminal or from a browser, gets IDENTICAL
    behaviour, because both are thin "front ends" over the same services/ layer.
  - Anything you do from one interface (e.g. add a vehicle from the browser) is
    immediately visible from the other (e.g. it shows up in the CLI too),
    because they share the one SQLite database file.

WHY FLASK:
Flask is a small, beginner-friendly Python web framework - no separate server
software, no database driver of its own to install, and no JavaScript build
step. Running "python web/app.py" starts a small local web server; opening
http://127.0.0.1:5000 in ANY browser on the same computer talks to it. Nothing
here calls out to the internet, so it runs fully offline, exactly like the CLI.

HOW LOGIN WORKS HERE (different from the CLI):
The CLI keeps the logged-in User object alive in one Python variable for as
long as that dashboard's menu loop keeps running. A web server cannot do that
- every click is a brand new, independent HTTP request with no memory of the
previous one. The standard fix (used here) is a SESSION: after a successful
login, Flask writes a small, signed cookie to the browser containing nothing
but the user's numeric ID. On every later request, before_request() below reads
that ID back out of the cookie and calls auth_service.get_user_by_id() to
rebuild the real User object fresh from the database - so `g.user` is always
correct and up to date, without ever storing a password (or even the object
itself) in the cookie.
"""

import os
import sys
from datetime import date
from functools import wraps

from flask import Flask, g, redirect, render_template, request, session, url_for, flash

# --- Make the project's top-level packages (services/models/database/utils/config)
# importable, regardless of the current working directory this script is run
# from. web/app.py lives one folder BELOW the project root, so its own folder's
# parent is the project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config
from services.rental_system import RentalSystem
from services import (
    auth_service, admin_service, vehicle_service, booking_service,
    waitlist_service, payment_service,
)
from models.user import Admin, VehicleOwnerDriver, Customer
from models.payment import Payment
from models.vehicle import Vehicle as VehicleModel
from utils.formatters import format_currency, mask_password


app = Flask(__name__)
# A fixed local secret key is fine here: this app only ever runs on the
# student's own computer (NFR1/NFR2 - fully offline, no real deployment), so
# there is no real attacker who could ever see this cookie traffic. A real
# production deployment would instead read this from an environment variable.
app.secret_key = "ncrs-web-local-secret-key-not-for-production"

# Starts the whole system the same way main.py does: creates the database
# connection (Singleton - see database/db_connection.py), builds the tables if
# they don't exist yet, and seeds the demo data on a first run.
RentalSystem.get_instance()

app.jinja_env.filters["currency"] = format_currency


# ---------------------------------------------------------------------------
# DEMO LOGIN ACCOUNTS
# ---------------------------------------------------------------------------
# The exact three demo accounts that database/seed_data.py always creates on a
# fresh database (see _seed_users() there for the full list, including the
# extras - owner_hari is left PENDING approval on purpose, so it cannot log in
# yet, and driver_bikash is a second owner account not needed for a quick demo).
# Shown directly on the login page, with one-click "Log in as..." buttons, so
# nobody giving a demo (or marking this assignment) has to remember or type a
# password. This list is display-only - it does not create or change any
# account; the real accounts and password hashes still come from seed_data.py.
DEMO_ACCOUNTS = [
    {"role_label": "Super Administrator", "username": "admin_ncrs", "password": "Admin@123"},
    {"role_label": "Vehicle Owner / Driver", "username": "owner_ram", "password": "Owner@123"},
    {"role_label": "Customer", "username": "customer_sita", "password": "Customer@123"},
]

# The 3 registration keywords (see config.py) shown as plain, copy-pasteable
# text on the registration pages - the register_choice.html "choose a role"
# page shows all 3 together, and each individual register_*.html form repeats
# its own one right next to the keyword field, matching the CLI's
# register_screen()/​_register_*_flow() equivalent (cli/auth_menu.py).
REGISTRATION_KEYWORDS = [
    {"role_label": "Super Administrator", "keyword": config.ADMIN_KEYWORD},
    {"role_label": "Vehicle Owner / Driver", "keyword": config.VEHICLE_OWNER_DRIVER_KEYWORD},
    {"role_label": "Customer", "keyword": config.CUSTOMER_KEYWORD},
]


# ---------------------------------------------------------------------------
# SESSION / CURRENT-USER HELPERS
# ---------------------------------------------------------------------------

@app.before_request
def load_logged_in_user():
    """Runs before EVERY request. Rebuilds the real User object (if any) from
    the session's stored user_id - see the module docstring above for why."""
    user_id = session.get("user_id")
    g.user = auth_service.get_user_by_id(user_id) if user_id else None


@app.context_processor
def inject_globals():
    """Makes these available in every template without passing them
    explicitly from every single route - avoids repeating the same four lines
    in 25+ view functions."""
    return {
        "project_name": config.PROJECT_NAME,
        "currency_symbol": config.CURRENCY_SYMBOL,
        "current_user": g.get("user"),
        "mask_password": mask_password,
        "demo_accounts": DEMO_ACCOUNTS,
        "registration_keywords": REGISTRATION_KEYWORDS,
    }


def login_required(view):
    """Decorator: redirects to /login if nobody is logged in."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    """Decorator: like login_required, but also checks the logged-in user's
    role is one of `roles` (e.g. @role_required('ADMIN')). Mirrors the CLI's
    isinstance() dispatch in cli/public_menu.py - same rule, same reason."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                flash("Please log in first.", "error")
                return redirect(url_for("login"))
            if g.user.role not in roles:
                flash("You do not have permission to view that page.", "error")
                return redirect(url_for("home"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def flash_value_error(error: ValueError):
    flash(str(error), "error")


# ---------------------------------------------------------------------------
# PUBLIC PAGES (no login required) - mirrors cli/public_menu.py
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            user = auth_service.login(username, password)
        except ValueError as error:
            flash_value_error(error)
            return render_template("login.html")

        session["user_id"] = user.user_id
        flash(f"Login successful! Welcome, {user.role_label()}.", "success")
        if isinstance(user, Admin):
            return redirect(url_for("admin_dashboard"))
        if isinstance(user, VehicleOwnerDriver):
            return redirect(url_for("owner_dashboard"))
        if isinstance(user, Customer):
            return redirect(url_for("customer_dashboard"))
        flash("This account's role is not recognised by the system.", "error")
        return redirect(url_for("home"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        try:
            auth_service.reset_own_password(
                request.form.get("username", ""),
                request.form.get("reset_keyword", ""),
                request.form.get("new_password", ""),
                request.form.get("confirm_password", ""),
            )
        except ValueError as error:
            flash_value_error(error)
            return render_template("forgot_password.html")
        flash("Password successfully changed. Please login again.", "success")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")


@app.route("/register")
def register_choice():
    return render_template("register_choice.html")


@app.route("/register/admin", methods=["GET", "POST"])
def register_admin():
    if request.method == "POST":
        full_name = request.form.get("full_name", "")
        username = request.form.get("username", "")
        try:
            auth_service.register_admin(
                username, request.form.get("password", ""), full_name,
                request.form.get("email", ""), request.form.get("phone", ""),
                request.form.get("keyword", ""),
            )
        except ValueError as error:
            flash_value_error(error)
            return render_template("register_admin.html")
        flash(
            f"Thank you, {full_name}! Your Super Administrator account has been "
            f"created successfully.\n\nUsername: {username}\n"
            f"You can now log in with this username and your password.",
            "success",
        )
        return redirect(url_for("login"))
    return render_template("register_admin.html")


@app.route("/register/owner", methods=["GET", "POST"])
def register_owner():
    if request.method == "POST":
        full_name = request.form.get("full_name", "")
        username = request.form.get("username", "")
        try:
            auth_service.register_owner_driver(
                username, request.form.get("password", ""), full_name,
                request.form.get("phone", ""), request.form.get("email", ""),
                request.form.get("licence_no", ""), request.form.get("licence_expiry", ""),
                request.form.get("daily_driver_rate", "0"), request.form.get("keyword", ""),
            )
        except ValueError as error:
            flash_value_error(error)
            return render_template("register_owner.html")
        flash(
            f"Thank you, {full_name}! Your Vehicle Owner / Driver account has been "
            f"created successfully.\n\nUsername: {username}\n"
            f"Your account is waiting for administrator approval - you will be "
            f"able to log in once it is approved.",
            "success",
        )
        return redirect(url_for("login"))
    return render_template("register_owner.html")


@app.route("/register/customer", methods=["GET", "POST"])
def register_customer():
    if request.method == "POST":
        full_name = request.form.get("full_name", "")
        username = request.form.get("username", "")
        try:
            auth_service.register_customer(
                username, request.form.get("password", ""), full_name,
                request.form.get("phone", ""), request.form.get("email", ""),
                request.form.get("address", ""), request.form.get("licence_no", ""),
                request.form.get("keyword", ""),
            )
        except ValueError as error:
            flash_value_error(error)
            return render_template("register_customer.html")
        flash(
            f"Thank you, {full_name}! Your Customer account has been created "
            f"successfully.\n\nUsername: {username}\n"
            f"You can now log in to search for and book available vehicles.",
            "success",
        )
        return redirect(url_for("login"))
    return render_template("register_customer.html")


@app.route("/vehicles")
def vehicles_public():
    return render_template("vehicles_public.html", vehicles=vehicle_service.list_available_vehicles())


@app.route("/vehicles/by-type")
def vehicles_by_type():
    selected_type = request.args.get("type", "")
    vehicles = vehicle_service.list_vehicles_by_type(selected_type) if selected_type else []
    return render_template(
        "vehicles_by_type.html", valid_types=vehicle_service.VALID_TYPES,
        selected_type=selected_type, vehicles=vehicles,
    )


@app.route("/rental-info")
def rental_info():
    return render_template("rental_info.html")


@app.route("/about")
def about():
    return render_template(
        "about.html", cfg=config,
        author_meta={
            "author": getattr(RentalSystem, "__author__", "n/a"),
            "student_id": getattr(RentalSystem, "__student_id__", "n/a"),
            "institution": getattr(RentalSystem, "__institution__", "n/a"),
        },
    )


# ---------------------------------------------------------------------------
# SHARED "CHANGE MY PASSWORD" PAGE - used by all 3 logged-in roles
# (mirrors _change_password() being copy-identical in admin/owner/customer
# menu.py on the CLI side - one template + one route instead of three).
# ---------------------------------------------------------------------------

_DASHBOARD_BY_ROLE = {
    "admin": ("admin_dashboard", "ADMIN"),
    "owner": ("owner_dashboard", "OWNER_DRIVER"),
    "customer": ("customer_dashboard", "CUSTOMER"),
}


@app.route("/change-password/<role>", methods=["GET", "POST"])
@login_required
def change_password(role):
    dashboard_endpoint, expected_role = _DASHBOARD_BY_ROLE.get(role, (None, None))
    if dashboard_endpoint is None or g.user.role != expected_role:
        flash("You do not have permission to view that page.", "error")
        return redirect(url_for("home"))

    dashboard_url = url_for(dashboard_endpoint)
    if request.method == "POST":
        try:
            auth_service.reset_own_password(
                g.user.username, request.form.get("reset_keyword", ""),
                request.form.get("new_password", ""), request.form.get("confirm_password", ""),
            )
        except ValueError as error:
            flash_value_error(error)
            return render_template("change_password.html", dashboard_url=dashboard_url)
        flash("Password successfully changed.", "success")
        return redirect(dashboard_url)
    return render_template("change_password.html", dashboard_url=dashboard_url)


# ---------------------------------------------------------------------------
# ADMIN PAGES - mirrors cli/admin_menu.py
# ---------------------------------------------------------------------------

@app.route("/admin")
@role_required("ADMIN")
def admin_dashboard():
    return render_template("admin_dashboard.html")


@app.route("/admin/users")
@role_required("ADMIN")
def admin_users():
    return render_template("admin_users.html", users=admin_service.list_all_users(g.user))


@app.route("/admin/users/reset-password", methods=["POST"])
@role_required("ADMIN")
def admin_reset_user_password():
    target_username = request.form.get("target_username", "")
    new_password = request.form.get("new_password") or None
    try:
        generated_password = auth_service.admin_reset_user_password(g.user, target_username, new_password)
    except (ValueError, PermissionError) as error:
        flash_value_error(error)
        return redirect(url_for("admin_users"))
    flash(
        f"Password for '{target_username}' has been reset.\n\n"
        f"New password (shown once - please pass it on securely): {generated_password}",
        "success",
    )
    return redirect(url_for("admin_users"))


@app.route("/admin/registrations")
@role_required("ADMIN")
def admin_registrations():
    return render_template("admin_registrations.html", pending=admin_service.list_pending_registration_requests())


@app.route("/admin/registrations/<int:owner_driver_id>/approve", methods=["POST"])
@role_required("ADMIN")
def admin_approve_registration(owner_driver_id):
    try:
        admin_service.approve_registration(g.user, owner_driver_id)
        flash("Registration approved. The account can now log in.", "success")
    except ValueError as error:
        flash_value_error(error)
    return redirect(url_for("admin_registrations"))


@app.route("/admin/registrations/<int:owner_driver_id>/reject", methods=["POST"])
@role_required("ADMIN")
def admin_reject_registration(owner_driver_id):
    try:
        admin_service.reject_registration(g.user, owner_driver_id)
        flash("Registration rejected.", "success")
    except ValueError as error:
        flash_value_error(error)
    return redirect(url_for("admin_registrations"))


@app.route("/admin/vehicles")
@role_required("ADMIN")
def admin_vehicles():
    return render_template(
        "admin_vehicles.html", vehicles=vehicle_service.list_all_vehicles(),
        valid_statuses=vehicle_service.VALID_STATUSES,
    )


@app.route("/admin/vehicles/<int:vehicle_id>/status", methods=["POST"])
@role_required("ADMIN")
def admin_update_vehicle_status(vehicle_id):
    try:
        vehicle_service.update_vehicle_status(vehicle_id, request.form.get("status", ""))
        flash("Vehicle status updated successfully.", "success")
    except ValueError as error:
        flash_value_error(error)
    return redirect(url_for("admin_vehicles"))


@app.route("/admin/bookings")
@role_required("ADMIN")
def admin_bookings():
    selected_status = request.args.get("status", "")
    if selected_status:
        bookings = booking_service.list_bookings_by_status(selected_status)
    else:
        bookings = booking_service.list_all_bookings()
    return render_template(
        "admin_bookings.html", bookings=bookings, selected_status=selected_status,
        valid_statuses=("PENDING", "CONFIRMED", "ACTIVE", "COMPLETED", "CANCELLED", "REJECTED"),
    )


_BOOKING_ACTIONS = {
    "confirm": (booking_service.confirm_booking, "confirmed"),
    "reject": (booking_service.reject_booking, "rejected"),
    "cancel": (booking_service.cancel_booking, "cancelled"),
    "complete": (booking_service.complete_booking, "completed"),
}


@app.route("/admin/bookings/<int:booking_id>/<action>", methods=["POST"])
@role_required("ADMIN")
def admin_booking_action(booking_id, action):
    handler = _BOOKING_ACTIONS.get(action)
    if handler is None:
        flash("Unknown booking action.", "error")
        return redirect(url_for("admin_bookings"))
    func, past_tense = handler
    try:
        func(booking_id)
        flash(f"Booking #{booking_id} has been {past_tense}.", "success")
    except ValueError as error:
        flash_value_error(error)
    return redirect(url_for("admin_bookings"))


@app.route("/admin/payments", methods=["GET", "POST"])
@role_required("ADMIN")
def admin_payments():
    if request.method == "POST":
        try:
            booking_id = int(request.form.get("booking_id", "0"))
            payment_service.record_payment(
                booking_id, request.form.get("amount", ""),
                request.form.get("method", ""), request.form.get("status", ""),
            )
            flash(f"Payment recorded for booking #{booking_id}.", "success")
        except ValueError as error:
            flash_value_error(error)
        return redirect(url_for("admin_payments"))

    return render_template(
        "admin_payments.html", payments=payment_service.list_all_payments(),
        valid_methods=Payment.VALID_METHODS, valid_statuses=Payment.VALID_STATUSES,
    )


@app.route("/admin/stats")
@role_required("ADMIN")
def admin_stats():
    return render_template("admin_stats.html", stats=admin_service.get_system_statistics(g.user))


@app.route("/admin/rate", methods=["GET", "POST"])
@role_required("ADMIN")
def admin_rate():
    if request.method == "POST":
        try:
            new_rate = booking_service.set_rate_per_km(request.form.get("new_rate", ""))
            flash(f"Rate per km updated to {format_currency(new_rate)}. This applies to all NEW bookings.", "success")
        except ValueError as error:
            flash_value_error(error)
        return redirect(url_for("admin_rate"))
    return render_template("admin_rate.html", current_rate=booking_service.get_current_rate_per_km())


@app.route("/admin/reset-test-data", methods=["POST"])
@role_required("ADMIN")
def admin_reset_test_data():
    admin_service.reset_test_data(g.user)
    flash("Test data has been reset to its original starting state.", "success")
    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------------------------
# OWNER / DRIVER PAGES - mirrors cli/owner_menu.py
# ---------------------------------------------------------------------------

def _get_own_vehicle_or_none(vehicle_id):
    """Web equivalent of cli/owner_menu.py's _get_own_vehicle_or_error() - the
    same ownership check (an owner can never touch someone else's vehicle,
    even by guessing an ID in the URL), adapted to flash + redirect instead of
    show_error() + return."""
    try:
        vehicle = vehicle_service.get_vehicle(vehicle_id)
    except ValueError as error:
        flash_value_error(error)
        return None
    if vehicle.owner_id != g.user.owner_driver_id:
        flash("That vehicle does not belong to your account.", "error")
        return None
    return vehicle


@app.route("/owner")
@role_required("OWNER_DRIVER")
def owner_dashboard():
    return render_template("owner_dashboard.html")


@app.route("/owner/vehicles")
@role_required("OWNER_DRIVER")
def owner_vehicles():
    return render_template("owner_vehicles.html", vehicles=vehicle_service.list_vehicles_owned_by(g.user.owner_driver_id))


@app.route("/owner/vehicles/add", methods=["GET", "POST"])
@role_required("OWNER_DRIVER")
def owner_vehicle_add():
    if request.method == "POST":
        try:
            vehicle_id = vehicle_service.add_vehicle(
                g.user.owner_driver_id, request.form.get("registration_no", ""),
                request.form.get("brand", ""), request.form.get("model", ""),
                request.form.get("year", ""), request.form.get("vehicle_type", ""),
                request.form.get("seats", ""), request.form.get("daily_rate", ""),
            )
            flash(f"Vehicle added successfully with ID {vehicle_id}.", "success")
            return redirect(url_for("owner_vehicles"))
        except ValueError as error:
            flash_value_error(error)
    return render_template("owner_vehicle_add.html", valid_types=vehicle_service.VALID_TYPES)


@app.route("/owner/vehicles/<int:vehicle_id>/edit")
@role_required("OWNER_DRIVER")
def owner_vehicle_edit(vehicle_id):
    vehicle = _get_own_vehicle_or_none(vehicle_id)
    if vehicle is None:
        return redirect(url_for("owner_vehicles"))
    return render_template("owner_vehicle_edit.html", vehicle=vehicle, valid_statuses=vehicle_service.VALID_STATUSES)


@app.route("/owner/vehicles/<int:vehicle_id>/rate", methods=["POST"])
@role_required("OWNER_DRIVER")
def owner_vehicle_update_rate(vehicle_id):
    if _get_own_vehicle_or_none(vehicle_id) is None:
        return redirect(url_for("owner_vehicles"))
    try:
        vehicle_service.update_vehicle_rate(vehicle_id, request.form.get("new_rate", ""))
        flash("Daily rate updated successfully.", "success")
    except ValueError as error:
        flash_value_error(error)
    return redirect(url_for("owner_vehicle_edit", vehicle_id=vehicle_id))


@app.route("/owner/vehicles/<int:vehicle_id>/status", methods=["POST"])
@role_required("OWNER_DRIVER")
def owner_vehicle_update_status(vehicle_id):
    if _get_own_vehicle_or_none(vehicle_id) is None:
        return redirect(url_for("owner_vehicles"))
    try:
        vehicle_service.update_vehicle_status(vehicle_id, request.form.get("status", ""))
        flash("Vehicle status updated successfully.", "success")
    except ValueError as error:
        flash_value_error(error)
    return redirect(url_for("owner_vehicle_edit", vehicle_id=vehicle_id))


@app.route("/owner/vehicles/<int:vehicle_id>/delete", methods=["POST"])
@role_required("OWNER_DRIVER")
def owner_vehicle_delete(vehicle_id):
    if _get_own_vehicle_or_none(vehicle_id) is None:
        return redirect(url_for("owner_vehicles"))
    try:
        vehicle_service.delete_vehicle(vehicle_id)
        flash("Vehicle deleted successfully.", "success")
    except ValueError as error:
        flash_value_error(error)
    return redirect(url_for("owner_vehicles"))


@app.route("/owner/vehicles/<int:vehicle_id>/waitlist")
@role_required("OWNER_DRIVER")
def owner_waitlist(vehicle_id):
    vehicle = _get_own_vehicle_or_none(vehicle_id)
    if vehicle is None:
        return redirect(url_for("owner_vehicles"))
    return render_template("owner_waitlist.html", vehicle=vehicle, entries=waitlist_service.list_waitlist_for_vehicle(vehicle_id))


# ---------------------------------------------------------------------------
# CUSTOMER PAGES - mirrors cli/customer_menu.py
# ---------------------------------------------------------------------------

@app.route("/customer")
@role_required("CUSTOMER")
def customer_dashboard():
    return render_template("customer_dashboard.html")


@app.route("/customer/vehicles")
@role_required("CUSTOMER")
def customer_vehicles():
    query = request.args.get("q", "").strip()
    vehicles = vehicle_service.search_vehicles(query) if query else vehicle_service.list_available_vehicles()
    return render_template("customer_vehicles.html", vehicles=vehicles, query=query)


@app.route("/customer/book/<int:vehicle_id>", methods=["GET", "POST"])
@role_required("CUSTOMER")
def customer_book(vehicle_id):
    try:
        vehicle = vehicle_service.get_vehicle(vehicle_id)
    except ValueError as error:
        flash_value_error(error)
        return redirect(url_for("customer_vehicles"))

    drivers = booking_service.list_available_drivers()
    form = {}
    show_waitlist_option = False

    if request.method == "POST":
        form = {
            "pickup_date": request.form.get("pickup_date", ""),
            "return_date": request.form.get("return_date", ""),
            "distance_km": request.form.get("distance_km", ""),
            "driver_required": request.form.get("driver_required") == "Y",
        }
        driver_required = form["driver_required"]
        driver_id_raw = request.form.get("driver_id") or None
        driver_id = int(driver_id_raw) if driver_id_raw else None

        if driver_required and driver_id is None:
            flash("A driver is required but no driver was selected.", "error")
            return render_template("customer_book.html", vehicle=vehicle, drivers=drivers, form=form, show_waitlist_option=False)

        try:
            from utils import validators
            pickup_date, return_date = validators.validate_date_range(form["pickup_date"], form["return_date"])
        except ValueError as error:
            flash_value_error(error)
            return render_template("customer_book.html", vehicle=vehicle, drivers=drivers, form=form, show_waitlist_option=False)

        if not booking_service.check_vehicle_availability(vehicle_id, pickup_date, return_date):
            flash(
                "Sorry! This vehicle is not available for the selected dates. "
                "You can join its waitlist instead using the button below, to be "
                "notified automatically when it becomes free.",
                "error",
            )
            return render_template("customer_book.html", vehicle=vehicle, drivers=drivers, form=form, show_waitlist_option=True)

        try:
            booking = booking_service.create_booking(
                g.user, vehicle_id, form["pickup_date"], form["return_date"],
                form["distance_km"], driver_required, driver_id,
            )
        except ValueError as error:
            flash_value_error(error)
            return render_template("customer_book.html", vehicle=vehicle, drivers=drivers, form=form, show_waitlist_option=False)

        flash(
            f"Booking #{booking.booking_id} created successfully!\n\n"
            f"Status: {booking.status} (awaiting administrator confirmation)\n"
            f"Number of days: {booking.number_of_days}\n"
            f"Total cost: {format_currency(booking.total_amount)}",
            "success",
        )
        return redirect(url_for("customer_bookings"))

    return render_template("customer_book.html", vehicle=vehicle, drivers=drivers, form=form, show_waitlist_option=show_waitlist_option)


@app.route("/customer/bookings")
@role_required("CUSTOMER")
def customer_bookings():
    bookings = booking_service.list_bookings_for_customer(g.user.customer_id)
    rows = []
    for booking in bookings:
        try:
            vehicle_name = vehicle_service.get_vehicle(booking.vehicle_id).display_name()
        except ValueError:
            vehicle_name = "(vehicle no longer in system)"
        rows.append((booking, vehicle_name))
    return render_template("customer_bookings.html", bookings=rows)


@app.route("/customer/bookings/<int:booking_id>/cancel", methods=["POST"])
@role_required("CUSTOMER")
def customer_cancel_booking(booking_id):
    try:
        booking = booking_service.get_booking(booking_id)
        if booking.customer_id != g.user.customer_id:
            flash("That booking does not belong to your account.", "error")
            return redirect(url_for("customer_bookings"))
        booking_service.cancel_booking(booking_id)
        flash(f"Booking #{booking_id} has been cancelled.", "success")
    except ValueError as error:
        flash_value_error(error)
    return redirect(url_for("customer_bookings"))


@app.route("/customer/bookings/<int:booking_id>/pay", methods=["GET", "POST"])
@role_required("CUSTOMER")
def customer_pay(booking_id):
    try:
        booking = booking_service.get_booking(booking_id)
    except ValueError as error:
        flash_value_error(error)
        return redirect(url_for("customer_bookings"))
    if booking.customer_id != g.user.customer_id:
        flash("That booking does not belong to your account.", "error")
        return redirect(url_for("customer_bookings"))

    already_paid = sum(p.amount for p in payment_service.list_payments_for_booking(booking_id) if p.status == "PAID")
    outstanding = booking.total_amount - already_paid

    if request.method == "POST":
        amount_str = request.form.get("amount", "")
        method = request.form.get("method", "")
        try:
            from utils import validators
            amount_for_status_check = validators.validate_positive_number(amount_str, "Payment amount")
        except ValueError as error:
            flash_value_error(error)
            return render_template("customer_pay.html", booking=booking, already_paid=already_paid,
                                    outstanding=outstanding, valid_methods=Payment.VALID_METHODS)

        status = "PAID" if (already_paid + amount_for_status_check) >= booking.total_amount else "PARTIAL"
        try:
            payment = payment_service.record_payment(booking_id, amount_str, method, status)
            flash(f"Payment of {format_currency(payment.amount)} recorded ({payment.method}, status: {payment.status}).", "success")
        except ValueError as error:
            flash_value_error(error)
        return redirect(url_for("customer_bookings"))

    return render_template("customer_pay.html", booking=booking, already_paid=already_paid,
                            outstanding=outstanding, valid_methods=Payment.VALID_METHODS)


@app.route("/customer/waitlist/join", methods=["GET", "POST"])
@role_required("CUSTOMER")
def customer_waitlist_join():
    form = {
        "vehicle_id": request.values.get("vehicle_id", ""),
        "pickup_date": request.values.get("pickup_date", ""),
        "return_date": request.values.get("return_date", ""),
    }
    if request.method == "POST":
        try:
            from utils import validators
            vehicle_id = validators.validate_positive_int(form["vehicle_id"], "Vehicle ID")
            vehicle_service.get_vehicle(vehicle_id)
            pickup_date, return_date = validators.validate_date_range(form["pickup_date"], form["return_date"])
        except ValueError as error:
            flash_value_error(error)
            return render_template("customer_waitlist_join.html", form=form)

        waitlist_service.join_waitlist(g.user, vehicle_id, pickup_date, return_date)
        flash("You have been added to the waitlist. You will be notified here if you log in after it opens up.", "success")
        return redirect(url_for("customer_dashboard"))

    return render_template("customer_waitlist_join.html", form=form)


if __name__ == "__main__":
    import threading
    import webbrowser

    WEB_URL = "http://127.0.0.1:5000"

    def _open_browser_when_ready():
        """Opens the default browser automatically once the server is up.

        Flask/Werkzeug's dev server does NOT open a browser by itself - it
        just starts listening and waits. Anyone running "python web/app.py"
        from a plain terminal (or VS Code's integrated terminal) sees the
        console messages below but nothing appears on screen otherwise,
        which looks like "it isn't working" even when it is. This timer
        waits 1.25 seconds (enough time for app.run() below to finish
        binding the port) and then opens WEB_URL in the system's default
        browser automatically, the same way clicking a link would.
        """
        webbrowser.open(WEB_URL)

    print(f"Starting {config.PROJECT_NAME} web interface...")
    print(f"Open {WEB_URL} in your browser. Press CTRL+C to stop.")
    print("(Your default browser should open automatically in a second or two.")
    print(" If it does not, copy the address above into any browser's address bar")
    print(" - it will NOT open by double-clicking this file or the terminal itself.)")
    threading.Timer(1.25, _open_browser_when_ready).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
