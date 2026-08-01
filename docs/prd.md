# PRD — Dashboard AI Monitoring Internal

**Status dokumen:** mencerminkan kondisi project per hari ke-5 pengembangan. Beberapa bagian masih "belum selesai" dan ditandai jelas di bagian Keterbatasan — dokumen ini jujur soal itu, bukan menggambarkan kondisi ideal.

---

## 1. Latar Belakang & Masalah

Tim manajemen membutuhkan cara memantau kinerja operasional internal (kehadiran, task, kepatuhan SOP) tanpa harus membaca laporan mentah satu-satu. Proses manual ini lambat dan tidak konsisten — pola seperti "tim mana yang produktivitasnya turun" atau "siapa yang sering melanggar SOP" sulit terlihat tanpa analisis berulang.

## 2. Tujuan Produk

Membangun sistem yang bisa:
1. Menjawab pertanyaan bebas (bahasa natural) tentang data operasional — kehadiran, task, kepatuhan SOP.
2. Menghasilkan insight otomatis dari data yang sudah pasti (rule-based), dirangkai jadi narasi oleh AI.
3. Menjamin data sensitif (nama, kehadiran individu) diproses dengan kontrol keamanan yang jelas.

## 3. Target Pengguna

Tim manajemen internal perusahaan — bukan technical user. Antarmuka akhir yang dituju: dashboard web, saat ini **baru tersedia lewat CLI** (lihat bagian Keterbatasan).

## 4. Ruang Lingkup

### 4.1 Fitur yang sudah dibangun dan berfungsi

| Fitur | Deskripsi | Status |
|---|---|---|
| Local LLM | `phi4-mini` via Ollama, jalan CPU-only | Selesai, teruji |
| MCP Server | Akses terstandar ke data warehouse (MySQL) via HTTP | Selesai, teruji |
| RAG (dokumen SOP) | Chroma + embedding Ollama, chunking berbasis paragraf+tabel, label per tim | Selesai, teruji — **threshold relevansi belum dikalibrasi** |
| AI Recommendation (rule-based) | `policy_rules.py`: deteksi keterlambatan, lembur, produktivitas per divisi — murni SQL, tidak pernah dihitung AI | Selesai, teruji |
| Text-to-SQL | LLM menyusun query SELECT dari pertanyaan bebas, dijalankan read-only | Selesai, teruji |
| Intent Router + Context Gatherer | Deteksi kata kunci, panggil beberapa sumber data paralel, gabung jadi 1 konteks | Selesai, teruji |
| Guardrails | Validasi jawaban akhir (kosong, kepanjangan, frasa mencurigakan) | Selesai, terpasang — validasi masih dasar |
| Scope Guard | Tolak pertanyaan di luar topik operasional internal, via Local LLM | Selesai, terpasang |
| Retry logic | Percobaan ulang otomatis untuk panggilan HTTP (Ollama, 9Router, MCP) | Selesai |
| Connection pooling | `DBUtils.PooledDB` untuk koneksi MySQL | Selesai, terpasang |
| Endpoint `/health` | Cek status Ollama, MySQL, MCP, 9Router | Selesai |
| Endpoint `/history` | Baca riwayat request dari Langfuse | Kode selesai — **belum diverifikasi jalan** (Langfuse belum full setup) |
| Chatbot CLI | `chat_cli.py`, mendukung command manual + jalur otomatis | Selesai, teruji |

### 4.2 Fitur yang direncanakan tapi belum dibangun

- Dashboard web (frontend) — **belum ada sama sekali**, semua akses sejauh ini lewat terminal.
- API eksternal untuk SaaS lain.
- Security & Governance matang (RBAC, audit log penuh, rotasi key terjadwal).
- Data masking (PII) — **sempat dibangun, lalu dihapus atas keputusan pemilik project** (lihat bagian Risiko).

## 5. Non-Functional Requirements

