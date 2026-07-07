# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "bot.db"


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                model TEXT,
                price INTEGER,
                quantity INTEGER,
                phone TEXT,
                address TEXT,
                latitude REAL,
                longitude REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_order(tg_id, username, full_name, model, price, quantity, phone,
                  address=None, latitude=None, longitude=None):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO orders
               (tg_id, username, full_name, model, price, quantity, phone, address, latitude, longitude)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (tg_id, username, full_name, model, price, quantity, phone, address, latitude, longitude),
        )
        conn.commit()
        return cur.lastrowid


def get_order(order_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        return dict(row) if row else None
