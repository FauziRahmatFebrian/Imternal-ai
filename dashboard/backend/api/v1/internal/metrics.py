"""
Endpoint metrik operasional — TIDAK lewat AI Orchestrator sama sekali.
Query langsung ke data warehouse yang diisi oleh integration-layer.

Contoh: jumlah submit task per bulan (yang jadi contoh awal Anda dulu).
Ini sengaja dipisah dari ai-orchestration/ karena tidak ada alasan
memanggil LLM hanya untuk menghitung jumlah baris data.
"""
from fastapi import APIRouter
# from your_db_client import get_connection   # sesuaikan dengan DB Anda

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/tasks-submitted-per-month")
async def tasks_submitted_per_month():
    """
    Contoh query (sesuaikan nama tabel/kolom dengan skema data warehouse
    yang dihasilkan integration-layer):

    SELECT DATE_TRUNC('month', submitted_at) AS month, COUNT(*) AS total
    FROM tasks
    GROUP BY month
    ORDER BY month;
    """
    # placeholder — ganti dengan query nyata setelah integration-layer jalan
    return {"data": [], "note": "belum tersambung ke data warehouse asli"}