| Aspek | Target/Kondisi |
|---|---|
| Hardware | Laptop CPU-only (Intel HD 520, 16GB RAM) — tanpa GPU |
| Konkurensi | Belum diuji dengan beban nyata; estimasi awal Ollama mulai kesulitan di atas ~5 user bersamaan (belum dibuktikan dengan load test) |
| Keamanan data sensitif | Data sensitif (ditandai `sensitive: true`) wajib lewat Local LLM, tidak pernah lewat 9Router |
| Ketepatan angka | Semua angka pasti (jumlah, persentase, rata-rata) wajib dihitung SQL, LLM cuma merangkai narasi — tidak pernah menghitung sendiri |

## 6. User Stories (yang sudah terpenuhi)

- **Sebagai manajer**, saya bisa bertanya "siapa yang paling sering terlambat?" dan mendapat jawaban berbasis data asli, bukan tebakan AI.
- **Sebagai manajer**, saya bisa bertanya soal isi SOP ("apa aturan lembur?") dan mendapat jawaban yang menyebut sumber dokumennya.
- **Sebagai manajer**, saya bisa bertanya hal yang butuh gabungan data + SOP sekaligus ("apakah ada yang lembur melebihi ketentuan SOP?") dalam satu jawaban.
- **Sebagai admin sistem**, saya bisa cek `/health` untuk tahu service mana yang mati tanpa harus debug manual satu-satu.

## 7. Keterbatasan & Risiko yang Diketahui (per hari ke-5)

Ini bagian paling penting dari dokumen ini — jangan dilewati.

1. **`MAX_DISTANCE_THRESHOLD` di RAG masih `999`** (efektif tidak memfilter apapun). Perlu dikalibrasi dengan data distance asli sebelum bisa dipercaya menyaring hasil tidak relevan.
2. **Langfuse belum terbukti mencatat data** — Docker sudah bisa dijalankan, tapi `LANGFUSE_PUBLIC_KEY`/`SECRET_KEY` belum diisi terakhir dicek, jadi `/history` belum bisa dites end-to-end.
3. **Data masking (Presidio) sudah dibangun, lalu dihapus** atas keputusan pemilik project. Konsekuensinya: nama karyawan sekarang terkirim apa adanya ke 9Router untuk jalur non-sensitif. Ini aman **selama** 9Router tidak meneruskan ke provider cloud pihak ketiga yang menyimpan data — **status ini tidak pernah dikonfirmasi**, lihat poin 4.
4. **9Router adalah kotak hitam** — tidak diketahui pasti provider apa yang ada di baliknya, apakah benar-benar "Cloud LLM" seperti di capability matrix awal, atau cuma proxy ke model lokal juga.
5. **Tidak ada autentikasi di `/analyze`** — endpoint terbuka tanpa proteksi, siapa saja yang tahu URL bisa memanggilnya.
6. **Tidak ada frontend** — seluruh pembuktian fungsi sejauh ini lewat CLI dan `Invoke-RestMethod`, belum ada UI yang bisa dipakai tim manajemen non-teknis.
7. **`Scope Guard` menambah 1 panggilan LLM ekstra** di setiap request (via Local LLM) — menambah latency untuk semua pertanyaan, termasuk yang jelas relevan.
8. **Belum ada automated test** (`pytest`) untuk `policy_rules.py` atau komponen lain — validasi sejauh ini manual lewat CLI.
9. **`git init` belum dilakukan** — belum ada version control resmi untuk project ini.
10. **Konkurensi belum diuji dengan angka nyata** — semua klaim soal batas ~5 user itu masih teori dari riset umum, belum load-test sungguhan di laptop ini.

## 8. Roadmap (revisi dari matrix awal)

| Fase | Fokus |
|---|---|
| Selesai (Hari 1-5) | Local LLM, MCP, RAG, AI Recommendation, text-to-SQL, intent router, guardrails, scope guard, retry logic, health check |
| Berikutnya (prioritas) | Kalibrasi threshold RAG, verifikasi Langfuse end-to-end, unit test, git init |
| Menyusul | Frontend dashboard, autentikasi API, containerize orchestrator |
| Terakhir | Security & governance matang (RBAC, audit log), keputusan ulang soal data masking |