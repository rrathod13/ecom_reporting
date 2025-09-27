import sqlite3


def main():
    conn = sqlite3.connect("db/ecom_reporting.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders LIMIT 5;")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    conn.close()


if __name__ == "__main__":
    main()
