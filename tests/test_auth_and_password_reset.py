"""
tests/test_auth_and_password_reset.py
========================================

WHAT THIS FILE IS FOR:
Automated tests for services/auth_service.py: logging in, the keyword-gated
registration flows, self-service password reset, and the admin-only "reset any
user's password" action (FR2-FR4b). These all need a real database, so every
test here takes the `clean_database` fixture.
"""

import pytest

from models.user import Admin, Customer, VehicleOwnerDriver
from services import auth_service
import config


def test_login_with_correct_credentials_returns_the_right_user_type(clean_database):
    user = auth_service.login("customer_sita", "Customer@123")
    assert isinstance(user, Customer)
    assert user.full_name == "Sita Gurung"


def test_login_with_wrong_password_is_rejected(clean_database):
    with pytest.raises(ValueError):
        auth_service.login("customer_sita", "WrongPassword")


def test_login_with_unknown_username_is_rejected(clean_database):
    with pytest.raises(ValueError):
        auth_service.login("no_such_user", "AnyPassword")


def test_login_error_message_is_identical_for_bad_username_and_bad_password(clean_database):
    # Deliberately checking that BOTH failure cases produce the exact same
    # message (see the comment in auth_service.login()) - this is a security
    # property, not just a wording preference: it stops an attacker using the
    # error message to figure out which usernames exist in the system.
    message_for_bad_username = None
    message_for_bad_password = None
    try:
        auth_service.login("no_such_user", "AnyPassword")
    except ValueError as error:
        message_for_bad_username = str(error)
    try:
        auth_service.login("customer_sita", "WrongPassword")
    except ValueError as error:
        message_for_bad_password = str(error)
    assert message_for_bad_username == message_for_bad_password


def test_login_rejects_a_pending_owner_driver_account(clean_database):
    # owner_hari is seeded with status PENDING specifically to demonstrate this
    # rule (FR4/BR1): a not-yet-approved account cannot log in even with the
    # exact correct password.
    with pytest.raises(ValueError, match="not been approved"):
        auth_service.login("owner_hari", "Owner@123")


def test_register_customer_with_correct_keyword_succeeds(clean_database):
    auth_service.register_customer(
        "new_customer_1", "Password@123", "New Customer", "9800000099",
        "new.customer@example.com", "Lalitpur, Nepal", "NP-DL-9001",
        config.CUSTOMER_KEYWORD,
    )
    user = auth_service.login("new_customer_1", "Password@123")
    assert isinstance(user, Customer)
    assert user.is_active() is True  # customers are ACTIVE immediately (no approval needed)


def test_register_customer_with_wrong_keyword_is_rejected(clean_database):
    with pytest.raises(ValueError, match="keyword"):
        auth_service.register_customer(
            "new_customer_2", "Password@123", "New Customer", "9800000099",
            "new.customer@example.com", "Lalitpur, Nepal", "NP-DL-9002",
            "wrong-keyword",
        )


def test_register_customer_with_a_taken_username_is_rejected(clean_database):
    with pytest.raises(ValueError, match="already taken"):
        auth_service.register_customer(
            "customer_sita", "Password@123", "Someone Else", "9800000099",
            "someone@example.com", "Somewhere, Nepal", "NP-DL-9003",
            config.CUSTOMER_KEYWORD,
        )


def test_register_owner_driver_creates_a_pending_account(clean_database):
    auth_service.register_owner_driver(
        "new_owner_1", "Password@123", "New Owner", "9800000098",
        "new.owner@example.com", "NP-LIC-9002", "2029-01-01", "0",
        config.VEHICLE_OWNER_DRIVER_KEYWORD,
    )
    # The account exists but should NOT be able to log in yet (BR1).
    with pytest.raises(ValueError, match="not been approved"):
        auth_service.login("new_owner_1", "Password@123")


def test_register_admin_with_correct_keyword_succeeds(clean_database):
    auth_service.register_admin(
        "new_admin_1", "Password@123", "New Admin", "new.admin@example.com",
        "9800000097", config.ADMIN_KEYWORD,
    )
    user = auth_service.login("new_admin_1", "Password@123")
    assert isinstance(user, Admin)


def test_reset_own_password_with_correct_keyword_and_matching_confirmation(clean_database):
    auth_service.reset_own_password(
        "customer_sita", config.PASSWORD_RESET_KEYWORD, "BrandNew@123", "BrandNew@123",
    )
    # Old password must no longer work, new one must.
    with pytest.raises(ValueError):
        auth_service.login("customer_sita", "Customer@123")
    user = auth_service.login("customer_sita", "BrandNew@123")
    assert isinstance(user, Customer)


def test_reset_own_password_rejects_mismatched_confirmation(clean_database):
    with pytest.raises(ValueError, match="do not match"):
        auth_service.reset_own_password(
            "customer_sita", config.PASSWORD_RESET_KEYWORD, "BrandNew@123", "SomethingElse@123",
        )


def test_admin_reset_user_password_returns_a_working_plain_text_password(clean_database):
    admin = auth_service.login("admin_ncrs", "Admin@123")
    new_password = auth_service.admin_reset_user_password(admin, "customer_sita", "Chosen@123")
    assert new_password == "Chosen@123"
    user = auth_service.login("customer_sita", "Chosen@123")
    assert isinstance(user, Customer)


def test_admin_reset_user_password_can_auto_generate_a_password(clean_database):
    admin = auth_service.login("admin_ncrs", "Admin@123")
    generated_password = auth_service.admin_reset_user_password(admin, "customer_sita", None)
    assert generated_password  # a non-empty temporary password was returned
    user = auth_service.login("customer_sita", generated_password)
    assert isinstance(user, Customer)


def test_non_admin_cannot_reset_another_users_password(clean_database):
    non_admin_customer = auth_service.login("customer_sita", "Customer@123")
    with pytest.raises(PermissionError):
        auth_service.admin_reset_user_password(non_admin_customer, "customer_gita", "Whatever@123")
