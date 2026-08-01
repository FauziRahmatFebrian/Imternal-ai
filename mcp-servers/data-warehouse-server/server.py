"""
MCP server — data warehouse. Sekarang query ke MySQL asli (bukan dummy lagi),
lewat db_client.py di integration-layer.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "integration-layer"))
from db_client import get_connection

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("data-warehouse-server", host="127.0.0.1", port=8200)


@mcp.tool()
def get_monthly_task_counts(months_back: int = 3) -> dict:
    """
    Ambil rata-rata task per hari sampel, dari tabel daily_tasks (skema baru).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DATE_FORMAT(work_date, '%%Y-%%m') AS month,
                       ROUND(AVG(total_tasks), 1) AS avg_tasks
                FROM daily_tasks
                GROUP BY month
                ORDER BY month DESC
                LIMIT %s
                """,
                (months_back,),
            )
            rows = cursor.fetchall()
        return {"data": rows}
    finally:
        conn.close()


@mcp.tool()
def get_data_freshness() -> dict:
    """
    Cek data kehadiran/task paling baru yang ada di database -- proxy
    sederhana untuk "seberapa baru data ini", karena integration-layer
    penuh (penarik data terjadwal) belum dibangun.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(submitted_at) AS last_task FROM tasks")
            last_task = cursor.fetchone()
            cursor.execute("SELECT MAX(tanggal) AS last_kehadiran FROM kehadiran")
            last_kehadiran = cursor.fetchone()
        return {
            "last_task_at": str(last_task["last_task"]),
            "last_kehadiran_at": str(last_kehadiran["last_kehadiran"]),
        }
    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
