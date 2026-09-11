"""
services/auth_service.py
=========================

WHAT THIS FILE IS FOR:
All the logic for registering new accounts, logging in, and resetting passwords
(both self-service and the Admin's reset-any-user action). This is the only place
in the project that reads or writes the `users`, `customers`, and
`vehicle_owners_drivers` tables for authentication purposes.
"""

import config
from database.db_connection import DatabaseConnection
from models.user import Admin, VehicleOwnerDriver, Customer
from utils.security import hash_password, verify_password, generate_temporary_password
from utils import validators


def _build_user_object(user_row, db):
    """
    Given one row from the `users` table, builds the CORRECT subclass of User
    (Admin, VehicleOwnerDriver, or Customer) by looking up that role's extra profile
    table. This is a small FACTORY-style helper: calling code just gets back a
    ready-to-use, fully-typed User object and does not need to know which table to
    join against for which role.
    """
    role = user_row["role"]
    if role == "ADMIN":
        return Admin(user_row["user_id"], user_row["username"], user_row["password_hash"],
                     role, user_row["status"])

    if role == "OWNER_DRIVER":
        profile = db.fetch_one(
            "SELECT * FROM vehicle_owners_drivers WHERE user_id = ?", (user_row["user_id"],)
        )
        return VehicleOwnerDriver(
            user_row["user_id"], user_row["username"], user_row["password_hash"], role,
            user_row["status"], profile["owner_driver_id"], profile["full_name"],
            profile["phone"], profile["email"], profile["licence_no"],
            profile["licence_expiry"], profile["daily_driver_rate"],
        )

    if role == "CUSTOMER":
        profile = db.fetch_one(
            "SELECT * FROM customers WHERE user_id = ?", (user_row["user_id"],)
        )
        return Customer(
            user_row["user_id"], user_row["username"], user_row["password_hash"], role,
            user_row["status"], profile["customer_id"], profile["full_name"],
            profile["phone"], profile["email"], profile["address"], profile["licence_no"],
        )

    raise ValueError(f"Unknown role '{role}' stored against user '{user_row['username']}'.")


def login(username: str, password: str):
    """
    Attempts to log in with the given username and password.

    Returns the matching User subclass instance on success.
    Raises ValueError with a clear, user-facing message on failure - covering all
    of: unknown username, wrong password, and an account that is not yet approved
    (FR2, BR1).
    """
    db = DatabaseConnection.get_instance()
    user_row = db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))

    if user_row is None or not verify_password(password, user_row["password_hash"]):
        # Deliberately the SAME message for "no such user" and "wrong password" -
        # telling an attacker WHICH one was wrong would leak information about
        # which usernames exist in the system.
        raise ValueError("Incorrect username or password.")

    user = _build_user_object(user_row, db)
    if not user.is_active():
        raise ValueError(
            "This account has not been approved yet. Please wait for an "
            "administrator to approve your registration before logging in."
        )
    return user


def get_user_by_id(user_id: int):
    """
    Fetches one user by their numeric user_id and returns the correct User
    subclass (Admin / VehicleOwnerDriver / Customer), or None if it does not
    exist. Not used anywhere by the CLI - the CLI keeps the logged-in user
    object alive in memory for the whole dashboard session. It IS used by the
    web interface (web/app.py), because a web request is stateless: each new
    page load only has the browser's session cookie (which stores the plain
    user_id, never a password or the object itself), so the actual User object
    has to be rebuilt fresh from the database on every request. Reusing
    _build_user_object() here keeps that "which subclass, which profile table"
    logic in exactly one place rather than duplicating it in the web layer.
    """
    db = DatabaseConnection.get_instance()
    user_row = db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if user_row is None:
        return None
    return _build_user_object(user_row, db)


