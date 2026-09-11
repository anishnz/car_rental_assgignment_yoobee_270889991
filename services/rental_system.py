"""
services/rental_system.py
============================

WHAT THIS FILE IS FOR:
Defines RentalSystem: the single top-level object that starts everything up when
the program runs - creating the database connection, building the tables if they
don't exist yet, and seeding the demo data on a first run. main.py talks to this
one object instead of importing the database/schema modules directly.

WHY A SINGLETON HERE TOO:
Just like DatabaseConnection (see database/db_connection.py), there should only ever
be ONE RentalSystem running the application at a time - it doesn't make sense to
"start the whole system" twice in the same run. Using the same Singleton pattern
here keeps that guarantee explicit rather than just hoping main.py only calls it
once.

WHY THE @author_info DECORATOR IS APPLIED HERE:
See utils/author_decorator.py for the full explanation of what this decorator does
and why. It is applied to this particular class because RentalSystem is the one
object that represents "the whole running application" - a natural place to attach
authorship metadata that the CLI's About screen can read back out.
"""

from database.db_connection import DatabaseConnection
from database.schema import init_database
from database.seed_data import seed_if_empty
from utils.author_decorator import author_info

import config


@author_info(name=config.STUDENT_NAME, student_id=config.STUDENT_ID, institution=config.INSTITUTION)
class RentalSystem:
    """Singleton facade that boots the whole Nepal Car Rental System."""

    _instance = None

    def __init__(self):
        if RentalSystem._instance is not None:
            raise RuntimeError("RentalSystem is a singleton - use RentalSystem.get_instance().")
        self.db = DatabaseConnection.get_instance()
        init_database(self.db)
        seed_if_empty(self.db)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance_for_tests(cls):
        """Test-only helper - see DatabaseConnection.reset_instance_for_tests()."""
        cls._instance = None

    def shutdown(self):
        """Closes the database connection cleanly - called once, on program exit."""
        self.db.close()
