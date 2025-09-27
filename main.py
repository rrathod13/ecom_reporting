import sqlite3


def get_orders(id: str):
    return f"SELECT * FROM orders WHERE order_id = '{id}';"


def main():
    conn = sqlite3.connect("db/ecom_reporting.db")
    cursor = conn.cursor()

    sql_str = get_orders("e481f51cbdc54678b7cc49136f2d6af7")
    print(sql_str)

    print("\nExecuting query...\n")

    cursor.execute(sql_str)
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    conn.close()


if __name__ == "__main__":
    main()
