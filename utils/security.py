"""
utils/security.py
==================

WHAT THIS FILE IS FOR:
Handles password hashing and verification. No other file in this project stores or
compares a plain-text password directly - everything goes through the two functions
here, so there is exactly ONE place that decides how passwords are protected.

WHY WE HASH PASSWORDS (the concept being demonstrated):
Hashing is a ONE-WAY mathematical function: it is easy to turn a password into its
hash, but there is no way to turn a hash back into the original password. This is
why, even the Super Administrator can never "see" another user's real password (see
FR4a/FR4b in docs/01_requirements_analysis.md) - only reset it to a new value.

WHY A "SALT":
If we hashed the same password the same way every time, two users who happened to
pick the same password would end up with the SAME hash stored in the database - and
anyone looking at the database could spot that pattern. A SALT is a random string
generated separately for every user and mixed into the password before hashing, so
even identical passwords produce completely different stored hashes. We keep the
salt next to the hash (they are not secret on their own) so we can redo the same
calculation later to check a login attempt.
"""

import hashlib
import os


def hash_password(plain_password: str, salt: str = None) -> str:
    """
    Turns a plain-text password into a salted hash.

    Arguments:
        plain_password: the real password, as typed by the user.
        salt: normally left as None so a new random salt is generated (used when
              creating an account). Pass the EXISTING salt back in when you need to
              re-hash a login attempt for comparison (see verify_password below).

    Returns:
        A single string in the format "salt$hash", ready to store in the database.
    """
    if salt is None:
        # os.urandom gives us cryptographically random bytes; .hex() turns them into
        # a readable string of letters/numbers we can store as ordinary text.
        salt = os.urandom(16).hex()

    # Combine the salt and password, then hash the combination with SHA-256 (a
    # standard, well-tested one-way hash function built into Python's hashlib).
    combined = (salt + plain_password).encode("utf-8")
    hash_value = hashlib.sha256(combined).hexdigest()

    return f"{salt}${hash_value}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Checks whether `plain_password` matches a previously stored "salt$hash" value.

    HOW THIS WORKS: we cannot "decrypt" stored_hash back into a password. Instead, we
    pull out the salt that was used originally, hash the CANDIDATE password with that
    same salt, and see if the result matches exactly. If the passwords were the same,
    the hashes will be identical; if not, they will (almost certainly) differ.
    """
    if not stored_hash or "$" not in stored_hash:
        return False
    salt, _, _ = stored_hash.partition("$")
    return hash_password(plain_password, salt) == stored_hash


def generate_temporary_password() -> str:
    """
    Generates a short, random, easy-to-type temporary password. Used by the Admin's
    "Reset Password" action when they choose to let the system generate one instead
    of typing a specific new password (see FR4b).
    """
    # A short hex string (8 characters) is random enough for a temporary password
    # that the user will be asked to change, and simple enough to read aloud/type.
    return os.urandom(4).hex()
