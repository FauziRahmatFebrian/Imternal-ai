import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "integration-layer"))
from db_client import get_connection

AMBANG_TERLAMBAT_MINIMAL = 1 


def get_sop_settings(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT batas_jam_masuk, jam_kerja_normal_selesai FROM sop_settings LIMIT 1")
        return cur.fetchone()


def detect_keterlambatan(conn) -> list[dict]:
    sop = get_sop_settings(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT e.name AS nama, d.name AS divisi,
                   COUNT(*) AS jumlah_terlambat
            FROM attendance a
            JOIN employees e ON e.id = a.employee_id
            JOIN divisions d ON d.id = e.division_id
            WHERE a.clock_in > %s
            GROUP BY a.employee_id, e.name, d.name
            HAVING jumlah_terlambat >= %s
            ORDER BY jumlah_terlambat DESC
            """,
            (sop["batas_jam_masuk"], AMBANG_TERLAMBAT_MINIMAL),
        )
        return cur.fetchall()


def detect_lembur(conn) -> list[dict]:
    sop = get_sop_settings(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT e.name AS nama, d.name AS divisi,
                   COUNT(*) AS jumlah_hari_lembur,
                   ROUND(AVG(TIME_TO_SEC(TIMEDIFF(a.clock_out, %s)) / 60)) AS rata_menit_lembur
            FROM attendance a
            JOIN employees e ON e.id = a.employee_id
            JOIN divisions d ON d.id = e.division_id
            WHERE a.clock_out > %s
            GROUP BY a.employee_id, e.name, d.name
            ORDER BY rata_menit_lembur DESC
            """,
            (sop["jam_kerja_normal_selesai"], sop["jam_kerja_normal_selesai"]),
        )
        return cur.fetchall()


def get_produktivitas_per_divisi(conn) -> list[dict]:
    """
    Pengganti "deteksi penurunan task" versi lama -- karena skema baru
    tidak lagi punya event submit per task, cuma ringkasan harian.
    Ini tampilkan rata-rata task & jam kerja per divisi, per tanggal
    sampel yang ada -- supaya masih bisa dibandingkan antar bulan.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT d.name AS divisi, dt.work_date,
                   ROUND(AVG(dt.total_tasks), 1) AS rata_task,
                   ROUND(AVG(dt.total_hours), 1) AS rata_jam
            FROM daily_tasks dt
            JOIN employees e ON e.id = dt.employee_id
            JOIN divisions d ON d.id = e.division_id
            GROUP BY d.name, dt.work_date
            ORDER BY d.name, dt.work_date
            """
        )
        return cur.fetchall()


def run_all_detections() -> dict:
    conn = get_connection()
    try:
        return {
            "keterlambatan": detect_keterlambatan(conn),
            "lembur": detect_lembur(conn),
            "produktivitas_per_divisi": get_produktivitas_per_divisi(conn),
        }
    finally:
        conn.close()