"""
tests/test_security.py
=========================

WHAT THIS FILE IS FOR:
Automated tests for utils/security.py - the password hashing functions this whole
project's account security depends on. No database is needed here either; hashing
is a pure function of the password text and (optionally) a salt.
"""

from utils.security import generate_temporary_password, hash_password, verify_password


def test_hash_password_never_stores_the_plain_password():
    plain_password = "Customer@123"
    stored_hash = hash_password(plain_password)
    # The whole point of hashing: the plain password text must never appear
    # anywhere inside the stored value.
    assert plain_password not in stored_hash


def test_hash_password_produces_a_different_hash_each_time_via_random_salt():
    # Hashing the SAME password twice should still produce two DIFFERENT stored
    # values, because each call generates a fresh random salt (see
    # utils/security.py) - this is what stops two users who happen to choose the
    # same password from ending up with identical, comparable hashes.
    first_hash = hash_password("Customer@123")
    second_hash = hash_password("Customer@123")
    assert first_hash != second_hash


def test_verify_password_accepts_the_correct_password():
    stored_hash = hash_password("Customer@123")
    assert verify_password("Customer@123", stored_hash) is True


def test_verify_password_rejects_the_wrong_password():
    stored_hash = hash_password("Customer@123")
    assert verify_password("WrongPassword", stored_hash) is False


def test_generate_temporary_password_returns_a_non_empty_string():
    temporary_password = generate_temporary_password()
    assert isinstance(temporary_password, str)
    assert len(temporary_password) > 0


def test_generate_temporary_password_is_different_each_time():
    # Not a mathematical proof of randomness - just a sanity check that two calls
    # in a row are not returning the exact same hard-coded string by mistake.
    assert generate_temporary_password() != generate_temporary_password()
