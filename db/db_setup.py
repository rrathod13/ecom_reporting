from pathlib import Path

ORDERS_CSV = "olist_orders_dataset.csv"
ORDER_ITEMS_CSV = "olist_order_items_dataset.csv"


def db_setup(dataset_folder: Path):
    """First-time database setup."""
    import sqlite3

    import pandas as pd

    conn = sqlite3.connect("db/ecom_reporting.db")

    orders_df = pd.read_csv(dataset_folder / ORDERS_CSV)
    order_items_df = pd.read_csv(dataset_folder / ORDER_ITEMS_CSV)

    orders_df.to_sql("orders", conn, if_exists="replace", index=False)
    order_items_df.to_sql("order_items", conn, if_exists="replace", index=False)

    conn.close()


if __name__ == "__main__":
    db_setup(Path(__file__).parent / "archive")
