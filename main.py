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


def get_prices_for_year(conn: sqlite3.Connection, year: int) -> pd.DataFrame:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT 
            strftime('%Y-%m', o.order_delivered_customer_date) AS month,
            SUM(oi.price) AS total_price
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
            AND strftime('%Y', o.order_delivered_customer_date) = '{year}'
        GROUP BY strftime('%Y-%m', o.order_delivered_customer_date)
        ORDER BY month;
        """,
    )
    rows = cursor.fetchall()
    return to_df(rows, cursor)


def get_avg_week_prices(
    conn: sqlite3.Connection, start: datetime, end: datetime
) -> pd.DataFrame:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT 
            strftime('%Y-%W', o.order_delivered_customer_date) AS week,
            AVG(oi.price) AS avg_price
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
            AND o.order_delivered_customer_date BETWEEN '{start}' AND '{end}'
        GROUP BY strftime('%Y-%W', o.order_delivered_customer_date)
        ORDER BY week;
        """,
    )
    rows = cursor.fetchall()
    return to_df(rows, cursor)


def calc_rma(df: pd.DataFrame, window: int) -> list[float]:
    # Calculate the rolling moving average (RMA) for a given window size
    return df["avg_price"].rolling(window=window).mean().tolist()


def main():
    conn = sqlite3.connect("db/ecom_reporting.db")

    # Get weekly prices for Q2 and Q3 2017
    res = get_avg_week_prices(
        conn,
        datetime(2017, 5, 1),
        datetime(2017, 8, 30),
    )

    plt.figure()
    plt.plot(res["week"], res["avg_price"], marker="o")
    plt.plot(res["week"], calc_rma(res, 4), label="4-week RMA", linestyle="--")
    plt.title("Avg Price per Week in Q2 2017")
    plt.xlabel("Week")
    plt.ylabel("Avg Price [$]")
    plt.xticks(res["week"], rotation=45)
    plt.grid()
    plt.legend()
    plt.show()

    conn.close()


if __name__ == "__main__":
    main()
