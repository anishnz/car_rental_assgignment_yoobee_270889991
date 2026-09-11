"""
config.py
=========

WHAT THIS FILE IS FOR:
This file holds configuration values and constants that are used across the whole
Nepal Car Rental System (NCRS) project. Keeping these values in one place (instead of
typing them directly inside many different functions) is a basic software engineering
practice: if a value ever needs to change (for example, the admin registration
keyword), it only needs to change here, not in ten different files.

WHY WE NEED IT (Python concept demonstrated):
This module shows the use of MODULE-LEVEL CONSTANTS in Python. By convention, constant
names are written in UPPER_CASE. Other files "import" this module (e.g.
`from config import ADMIN_KEYWORD`) instead of hard-coding the same value repeatedly.
"""

# ---------------------------------------------------------------------------
# ASSIGNMENT / ASSESSMENT DETAILS
# ---------------------------------------------------------------------------
# These details identify this submission. They are shown on the CLI "About" screen
# (see cli/about_screen.py, added later) so that anyone running the program can see
# whose assignment this is and which course/assessment it was built for.

PROGRAMME = "Master of Software Engineering - 180 Credits"
COURSE_NAME = "Professional Software Engineering (MSE-800)"
COURSE_DETAILS = "Level 8, 15 Credits, Version 1"
ASSESSMENT_TITLE = "Assessment 1 - Object-Oriented Programming Assignment"
LECTURER_NAME = "Mohammad Norouzifard"
STUDENT_NAME = "Anish Shrestha"
STUDENT_ID = "270889991"
INSTITUTION = "Yoobee College, New Zealand"

# ---------------------------------------------------------------------------
# PROJECT IDENTITY
# ---------------------------------------------------------------------------
PROJECT_NAME = "Nepal Car Rental System (NCRS)"
PROJECT_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# REGISTRATION KEYWORDS
# ---------------------------------------------------------------------------
# For an academic demo system, new accounts must supply a simple "keyword" during
# registration so the CLI can decide which role to create. In a real production
# system these would be replaced with a proper invite/approval workflow, but for this
# assignment a keyword is a simple, explainable way to demonstrate role assignment.
# Storing them here (instead of writing "admin" directly inside the registration
# function) means we only need to change ONE place if the keyword ever changes.

ADMIN_KEYWORD = "admin"
VEHICLE_OWNER_DRIVER_KEYWORD = "vehicle_Owner_Driver"
CUSTOMER_KEYWORD = "customer"
PASSWORD_RESET_KEYWORD = "password_rest"

# ---------------------------------------------------------------------------
# CURRENCY & PRICING
# ---------------------------------------------------------------------------
# All monetary values in this project are shown in New Zealand Dollars, using the
# symbol below. This is purely a DISPLAY convention (we are not doing any real
# currency conversion) - every price is just formatted with this symbol in front.
CURRENCY_SYMBOL = "NZD$"

# DEFAULT_RATE_PER_KM is only the STARTING value written into the database the very
# first time the program runs (it seeds the `settings` table - see database/ once
# built). After that, the *live* rate used in every cost calculation is read from the
# database, not from this constant, because the Super Administrator can change it at
# any time through the CLI (see FR13a in docs/01_requirements_analysis.md). Keeping a
# default here just means the system always has a sensible starting value.
DEFAULT_RATE_PER_KM = 5.00

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------
# SQLite stores the entire database as a single file. Using a local file (instead of
# a MySQL/remote server) means the whole project can run offline, with no separate
# database installation or configuration - just Python itself.
DATABASE_FILE_NAME = "ncrs_database.sqlite3"
