"""
models/user.py
===============

WHAT THIS FILE IS FOR:
Defines the User class hierarchy: one base class (User) that holds what every
account has in common, and three subclasses (Admin, VehicleOwnerDriver, Customer)
that each add the extra details and behaviour specific to that role.

WHY INHERITANCE HERE (the OOP concept demonstrated):
Every account in this system - no matter its role - has a user_id, username,
password hash, role, and status, and can log in / log out / reset its password.
Rather than repeating those fields and methods in three separate, unrelated classes,
INHERITANCE lets us write them ONCE on the `User` base class, and have Admin,
VehicleOwnerDriver, and Customer each `extend` User by inheriting everything it
already has, then adding only what makes that role different. This avoids
duplicated code and models the real relationship between these roles accurately
("an Admin IS A User, with extra permissions").

WHY POLYMORPHISM HERE:
Each subclass overrides `role_label()` to return a different string. Code elsewhere
(for example, the "About"/welcome screens) can call `current_user.role_label()`
without needing to know or check WHICH subclass it actually has - Python
automatically runs the correct subclass's version of the method. This is
polymorphism: the same method call behaves differently depending on the real
(sub)class of the object it is called on.

NOTE ON PERSISTENCE: these are plain in-memory domain objects. Reading a user from
the database and saving changes back to it is handled by services/auth_service.py -
these classes only hold data and enforce the RULES about that data (e.g. you cannot
construct a Customer without a name); they never talk to the database directly. This
keeps the "models" layer (domain rules) cleanly separated from the "database" layer
(storage), matching the layered architecture in docs/01_requirements_analysis.md
section 18.
"""

from utils.security import verify_password


class User:
    """Base class shared by every account in the system."""

    def __init__(self, user_id: int, username: str, password_hash: str, role: str, status: str):
        self.user_id = user_id
        self.username = username
        # A leading underscore is Python's convention for "please treat this as
        # private" - ENCAPSULATION. Nothing outside this class should ever read
        # or set password_hash directly; it should only ever be checked through
        # check_password(), which never exposes the actual hash value to the caller.
        self._password_hash = password_hash
        self.role = role
        self.status = status

    def check_password(self, plain_password: str) -> bool:
        """Returns True if `plain_password` matches this user's stored hash."""
        return verify_password(plain_password, self._password_hash)

    def is_active(self) -> bool:
        """
        Whether this account is currently allowed to log in. Vehicle Owner/Driver
        accounts start PENDING and only become usable once an admin approves them
        (FR4); other roles are active as soon as they register.
        """
        return self.status in ("ACTIVE", "APPROVED")

    def role_label(self) -> str:
        """
        Human-readable label for this account's role. Overridden by every subclass
        below - this is the polymorphism example described at the top of this file.
        """
        return "User"

    def __str__(self):
        return f"{self.username} ({self.role_label()})"


class Admin(User):
    """A Super Administrator account - full system access."""

    def role_label(self) -> str:
        return "Super Administrator"


class VehicleOwnerDriver(User):
    """
    A Vehicle Owner/Driver account. Combines two related real-world roles (someone
    who owns vehicles listed on the platform, and/or someone available to be hired
    as a driver) into one account type, matching the role model agreed for this
    project (see docs/01_requirements_analysis.md section 7).
    """

    def __init__(self, user_id, username, password_hash, role, status,
                 owner_driver_id, full_name, phone, email, licence_no,
                 licence_expiry, daily_driver_rate):
        super().__init__(user_id, username, password_hash, role, status)
        self.owner_driver_id = owner_driver_id
        self.full_name = full_name
        self.phone = phone
        self.email = email
        self.licence_no = licence_no
        self.licence_expiry = licence_expiry
        self.daily_driver_rate = daily_driver_rate

    def role_label(self) -> str:
        return "Vehicle Owner / Driver"


class Customer(User):
    """A Customer account - can browse, book, and manage their own bookings."""

    def __init__(self, user_id, username, password_hash, role, status,
                 customer_id, full_name, phone, email, address, licence_no):
        super().__init__(user_id, username, password_hash, role, status)
        self.customer_id = customer_id
        self.full_name = full_name
        self.phone = phone
        self.email = email
        self.address = address
        self.licence_no = licence_no

    def role_label(self) -> str:
        return "Customer"
