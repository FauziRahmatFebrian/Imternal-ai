import os
from dotenv import load_dotenv
from openai import OpenAI

from policy_rules import run_all_detections

load_dotenv()

client = OpenAI(
    base_url=os.getenv("NINEROUTER_BASE_URL", "http://localhost:20128/v1"),
    api_key=os.getenv("NINEROUTER_API_KEY", "sk-4e3d787874101446-dbhrqv-ddfc1e86"),
)
MODEL_NAME = os.getenv("NINEROUTER_MODEL", "free_tier")


def format_findings_as_text(findings: dict) -> str:
    parts = []

    if findings["keterlambatan"]:
        parts.append("Keterlambatan (dari seluruh data yang tersedia):")
        for row in findings["keterlambatan"]:
            parts.append(f"- {row['nama']} ({row['divisi']}): {row['jumlah_terlambat']} kali terlambat")
    else:
        parts.append("Tidak ada karyawan yang tercatat terlambat.")
    parts.append("")

    if findings["lembur"]:
        parts.append("Lembur (dari seluruh data yang tersedia):")
        for row in findings["lembur"]:
            parts.append(
                f"- {row['nama']} ({row['divisi']}): {row['jumlah_hari_lembur']} hari lembur, "
                f"rata-rata {row['rata_menit_lembur']} menit/hari"
            )
    else:
        parts.append("Tidak ada data lembur.")
    parts.append("")

    if findings["produktivitas_per_divisi"]:
        parts.append("Rata-rata task & jam kerja per divisi, per tanggal sampel:")
        for row in findings["produktivitas_per_divisi"]:
            parts.append(
                f"- {row['divisi']} ({row['work_date']}): {row['rata_task']} task/hari, "
                f"{row['rata_jam']} jam/hari"
            )
    else:
        parts.append("Tidak ada data produktivitas.")

    return "\n".join(parts)


def call_9router(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def main():
    print("Menjalankan deteksi rule-based dari database...")
    findings = run_all_detections()

    findings_text = format_findings_as_text(findings)
    print("\n=== Hasil deteksi (murni SQL, tanpa AI) ===")
    print(findings_text)

    if not any(findings.values()):
        print("\nTidak ada kondisi yang layak disorot bulan ini. Selesai (LLM tidak dipanggil).")
        return

    prompt = (
        "Kamu adalah asisten yang merangkai temuan data kepegawaian menjadi "
        "ringkasan singkat untuk tim manajemen. ATURAN: hanya gunakan angka "
        "yang ada di data berikut, jangan menambah asumsi atau angka lain. "
        "Tulis dalam bentuk paragraf mengalir, BUKAN dalam bentuk daftar/bullet.\n\n"
        f"Data temuan:\n{findings_text}\n\n"
        "Tulis ringkasan singkat (maksimal 5 kalimat) dalam Bahasa Indonesia "
        "untuk tim manajemen, bahasa profesional dan netral, dalam bentuk paragraf."
    )

    print("\nMengirim ke LLM lewat 9Router untuk dirangkai jadi narasi...")
    narasi = call_9router(prompt)

    print("\n=== Narasi hasil AI (lewat 9Router) ===")
    print(narasi)


if __name__ == "__main__":
    main()
