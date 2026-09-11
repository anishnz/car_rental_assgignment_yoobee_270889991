"""
database/db_connection.py
==========================

WHAT THIS FILE IS FOR:
Manages the single, shared connection to the project's SQLite database file. Every
other module that needs to run a query goes through this class instead of opening
its own separate connection to the same file.

WHY A SINGLETON (design pattern demonstrated):
A SINGLETON is a design pattern that guarantees only ONE instance of a class ever
exists in the whole running program, and gives every part of the code a single,
shared way to reach that instance. Here it means the whole application shares
exactly ONE connection to ncrs_database.sqlite3, instead of every file opening its
own independent connection to the same file - which could cause conflicting writes
and wasted memory. Python has no special "singleton" keyword, so the pattern is
built by hand using a class-level variable that remembers whether an instance has
already been created (see get_instance() below).
"""

import os
import sqlite3

import config


class DatabaseConnection:
    """
    Singleton wrapper around a single sqlite3 connection.

    Usage:
        db = DatabaseConnection.get_instance()
        db.execute("INSERT INTO vehicles (...) VALUES (?, ?)", (value1, value2))
        rows = db.fetch_all("SELECT * FROM vehicles")
    """

    _instance = None  # holds the ONE shared instance, once created

    def __init__(self):
        # Guard against someone accidentally calling DatabaseConnection() directly
        # instead of going through get_instance() - that would defeat the whole
        # point of the Singleton pattern.
        if DatabaseConnection._instance is not None:
            raise RuntimeError(
                "DatabaseConnection is a singleton - call "
                "DatabaseConnection.get_instance() instead of creating a new one."
            )

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, config.DATABASE_FILE_NAME)

        # check_same_thread=False just relaxes a default sqlite3 restriction that
        # does not matter for this simple, single-threaded CLI application.
        self.connection = sqlite3.connect(db_path, check_same_thread=False)

        # sqlite3.Row lets us access columns by name (row["username"]) instead of
        # only by position (row[1]) - much easier to read throughout the project.
        self.connection.row_factory = sqlite3.Row

        # SQLite does not enforce foreign keys unless we explicitly turn it on. With
        # this on, the database itself will reject, for example, a booking that
        # points at a customer_id that does not exist - an extra safety net on top
        # of our own validation code.
        self.connection.execute("PRAGMA foreign_keys = ON")

    @classmethod
    def get_instance(cls):
        """
        Returns the single shared DatabaseConnection, creating it the first time this
        is called ("lazy initialisation" - we don't open the database file until it
        is actually needed).
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance_for_tests(cls):
        """
        Test-only helper: closes and forgets the current singleton instance, so an
        automated test can point a fresh instance at a temporary database file
        instead of the real one. Application code (main.py, services, cli) never
        calls this - only tests/conftest.py does.
        """
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None

    def execute(self, query: str, params: tuple = ()):
        """
        Runs an INSERT / UPDATE / DELETE (or any statement that changes data) and
        commits the change immediately, so every write is saved to disk right away.

        IMPORTANT: `query` uses "?" placeholders and `params` is a tuple of the real
        values, e.g. execute("UPDATE vehicles SET status = ? WHERE vehicle_id = ?",
        (new_status, vehicle_id)). This is a PARAMETERISED QUERY - the standard, safe
        way to include user-supplied values in SQL. It stops "SQL injection" (a user
        typing SQL code into a text field to trick the database), which would be a
        real risk if we instead built query strings by joining text together.
        """
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor

    def fetch_one(self, query: str, params: tuple = ()):
        """Runs a SELECT and returns the first matching row, or None if there isn't one."""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query: str, params: tuple = ()):
        """Runs a SELECT and returns every matching row as a list."""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def close(self):
        """Closes the underlying connection - called once, when the program exits."""
        self.connection.close()
