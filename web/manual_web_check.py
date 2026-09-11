"""
web/manual_web_check.py
=========================

WHAT THIS FILE IS FOR:
A manual end-to-end smoke test for the web interface (web/app.py) - it starts
the Flask app in Flask's own in-memory "test client" (no real network port
needed) and clicks through every major page and action: registering,
logging in as each of the three roles, adding/editing/deleting a vehicle,
booking a vehicle, hitting a booking conflict and joining the waitlist,
making a payment, approving a pending registration, resetting a password,
and confirming the ownership/access-control rules ("you cannot edit someone
else's vehicle", "you cannot pay for someone else's booking") are enforced.

WHY THIS IS SEPARATE FROM THE tests/ FOLDER'S 86 pytest TESTS:
Those 86 tests are the project's real, automated test suite - they test the
services/ layer directly, in isolation, against a fresh temporary database
per test (see tests/conftest.py), and that is what the project report quotes
as "86 passing tests". This script is a DIFFERENT kind of check: it exercises
the actual web pages themselves (routing, templates, forms, redirects,
sessions) end-to-end, against the real database file, so it deliberately
starts by deleting any existing ncrs_database.sqlite3 and lets it be
re-seeded fresh. It is meant to be run by hand after changing anything in
web/, not as part of the official `pytest` run.

HOW TO RUN IT:
    cd Car_Rental_MIS
    python web/manual_web_check.py

A clean run ends with "TOTAL FAILURES: 0". Any FAIL line above that is printed
with the response it got, to make it easy to see what broke.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(PROJECT_ROOT, "ncrs_database.sqlite3")
if os.path.exists(db_path):
    os.remove(db_path)

import app as webapp  # noqa: E402  (must come after the sys.path fix above)

client = webapp.app.test_client()
failures = 0


def check(name, resp, expect=200, contains=None):
    global failures
    ok = resp.status_code == expect
    if contains and ok:
        ok = contains in resp.get_data(as_text=True)
    print(f"[{'OK' if ok else 'FAIL'}] {name} -> {resp.status_code} (expected {expect})")
    if not ok:
        failures += 1
        print("     Location header:", resp.headers.get("Location"))
        print("     Body snippet    :", resp.get_data(as_text=True)[:300].replace("\n", " "))


# --- Public pages, no login needed --------------------------------------
check("home page", client.get("/"), contains="Nepal Car Rental")
check("browse available vehicles", client.get("/vehicles"), contains="Available Vehicles")
check("browse vehicles by type", client.get("/vehicles/by-type?type=SUV"), contains="Sportage")
check("rental info page", client.get("/rental-info"), contains="Pricing formula")
check("about page", client.get("/about"), contains="Anish Shrestha")
check("register: choose role", client.get("/register"), contains="Super Administrator")
check("register: admin form", client.get("/register/admin"), contains="Administrator Keyword")
check("forgot password form", client.get("/forgot-password"), contains="Reset Keyword")

check("register admin (correct keyword) redirects to login", client.post(
    "/register/admin",
    data={"full_name": "Web Test Admin", "username": "web_admin_test", "email": "wa@example.com",
          "phone": "9800000099", "password": "WebAdmin1", "keyword": "admin"},
), expect=302)
check("register admin (wrong keyword) shows error", client.post(
    "/register/admin",
    data={"full_name": "X", "username": "bad_admin", "email": "x@example.com",
          "phone": "9800000000", "password": "pw", "keyword": "WRONG"},
    follow_redirects=True,
), contains="Invalid administrator keyword")

# --- Admin flow -----------------------------------------------------------
check("admin login redirects", client.post("/login", data={"username": "admin_ncrs", "password": "Admin@123"}), expect=302)
check("admin dashboard", client.get("/admin"), contains="Super Administrator Dashboard")
check("manage users page", client.get("/admin/users"), contains="admin_ncrs")
check("pending registrations page", client.get("/admin/registrations"), contains="owner_hari")
check("all vehicles page", client.get("/admin/vehicles"), contains="Corolla")
check("manage bookings page", client.get("/admin/bookings"), contains="CONFIRMED")
check("payments page", client.get("/admin/payments"), contains="Record a Payment")
check("system statistics page", client.get("/admin/stats"), contains="Total Customers")
check("rate-per-km page", client.get("/admin/rate"), contains="Current rate")
check("approve pending registration", client.post("/admin/registrations/2/approve", follow_redirects=True), contains="Registration approved")
check("update rate per km", client.post("/admin/rate", data={"new_rate": "6.00"}, follow_redirects=True), contains="updated to")
check("admin resets a user's password", client.post(
    "/admin/users/reset-password", data={"target_username": "customer_gita", "new_password": ""}, follow_redirects=True,
), contains="has been reset")
check("admin logout", client.get("/logout", follow_redirects=True), contains="logged out")

# --- Owner flow -------------------------------------------------------------
check("owner login", client.post("/login", data={"username": "owner_ram", "password": "Owner@123"}, follow_redirects=True), contains="Owner / Driver Dashboard")
check("owner's vehicle list", client.get("/owner/vehicles"), contains="Corolla")
check("owner adds a vehicle", client.post(
    "/owner/vehicles/add",
    data={"registration_no": "BA 99 PA 0001", "brand": "Test", "model": "Car", "year": "2023",
          "vehicle_type": "Sedan", "seats": "5", "daily_rate": "70"},
    follow_redirects=True,
), contains="added successfully")
check("new vehicle appears in owner's list", client.get("/owner/vehicles"), contains="BA 99 PA 0001")
# 10 seeded vehicles + this new one = vehicle_id 11 on a freshly-seeded database
check("owner edit-vehicle page", client.get("/owner/vehicles/11/edit"), contains="Test Car")
check("owner updates rate", client.post("/owner/vehicles/11/rate", data={"new_rate": "75"}, follow_redirects=True), contains="updated successfully")
check("owner updates status", client.post("/owner/vehicles/11/status", data={"status": "MAINTENANCE"}, follow_redirects=True), contains="updated successfully")
check("owner views (empty) waitlist", client.get("/owner/vehicles/11/waitlist"), contains="no one is currently waitlisted")
check("owner deletes the vehicle", client.post("/owner/vehicles/11/delete", follow_redirects=True), contains="deleted successfully")
check("owner cannot edit a vehicle they do not own", client.get("/owner/vehicles/4/edit", follow_redirects=True), contains="does not belong to your account")
check("owner logout", client.get("/logout", follow_redirects=True), contains="logged out")

# --- Customer flow ----------------------------------------------------------
check("customer login", client.post("/login", data={"username": "customer_sita", "password": "Customer@123"}, follow_redirects=True), contains="Customer Dashboard")
check("customer browses vehicles", client.get("/customer/vehicles"), contains="Book")
check("customer searches vehicles", client.get("/customer/vehicles?q=Swift"), contains="Swift")
check("book-vehicle form loads", client.get("/customer/book/3"), contains="Book Suzuki Swift")
check("customer books an available vehicle", client.post(
    "/customer/book/3", data={"pickup_date": "2026-11-01", "return_date": "2026-11-03", "distance_km": "40"}, follow_redirects=True,
), contains="created successfully")
check("new booking appears in My Bookings", client.get("/customer/bookings"), contains="Swift")
check("booking conflict offers the waitlist instead", client.post(
    "/customer/book/2", data={"pickup_date": "2026-09-21", "return_date": "2026-09-24", "distance_km": "50"}, follow_redirects=True,
), contains="Join the Waitlist")
check("customer joins the waitlist", client.post(
    "/customer/waitlist/join", data={"vehicle_id": "2", "pickup_date": "2026-09-21", "return_date": "2026-09-24"}, follow_redirects=True,
), contains="added to the waitlist")
# 3 seeded bookings + the one just created above = booking_id 4
check("payment page loads", client.get("/customer/bookings/4/pay"), contains="Make a Payment")
check("customer records a payment", client.post("/customer/bookings/4/pay", data={"amount": "50", "method": "CASH"}, follow_redirects=True), contains="recorded")
check("customer cancels the booking", client.post("/customer/bookings/4/cancel", follow_redirects=True), contains="has been cancelled")
check("customer cannot pay for someone else's booking", client.get("/customer/bookings/3/pay", follow_redirects=True), contains="does not belong to your account")
check("customer changes their own password", client.post(
    "/change-password/customer", data={"reset_keyword": "password_rest", "new_password": "NewPass9", "confirm_password": "NewPass9"}, follow_redirects=True,
), contains="Password successfully changed")
check("customer logout", client.get("/logout", follow_redirects=True), contains="logged out")

# --- Access control ----------------------------------------------------------
check("an anonymous visitor is redirected away from /admin", client.get("/admin", follow_redirects=True), contains="log in first")

print()
print(f"TOTAL FAILURES: {failures}")
sys.exit(1 if failures else 0)
