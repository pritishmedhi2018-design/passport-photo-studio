import sqlite3
from datetime import datetime

DB_NAME = "sales.db"


def create_database():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_time TEXT,
        photo_type TEXT,
        layout INTEGER,
        total_photos INTEGER,
        amount REAL
    )
    """)

    conn.commit()
    conn.close()


def save_order(
    photo_type,
    layout,
    total_photos,
    amount
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO orders(
            date_time,
            photo_type,
            layout,
            total_photos,
            amount
        )
        VALUES(?,?,?,?,?)
        """,
        (
            datetime.now().strftime(
                "%d-%m-%Y %I:%M:%S %p"
            ),
            photo_type,
            layout,
            total_photos,
            amount
        )
    )

    conn.commit()
    conn.close()


def get_orders():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM orders
    ORDER BY id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data


def get_total_orders():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM orders
    """)

    result = cursor.fetchone()[0]

    conn.close()

    return result


def get_total_revenue():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT SUM(amount)
    FROM orders
    """)

    result = cursor.fetchone()[0]

    conn.close()

    if result is None:
        return 0

    return result


def get_today_revenue():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    today = datetime.now().strftime(
        "%d-%m-%Y"
    )

    cursor.execute("""
    SELECT date_time, amount
    FROM orders
    """)

    rows = cursor.fetchall()

    total = 0

    for row in rows:

        order_date = row[0]
        amount = row[1]

        if order_date.startswith(today):

            total += amount

    conn.close()

    return total


def get_today_orders():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    today = datetime.now().strftime(
        "%d-%m-%Y"
    )

    cursor.execute("""
    SELECT date_time
    FROM orders
    """)

    rows = cursor.fetchall()

    count = 0

    for row in rows:

        if row[0].startswith(today):
            count += 1

    conn.close()

    return count