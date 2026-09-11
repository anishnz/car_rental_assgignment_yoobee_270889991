"""
cli/common.py
==============

WHAT THIS FILE IS FOR:
Shared building blocks used by EVERY menu screen in the CLI, so the whole
application understands the same navigation commands (the "Option B" convention
agreed for this project - see README.md's "Navigation conventions" section):

    0        Back / Logout / Exit
    00       Reset test data (Super Administrator only)
    H        Show a short help message for the current prompt
    C        Cancel the current multi-step operation, back to the previous menu
    Ctrl+C   Safely exit the program at any time, from anywhere

WHY ONE SHARED read_input() FUNCTION (the concept being demonstrated):
Every single text prompt in this whole project calls the SAME function below,
instead of every menu screen writing its own input()/print() logic and quietly
handling "H" and "C" differently (or not at all) in different places. This is good
software engineering practice: one function, one clear job, reused everywhere,
means a bug fix or improvement here automatically applies to the entire CLI.
"""


class CancelOperation(Exception):
    """
    Raised internally when the user types "C" during a multi-step operation (like
    filling in a booking form). Calling code catches this ONE exception type around
    the whole multi-step flow, instead of checking "did they cancel?" after every
    single field.
    """
    pass


def print_header(title: str):
    line = "=" * 56
    print(f"\n{line}\n{title.center(56)}\n{line}\n")


def print_divider():
    print("-" * 56)


def read_input(field_label: str, help_text: str = None) -> str:
    """
    Prompts for one piece of text input, handling "H" (help) and "C" (cancel) the
    same way everywhere in the project.

    Returns the typed value (stripped of extra whitespace) once the user enters
    something that is not "H". Raises CancelOperation if they type "C" - the
    calling multi-step flow is expected to catch this.
    """
    while True:
        raw = input(f"{field_label}: ").strip()
        if raw.upper() == "H":
            print(help_text or "No extra help is available for this field.")
            continue
        if raw.upper() == "C":
            raise CancelOperation()
        return raw


def read_menu_choice(prompt_text: str = "Enter your choice") -> str:
    """
    Prompts for a menu selection (a number, or "0"/"00"/"H"). Unlike read_input(),
    this does NOT raise CancelOperation on "C" - most menus don't have a
    "cancel" concept for choosing a menu option (there's nothing to cancel out of
    yet), only for a multi-step form. The raw text is returned so each menu screen
    can decide what to do with "0", "00", "H", or a number.
    """
    return input(f"{prompt_text}: ").strip()


def confirm_yes_no(question: str) -> bool:
    """Asks a Yes/No question. Keeps asking until the user answers 1 (Yes) or 2 (No)."""
    while True:
        print(question)
        print("1. Yes")
        print("2. No")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            return True
        if choice == "2":
            return False
        print("Invalid input. Please enter 1 or 2.")


def pause():
    input("\nPress Enter to continue...")


def show_error(message: str):
    """
    Prints an error/validation message.

    FIX (reported bug - registration, and every other action in the app, did not
    clearly say whether it had succeeded or failed): show_error() and
    show_success() are the ONE shared function every single screen in this whole
    project calls to report an outcome (see the module docstring above on why
    that "one shared function" design matters) - so pausing HERE, in this one
    place, automatically makes every action everywhere (login, register, adding
    a vehicle, confirming a booking, recording a payment, and so on) hold the
    result on screen with "Press Enter to continue..." before the next menu is
    drawn. Without this, the message was technically printed, but the very next
    line of the program's main loop immediately redrew the next menu screen
    underneath it, so it looked like nothing had happened at all.
    """
    print(f"\n{message}\n")
    pause()


def show_success(message: str):
    """Prints a success message and holds the screen - see show_error() above
    for why pause() belongs here."""
    print(f"\n{message}\n")
    pause()
