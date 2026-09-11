"""
utils/formatters.py
====================

WHAT THIS FILE IS FOR:
Small helper functions that turn raw data (numbers, lists of database rows) into
neatly formatted text for the CLI to print. Keeping this separate from the business
logic (in services/) and the menu code (in cli/) means the same formatting rule -
for example, how a price is displayed - is written once and reused everywhere.
"""

from tabulate import tabulate

import config


def format_currency(amount: float) -> str:
    """
    Formats a number as a currency string using the project's currency symbol, with
    thousands separators and 2 decimal places, e.g. format_currency(1200) ->
    "NZD$1,200.00". Every place in the project that shows a price calls this
    function, so the currency symbol only needs to be defined once (in config.py).
    """
    return f"{config.CURRENCY_SYMBOL}{amount:,.2f}"


def format_table(headers: list, rows: list) -> str:
    """
    Formats a list of rows (each row itself a list of values, in the same order as
    `headers`) as a clean, aligned text table for the CLI, using the third-party
    `tabulate` package (see README section 4 for why this package was chosen).
    """
    if not rows:
        return "(no records to show)"
    return tabulate(rows, headers=headers, tablefmt="simple")


def mask_password() -> str:
    """
    Returns the fixed placeholder text shown in place of a real password anywhere a
    password would otherwise be displayed (see FR4a) - a hashed password can never
    be turned back into its original value, so this is always the same text rather
    than anything derived from the actual stored hash.
    """
    return "****** (hashed)"
