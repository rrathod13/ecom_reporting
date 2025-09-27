import sqlite3
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd


def to_df(rows, cursor: sqlite3.Cursor):
    return pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])


def get_order_id_by_date(
    conn: sqlite3.Connection,
    order_status: str,
    delivery_date_range: tuple[datetime, datetime],
    limit: int | None = None,
) -> list[str]:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT order_id FROM orders
        WHERE order_status = '{order_status}'
        AND order_delivered_customer_date BETWEEN '{delivery_date_range[0]}' AND '{delivery_date_range[1]}'
        {f'LIMIT {limit}' if limit is not None else ''};
        """,
    )
    rows = cursor.fetchall()
    return to_df(rows, cursor)["order_id"].tolist()


def get_price_by_order_id(
    conn: sqlite3.Connection,
    order_id: list[str],
    limit: int | None = None,
) -> list[float]:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT price FROM order_items
        WHERE order_id IN ({', '.join(['?' for _ in order_id])})
        {f'LIMIT {limit}' if limit is not None else ''};
        """,
        order_id,
    )
    rows = cursor.fetchall()
    return to_df(rows, cursor)["price"].tolist()


def main():
    conn = sqlite3.connect("db/ecom_reporting.db")

    # Get total price per month in 2018
    months = list(range(1, 13))
    prices = []
    for month in months:
        start_date = datetime(2018, month, 1)
        if month == 12:
            end_date = datetime(2019, 1, 1)
        else:
            end_date = datetime(2018, month + 1, 1)

        ids = get_order_id_by_date(
            conn,
            "delivered",
            (start_date, end_date),
            limit=10,
        )
        total_price = 0.0
        for order_id in ids:
            order_prices = get_price_by_order_id(conn, [order_id])
            total_price += sum(order_prices)

        prices.append(total_price)
        print(f"Month: {month}, Total Price: {total_price}")

    plt.figure()
    plt.plot(months, prices, marker="o")
    plt.title("Total Price per Month in 2018")
    plt.xlabel("Month")
    plt.ylabel("Total Price")
    plt.xticks(months)
    plt.grid()
    plt.show()

    conn.close()


if __name__ == "__main__":
    main()
