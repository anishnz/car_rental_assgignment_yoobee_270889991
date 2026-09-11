"""
tests/conftest.py
====================

WHAT THIS FILE IS FOR:
pytest automatically loads this file before running any test in this folder, and
any fixture defined here (a function decorated with @pytest.fixture) becomes
available to every test function just by naming it as a parameter - this is how
pytest lets many test functions share the same setup code without copy-pasting it.

WHY WE NEED A "clean_database" FIXTURE:
Every test in this project needs its OWN throwaway database - completely separate
from the real ncrs_database.sqlite3 file the actual application uses - so that
running the tests never touches (or is affected by) real project data, and so each
test starts from the exact same known starting point (freshly seeded demo data)
regardless of what other tests ran before it. This is achieved using:

  1. `tempfile` to create a brand new, empty SQLite file path for each test.
  2. `config.DATABASE_FILE_NAME` being TEMPORARILY reassigned to that path
     (config.py is just a module - like any Python object, its attributes can be
     reassigned at runtime - so this redirects every part of the app that reads
     config.DATABASE_FILE_NAME, with no other code changes needed). We give it
     an ABSOLUTE path on purpose: DatabaseConnection builds its real path with
     os.path.join(project_root, config.DATABASE_FILE_NAME), and os.path.join
     simply returns an absolute second argument unchanged - so this reliably
     points the connection at our temp file no matter where it is.
  3. `DatabaseConnection.reset_instance_for_tests()` and
     `RentalSystem.reset_instance_for_tests()` (both written specifically for
     this purpose - see database/db_connection.py and services/rental_system.py)
     to forget any previously-created Singleton instance, so the NEXT call to
     get_instance() is forced to build a fresh one against the new temp file.

Every test that needs the database simply asks for `clean_database` as a
parameter, e.g. `def test_something(clean_database): ...` - pytest runs the setup
above before the test body, then runs the cleanup after it finishes (whether the
test passed or failed), thanks to the `yield` keyword splitting this fixture into
"before" and "after" halves.
"""

import os
import tempfile

import pytest

import config
from database.db_connection import DatabaseConnection
from services.rental_system import RentalSystem


@pytest.fixture
def clean_database():
    """
    Points the whole application at a brand-new, empty, temporary SQLite file for
    the duration of one test, pre-loaded with the standard seed data (via
    RentalSystem.get_instance(), exactly like a real first run of main.py) so
    every test can rely on the same known accounts/vehicles/bookings existing.
    """
    original_db_file_name = config.DATABASE_FILE_NAME

    temp_file_descriptor, temp_path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(temp_file_descriptor)  # we only need the unique, empty file path itself

    config.DATABASE_FILE_NAME = temp_path
    DatabaseConnection.reset_instance_for_tests()
    RentalSystem.reset_instance_for_tests()

    rental_system = RentalSystem.get_instance()  # creates tables + seeds demo data

    yield rental_system

    # Clean up: close the connection, forget both singletons, restore config back
    # to the real database filename, and delete the temp file so repeated test
    # runs never leave clutter behind on disk.
    DatabaseConnection.reset_instance_for_tests()
    RentalSystem.reset_instance_for_tests()
    config.DATABASE_FILE_NAME = original_db_file_name
    if os.path.exists(temp_path):
        os.remove(temp_path)
