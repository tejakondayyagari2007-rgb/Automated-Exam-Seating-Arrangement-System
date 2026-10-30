import getpass

from flask import Flask

from backend.database.connection import (
    check_mysql,
    close_db,
    execute,
    fetch_one,
    get_db,
)
from backend.utils.security import hash_password
from config import Config


LOCK_NAME = "exam_seating_system_initial_admin"


def required_input(prompt):
    value = input(prompt).strip()
    if not value:
        raise ValueError("This value cannot be blank.")
    return value


def create_initial_admin():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.teardown_appcontext(close_db)

    with app.app_context():
        if not check_mysql():
            raise RuntimeError("MySQL is unavailable; no account was created.")

        connection = get_db()
        if not connection.__class__.__module__.startswith("mysql"):
            raise RuntimeError("The database helper did not connect to MySQL; no account was created.")

        name = required_input("Admin name: ")
        username = required_input("Admin username: ")
        email = required_input("Admin email: ")
        password = getpass.getpass("Admin password: ")
        confirmation = getpass.getpass("Confirm password: ")
        if not password:
            raise ValueError("Password cannot be blank.")
        if password != confirmation:
            raise ValueError("Passwords do not match.")

        lock = fetch_one("SELECT GET_LOCK(%s, 0) AS acquired", (LOCK_NAME,))
        if not lock or lock.get("acquired") != 1:
            raise RuntimeError("Could not acquire the initial-admin setup lock; no account was created.")

        try:
            admin = fetch_one(
                "SELECT id FROM users WHERE role = %s LIMIT 1",
                ("ADMIN",),
            )
            if admin:
                raise RuntimeError("An admin account already exists; no account was created.")

            existing_user = fetch_one(
                "SELECT id FROM users WHERE username = %s OR email = %s LIMIT 1",
                (username, email),
            )
            if existing_user:
                raise RuntimeError("That username or email is already in use; no account was created.")

            execute(
                """
                INSERT INTO users
                    (name, username, email, role, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, 'ADMIN', %s, NOW(), NOW())
                """,
                (name, username, email, hash_password(password)),
            )
        finally:
            released = fetch_one("SELECT RELEASE_LOCK(%s) AS released", (LOCK_NAME,))
            if not released or released.get("released") != 1:
                raise RuntimeError("Could not release the initial-admin setup lock.")

    print("Initial admin account created.")


if __name__ == "__main__":
    create_initial_admin()
