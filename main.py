import sqlite3
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PLOT_DIR = Path("plots")


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
            AVG(oi.price) AS avg_price
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
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT 
            strftime('%Y-%W', o.order_delivered_customer_date) AS week,
            AVG(oi.price) AS price
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
    return df["price"].rolling(window=window).mean().tolist()


def calc_mults(df: pd.DataFrame, col: str) -> list[float]:
    # Calculate seasonal multipliers for each data point based on first point
    return (df[col] / df[col][0]).tolist()


# ----------------
# KPI Reports
# ----------------
def rma_report(conn: sqlite3.Connection, year: int, window: int = 4):
    df = get_avg_week_prices(
        conn,
        start=datetime(year, 1, 1),
        end=datetime(year, 12, 31),
    )

    # Calculate RMA
    df["rma"] = calc_rma(df, window=window)

    # Plot original prices and RMA
    plt.figure(figsize=(15, 6))
    plt.plot(df["week"], df["price"], marker="o", label="Avg Weekly Price")
    plt.plot(
        df["week"],
        df["rma"],
        label=f"{window}-Week RMA",
        color="orange",
        linestyle="--",
    )
    plt.title(f"Avg Weekly Prices and {window}-Week RMA for {year}")
    plt.xlabel("Week")
    plt.ylabel("Price [$]")
    plt.xticks(rotation=45)
    plt.grid()
    plt.legend()

    plt.savefig(PLOT_DIR / f"rma_report_{year}.png")


def year_forcast(conn: sqlite3.Connection, reference_year: int, forecast_year: int):
    df_ref = get_prices_for_year(conn, reference_year)

    # Calculate seasonal multipliers based on avg_price
    df_ref["seasonal_mults"] = calc_mults(df_ref, col="avg_price")

    df_for = get_prices_for_year(conn, forecast_year)

    all_months_for = [f"{forecast_year}-{i:02d}" for i in range(1, 13)]
    df_for = df_for.set_index("month").reindex(all_months_for).reset_index()
    df_for.columns = ["month", "avg_price"]

    jan_price = df_for["avg_price"].iloc[0]

    df_for["avg_price"] = df_for["avg_price"].fillna(
        df_ref["seasonal_mults"] * jan_price
    )

    plt.figure(figsize=(10, 6))
    plt.plot(df_for["month"], df_for["avg_price"], marker="o")
    plt.title(
        f"Forecasted Monthly Prices for {forecast_year} based on {reference_year}"
    )
    plt.xlabel("Month")
    plt.ylabel("Total Price [$]")
    plt.xticks(rotation=45)
    plt.grid()

    plt.savefig(
        PLOT_DIR / f"year_forecast_{forecast_year}_based_on_{reference_year}.png"
    )


def main():
    conn = sqlite3.connect("db/ecom_reporting.db")

    # Create a directory for plots if it doesn't exist
    PLOT_DIR.mkdir(exist_ok=True, parents=True)

    rma_report(conn, year=2017, window=4)
    year_forcast(conn, reference_year=2017, forecast_year=2018)

    conn.close()


if __name__ == "__main__":
    main()
