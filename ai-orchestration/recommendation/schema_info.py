import os
import pymysql
from dotenv import load_dotenv

load_dotenv()


def get_schema_description() -> str:
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_READONLY_USER"),
        password=os.getenv("DB_READONLY_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, ORDINAL_POSITION
                """,
                (os.getenv("DB_NAME"),),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    tables = {}
    for row in rows:
        tables.setdefault(row["TABLE_NAME"], []).append(f"{row['COLUMN_NAME']} {row['DATA_TYPE']}")

    lines = []
    for table_name, columns in tables.items():
        lines.append(f"Tabel {table_name} ({', '.join(columns)})")

    return "\n".join(lines)


# Di-cache sekali per proses -- supaya tidak query INFORMATION_SCHEMA
# tiap kali ada pertanyaan, cukup sekali di awal.
_cached_schema = None


def get_schema_description_cached() -> str:
    global _cached_schema
    if _cached_schema is None:
        _cached_schema = get_schema_description()
    return _cached_schema