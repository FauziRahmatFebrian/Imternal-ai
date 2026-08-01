"""
scope_guard.py — filter topik SEBELUM decision.py. Cuma terima pertanyaan
seputar operasional internal perusahaan, tolak yang di luar itu.

SENGAJA PAKAI LOCAL LLM (Ollama), BUKAN 9Router.

CATATAN: phi4-mini (model kecil) kadang tidak konsisten mengikuti
instruksi "jawab satu kata" -- prompt ini dikasih CONTOH (few-shot)
supaya lebih akurat, dan parsing-nya dibuat FAIL-OPEN (kalau jawaban
model ambigu/tidak jelas, DIIZINKAN, bukan ditolak) -- karena menolak
pertanyaan yang sah itu lebih mengganggu daripada sesekali kelolosan
pertanyaan di luar topik.
"""
from local_client import call_local

SCOPE_DESCRIPTION = """Topik DIIZINKAN: kehadiran karyawan, keterlambatan, lembur,
produktivitas/task, SOP perusahaan, kebijakan HR, data divisi/departemen,
kontrak kerja sama (PKS), dan operasional internal perusahaan lainnya.

Topik DITOLAK: rekomendasi makanan, hiburan, berita umum, cuaca, dan
hal-hal di luar operasional internal perusahaan.

Contoh:
"berapa yang terlambat bulan ini?" -> YA
"ada SOP apa saja?" -> YA
"apa aturan lembur?" -> YA
"berapa harga mie goreng?" -> TIDAK
"film apa yang bagus?" -> TIDAK"""


async def is_in_scope(question: str) -> bool:
    prompt = f"""{SCOPE_DESCRIPTION}

Pertanyaan: "{question}"

Jawab HANYA dengan satu kata di baris pertama: YA atau TIDAK."""

    answer = await call_local(prompt)
    first_line = answer.strip().split("\n")[0].upper()

    # Fail-open: cuma tolak kalau model EKSPLISIT bilang TIDAK.
    # Kalau jawabannya ambigu/tidak jelas, default IZINKAN -- lebih
    # aman untuk usability daripada salah tolak pertanyaan yang sah.
    if "TIDAK" in first_line and "YA" not in first_line:
        return False
    return True

if __name__ == "__main__":
    import asyncio

    test_questions = [
        "ada berapa karyawan yang terlambat",
        "ada sop apa saja",
        "apa makanan yang enak",
    ]

    async def _test():
        for q in test_questions:
            result = await is_in_scope(q)
            print(f"Q: {q}\n  -> in_scope: {result}\n")

    asyncio.run(_test())