"""
cli/about_screen.py
=====================

WHAT THIS FILE IS FOR:
Shows the "About" screen (available from the public welcome menu, option 6): the
academic cover details for this assignment (programme, course, lecturer, student),
the project's name/version, and - as a small demonstration of the custom
@author_info decorator (see utils/author_decorator.py) - the authorship metadata
read directly OFF the RentalSystem class/object at runtime, rather than typed out
again by hand here.

WHY THIS PROVES THE DECORATOR ACTUALLY DID SOMETHING:
utils/author_decorator.py attaches __author__, __student_id__, and __institution__
attributes onto whatever it decorates. services/rental_system.py's RentalSystem
class is decorated with it. Reading those three attributes back here (instead of
importing config.STUDENT_NAME etc. a second time) is a small, honest proof that the
decorator is doing real work, not just sitting there unused.
"""

import config
from cli.common import print_header, print_divider, pause
from services.rental_system import RentalSystem


def show_about_screen():
    """Prints the academic cover block, project identity, and live decorator-read
    authorship metadata, then waits for the user to press Enter."""
    print_header("ABOUT " + config.PROJECT_NAME)

    print(f"Programme     : {config.PROGRAMME}")
    print(f"Course        : {config.COURSE_NAME}")
    print(f"Course Details: {config.COURSE_DETAILS}")
    print(f"Assessment    : {config.ASSESSMENT_TITLE}")
    print(f"Lecturer      : {config.LECTURER_NAME}")
    print(f"Student Name  : {config.STUDENT_NAME}")
    print(f"Student ID    : {config.STUDENT_ID}")
    print(f"Institution   : {config.INSTITUTION}")
    print_divider()
    print(f"Project       : {config.PROJECT_NAME}")
    print(f"Version       : {config.PROJECT_VERSION}")
    print_divider()

    # RentalSystem is the class decorated with @author_info - read its attributes
    # back out to show the decorator is genuinely attaching metadata at import
    # time, not just decoration for decoration's sake.
    print("Authorship metadata attached by the @author_info decorator")
    print("(see utils/author_decorator.py and services/rental_system.py):")
    print(f"  RentalSystem.__author__      = {getattr(RentalSystem, '__author__', 'n/a')}")
    print(f"  RentalSystem.__student_id__  = {getattr(RentalSystem, '__student_id__', 'n/a')}")
    print(f"  RentalSystem.__institution__ = {getattr(RentalSystem, '__institution__', 'n/a')}")

    pause()
