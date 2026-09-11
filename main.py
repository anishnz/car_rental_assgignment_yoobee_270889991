"""
main.py
========

WHAT THIS FILE IS FOR:
The single entry point for the entire Nepal Car Rental System (NCRS). Running
this file (`python main.py`) is ALL that is needed to start the whole
application - it boots the RentalSystem Singleton (which sets up the SQLite
database and seeds the demo data on a first run), then hands control to the
public welcome-screen loop (cli/public_menu.py) until the user exits.

WHY KeyboardInterrupt IS HANDLED HERE (and nowhere else):
Ctrl+C must be able to safely exit the program from ANY screen, at ANY point
(see the "Navigation conventions" in README.md). Rather than wrapping every
single input() call across the whole CLI in its own try/except, Python lets a
KeyboardInterrupt (the exception Ctrl+C raises) propagate all the way up
through every function call until it reaches THIS one try/except at the very
top of the program. This is a clean, simple way to guarantee a safe, friendly
shutdown message everywhere, using a single piece of code.

WHY shutdown() IS IN A `finally` BLOCK:
A `finally` block always runs, whether the program exited normally, via
Ctrl+C, or because of an unexpected error - so the database connection is
always closed cleanly (see database/db_connection.py's close()), never left
open by accident.
"""

import sys

from cli import public_menu
from services.rental_system import RentalSystem
import config


def main():
    print("=" * 56)
    print(f"  Starting {config.PROJECT_NAME} (v{config.PROJECT_VERSION})...")
    print("=" * 56)

    rental_system = RentalSystem.get_instance()

    try:
        public_menu.run()
    except KeyboardInterrupt:
        # Ctrl+C was pressed - this is a NORMAL, supported way to exit (see the
        # "Navigation conventions" section of README.md), not a crash, so we
        # print a clean message instead of letting Python show a traceback.
        print("\n\nCtrl+C detected - exiting safely. Goodbye!\n")
    finally:
        rental_system.shutdown()


if __name__ == "__main__":
    # This guard means main() only runs when this file is executed directly
    # (e.g. `python main.py`), not if it were ever imported by another module
    # (for example, by the test suite) - a standard, expected Python pattern.
    sys.exit(main() or 0)