def register_customer(username, password, full_name, phone, email, address, licence_no, keyword):
    """Registers a new Customer account. Raises ValueError on any problem."""
    if keyword != config.CUSTOMER_KEYWORD:
        raise ValueError("Invalid customer registration keyword. Registration denied.")

    username = validators.validate_non_empty(username, "Username")
    full_name = validators.validate_non_empty(full_name, "Full name")
    phone = validators.validate_phone(phone)
    email = validators.validate_email(email)
    address = validators.validate_non_empty(address, "Address")
    licence_no = validators.validate_non_empty(licence_no, "Driving licence number")

    db = DatabaseConnection.get_instance()
    _ensure_username_available(db, username)

    cursor = db.execute(
        "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, ?, ?)",
        (username, hash_password(password), "CUSTOMER", "ACTIVE"),
    )
    user_id = cursor.lastrowid
    db.execute(
        """INSERT INTO customers (user_id, full_name, phone, email, address, licence_no)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, full_name, phone, email, address, licence_no),
    )


def register_owner_driver(username, password, full_name, phone, email, licence_no,
                           licence_expiry, daily_driver_rate, keyword):
    """
    Registers a new Vehicle Owner/Driver account. The account is created with
    status PENDING (BR1) - it cannot log in until an administrator approves it
    (see services/admin_service.approve_registration).
    """
    if keyword != config.VEHICLE_OWNER_DRIVER_KEYWORD:
        raise ValueError("Invalid registration keyword. Registration denied.")

    username = validators.validate_non_empty(username, "Username")
    full_name = validators.validate_non_empty(full_name, "Full name")
    phone = validators.validate_phone(phone)
    email = validators.validate_email(email)
    licence_no = validators.validate_non_empty(licence_no, "Driving licence number")
    licence_expiry_date = validators.validate_date(licence_expiry, "Licence expiry date")
    daily_driver_rate = validators.validate_non_negative_number(daily_driver_rate, "Daily driver rate")

    db = DatabaseConnection.get_instance()
    _ensure_username_available(db, username)

    cursor = db.execute(
        "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, ?, ?)",
        (username, hash_password(password), "OWNER_DRIVER", "PENDING"),
    )
    user_id = cursor.lastrowid
    db.execute(
        """INSERT INTO vehicle_owners_drivers
           (user_id, full_name, phone, email, licence_no, licence_expiry, daily_driver_rate, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, full_name, phone, email, licence_no, licence_expiry_date.isoformat(),
         daily_driver_rate, "PENDING"),
    )


def register_admin(username, password, full_name, email, phone, keyword):
    """Registers a new Super Administrator account."""
    if keyword != config.ADMIN_KEYWORD:
        raise ValueError("Invalid administrator keyword. Registration denied.")

    username = validators.validate_non_empty(username, "Username")
    validators.validate_non_empty(full_name, "Full name")
    validators.validate_email(email)
    validators.validate_phone(phone)

    db = DatabaseConnection.get_instance()
    _ensure_username_available(db, username)

    db.execute(
        "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, ?, ?)",
        (username, hash_password(password), "ADMIN", "ACTIVE"),
    )


def _ensure_username_available(db, username):
    """Raises ValueError if a user with this username already exists."""
    existing = db.fetch_one("SELECT 1 FROM users WHERE username = ?", (username,))
    if existing is not None:
        raise ValueError(f"Username '{username}' is already taken. Please choose another.")


def reset_own_password(username, reset_keyword, new_password, confirm_password):
    """Self-service password reset flow (FR3), gated by a shared reset keyword."""
    if reset_keyword != config.PASSWORD_RESET_KEYWORD:
        raise ValueError("Invalid reset keyword.")
    if new_password != confirm_password:
        raise ValueError("New password and confirmation do not match.")
    validators.validate_non_empty(new_password, "New password")

    db = DatabaseConnection.get_instance()
    user_row = db.fetch_one("SELECT user_id FROM users WHERE username = ?", (username,))
    if user_row is None:
        raise ValueError(f"No account found with username '{username}'.")

    db.execute(
        "UPDATE users SET password_hash = ? WHERE user_id = ?",
        (hash_password(new_password), user_row["user_id"]),
    )


def admin_reset_user_password(acting_admin, target_username, new_password=None):
    """
    Admin-only action (FR4b): resets ANY user's password, without ever needing to
    know (or being able to see) their previous one. If `new_password` is not
    supplied, a random temporary password is generated instead.

    Returns the new PLAIN-TEXT password once, so the admin can pass it on to the
    user - this is the only moment that plain-text value exists; after this
    function returns, only its hash is stored anywhere.
    """
    if not isinstance(acting_admin, Admin):
        raise PermissionError("Only a Super Administrator can reset another user's password.")

    db = DatabaseConnection.get_instance()
    user_row = db.fetch_one("SELECT user_id FROM users WHERE username = ?", (target_username,))
    if user_row is None:
        raise ValueError(f"No account found with username '{target_username}'.")

    if new_password is None:
        new_password = generate_temporary_password()

    db.execute(
        "UPDATE users SET password_hash = ? WHERE user_id = ?",
        (hash_password(new_password), user_row["user_id"]),
    )
    return new_password
