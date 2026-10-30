import os
from contextlib import closing

import mysql.connector
from flask import g

from config import config


class DatabaseConnection:
    @staticmethod
    def get_config():
        return {
            "host": config.MYSQL_HOST,
            "user": config.MYSQL_USER,
            "password": config.MYSQL_PASSWORD,
            "database": config.MYSQL_DATABASE,
            "port": config.MYSQL_PORT,
            "autocommit": True,
            "charset": "utf8mb4",
            "raise_on_warnings": True,
        }

    @staticmethod
    def connect():
        try:
            return mysql.connector.connect(**DatabaseConnection.get_config())
        except Exception:
            sqlite_db = os.path.join(os.getcwd(), "exam_seating_system.db")
            import sqlite3
            connection = sqlite3.connect(sqlite_db)
            connection.row_factory = sqlite3.Row
            return connection


def check_mysql():
    with closing(mysql.connector.connect(**DatabaseConnection.get_config())) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)


def get_db():
    if "db" not in g:
        g.db = DatabaseConnection.connect()
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def fetch_all(query, params=()):
    conn = get_db()
    if conn.__class__.__module__.startswith("mysql"):
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def fetch_one(query, params=()):
    conn = get_db()
    if conn.__class__.__module__.startswith("mysql"):
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        return row
    cursor = conn.execute(query, params)
    row = cursor.fetchone()
    return dict(row) if row else None


def execute(query, params=()):
    conn = get_db()
    if conn.__class__.__module__.startswith("mysql"):
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        last_id = cursor.lastrowid
        cursor.close()
        return last_id
    cursor = conn.execute(query, params)
    conn.commit()
    return cursor.lastrowid


def init_db():
    schema_path = os.path.join(os.getcwd(), "database", "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as file:
            script = file.read()
        conn = get_db()
        if conn.__class__.__module__.startswith("mysql"):
            cursor = conn.cursor()
            for statement in script.split(";"):
                if statement.strip():
                    try:
                        cursor.execute(statement)
                    except mysql.connector.Error as error:
                        if (
                            error.errno == 1050
                            and statement.lstrip().upper().startswith("CREATE TABLE IF NOT EXISTS")
                        ):
                            continue
                        raise
            cursor.close()
            conn.commit()
        else:
            conn.executescript(script)
            conn.commit()
