"""
db.py
------
Lightweight SQLite persistence layer — no ORM, just sqlite3 and plain
SQL, so the project has zero extra dependencies beyond Flask.

Two tables:
  transactions(id, date, description, category, amount, txn_type)
    - amount is always stored as a positive number
    - txn_type is 'income' or 'expense'
  budgets(category, monthly_limit)
    - a monthly spending limit per category, used for budget-vs-actual insights
"""

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "finance.db")


@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                txn_type TEXT NOT NULL CHECK (txn_type IN ('income', 'expense'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL
            )
        """)


def add_transaction(date, description, category, amount, txn_type):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO transactions (date, description, category, amount, txn_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (date, description, category, abs(amount), txn_type),
        )
        return cur.lastrowid


def add_transactions_bulk(rows):
    """rows: list of (date, description, category, amount, txn_type) tuples."""
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO transactions (date, description, category, amount, txn_type) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )


def delete_transaction(txn_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))


def get_transactions(limit=None, month=None):
    """
    Return transactions, newest first. If month is given (format 'YYYY-MM'),
    only transactions in that month are returned.
    """
    query = "SELECT * FROM transactions"
    params = []
    if month:
        query += " WHERE date LIKE ?"
        params.append(f"{month}%")
    query += " ORDER BY date DESC, id DESC"
    if limit:
        query += " LIMIT ?"
        params.append(limit)

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_all_months():
    """Return distinct 'YYYY-MM' months present in the data, newest first."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(date, 1, 7) AS month FROM transactions "
            "ORDER BY month DESC"
        ).fetchall()
        return [r["month"] for r in rows if r["month"]]


def set_budget(category, monthly_limit):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
            "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
            (category, monthly_limit),
        )


def get_budgets():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM budgets ORDER BY category").fetchall()
        return {r["category"]: r["monthly_limit"] for r in rows}


def delete_budget(category):
    with get_conn() as conn:
        conn.execute("DELETE FROM budgets WHERE category = ?", (category,))
