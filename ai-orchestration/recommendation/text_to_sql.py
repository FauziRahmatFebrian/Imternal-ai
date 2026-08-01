import os
import re
import sys
import pymysql
from dotenv import load_dotenv
from openai import OpenAI

from schema_info import get_schema_description_cached

load_dotenv()

client = OpenAI(
    base_url=os.getenv("NINEROUTER_BASE_URL", "http://localhost:20128/v1"),
    api_key=os.getenv("NINEROUTER_API_KEY", "sk-4e3d787874101446-dbhrqv-ddfc1e86"),
)
MODEL_NAME = os.getenv("NINEROUTER_MODEL", "free_tier")

FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "truncate",
    "grant", "revoke", "create", "replace", "call", "exec", ";--", "/*",
]


def get_readonly_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_READONLY_USER"),
        password=os.getenv("DB_READONLY_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def generate_sql(question: str) -> str:
    schema = get_schema_description_cached()

    prompt = f"""Kamu adalah generator query SQL MySQL. Skema database:
{schema}

Aturan WAJIB:
- HANYA tulis satu query SELECT, tanpa penjelasan, tanpa markdown, tanpa titik koma di akhir.
- JANGAN gunakan INSERT/UPDATE/DELETE/DROP/ALTER/CREATE dalam bentuk apapun.
- Kalau pertanyaan tidak bisa dijawab dari skema ini, tulis persis: TIDAK_BISA_DIJAWAB

Pertanyaan: {question}

Query SQL:"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    sql = response.choices[0].message.content.strip()
    sql = re.sub(r"^```sql\s*|```$", "", sql, flags=re.IGNORECASE).strip()
    return sql


def is_sql_safe(sql: str) -> bool:
    lowered = sql.lower().strip()
    if not lowered.startswith("select"):
        return False
    return not any(keyword in lowered for keyword in FORBIDDEN_KEYWORDS)


def run_text_to_sql(question: str) -> dict:
    sql = generate_sql(question)

    if sql == "TIDAK_BISA_DIJAWAB":
        return {"success": False, "reason": "Pertanyaan di luar cakupan data yang tersedia.", "sql": None}

    if not is_sql_safe(sql):
        return {"success": False, "reason": f"Query ditolak karena tidak aman: {sql}", "sql": sql}

    try:
        conn = get_readonly_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
            return {"success": True, "sql": sql, "rows": rows}
        finally:
            conn.close()
    except Exception as e:
        return {"success": False, "reason": f"Query gagal dijalankan: {e}", "sql": sql}


def answer_with_narration(question: str) -> str:
    result = run_text_to_sql(question)

    if not result["success"]:
        return f"Tidak bisa menjawab lewat text-to-SQL: {result['reason']}"
    prompt = (
        f"Pertanyaan: {question}\n"
        f"Hasil query database (data pasti, JANGAN dihitung ulang): {masked_rows}\n\n"
        "Rangkai hasil ini jadi jawaban singkat (1-3 kalimat) Bahasa Indonesia, natural. "
        "Gunakan HANYA angka dari hasil query di atas."
    )
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content