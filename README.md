# Dashboard AI Monitoring Internal

Dashboard monitoring operasional internal dengan kemampuan tanya-jawab bahasa natural menggunakan AI. Sistem ini memungkinkan tim manajemen bertanya tentang kehadiran, produktivitas, dan kepatuhan SOP dalam bahasa sehari-hari, dengan jawaban yang dihasilkan dari kombinasi deteksi rule-based (SQL) dan AI — bukan AI yang menghitung sendiri.

**Status:** Prototype Hari ke-5 — fungsional lewat CLI dan API, **belum ada frontend/dashboard web**.

> ⚠️ **Sebelum clone/pakai repo ini:** pastikan file `.env` (bukan `.env.example`) **tidak** ikut ter-commit. Kalau repo ini public dan pernah ter-push `.env` berisi kredensial asli, anggap semua kredensial itu bocor dan **wajib diganti** (password database, API key 9Router, secret key Langfuse) sebelum lanjut pakai.

## Fitur Utama

- **Natural Language Query** — tanya data operasional dalam bahasa Indonesia bebas
- **Dual-Path AI** — data sensitif diproses Local LLM (Ollama), request umum lewat 9Router
- **Context Gathering Paralel** — beberapa sumber data (MCP, RAG, SQL, business rules) dipanggil bersamaan, digabung jadi satu konteks, dijawab sekali oleh LLM
- **AI Recommendation (rule-based)** — deteksi keterlambatan, lembur, dan tren produktivitas per divisi, murni dihitung SQL; AI cuma merangkai jadi narasi
- **Text-to-SQL** — pertanyaan bebas diubah jadi query SQL oleh LLM, dijalankan read-only, dengan validasi keamanan
- **RAG untuk dokumen SOP** — pencarian isi SOP (PDF, termasuk tabel) berbasis embedding, bukan pencarian kata kunci biasa
- **Scope Guard** — menolak pertanyaan di luar topik operasional internal, dicek lewat Local LLM
- **Guardrails** — validasi jawaban akhir (kosong, kepanjangan, frasa mencurigakan) sebelum dikirim ke pengguna
- **Retry + Connection Pooling** — pemanggilan HTTP (Ollama/9Router/MCP) otomatis dicoba ulang; koneksi MySQL memakai pool, bukan buka-tutup tiap request
- **Health Check** — endpoint untuk cek status semua service dependency sekaligus

## Arsitektur

```
Pengguna bertanya
        │
        ▼
Scope Guard (Local LLM) — tolak kalau di luar topik operasional internal
        │
        ▼
Cek: ditandai sensitif?
   ├── YA  → Local LLM (Ollama) langsung, TIDAK lewat 9Router sama sekali
   └── TIDAK → Intent Router (keyword) → pilih tool relevan
                    │
                    ▼
              Context Gatherer — panggil PARALEL:
                ├── business_rules (policy_rules.py, SQL)
                ├── mcp (MCP server, data warehouse)
                ├── sql (text-to-SQL, read-only)
                └── rag (dokumen SOP, Chroma+embedding)
                    │
                    ▼
              9Router — jawab SEKALI dari konteks gabungan
        │
        ▼
Guardrails (validasi jawaban) → Langfuse (catat request) → Jawaban ke pengguna
```

**Prinsip desain:**
- AI **tidak pernah menghitung angka sendiri** — semua metrik pasti (jumlah, persentase, rata-rata) dihitung SQL, AI cuma merangkai jadi kalimat
- Data sensitif **wajib** lewat Local LLM — 9Router tidak dipakai untuk data itu, apapun alasannya
- Semua tool relevan dipanggil **paralel**, bukan coba-satu-satu — lebih cepat dan bisa jawab pertanyaan yang butuh gabungan sumber

## Struktur Project

```
├── ai-orchestration/
│   ├── orchestrator/
│   │   ├── orchestrator.py       # FastAPI: /analyze, /health, /history
│   │   ├── chat_cli.py           # Chatbot interaktif di CLI
│   │   ├── decision.py           # Tentukan jalur local vs router
│   │   ├── scope_guard.py        # Filter topik (via Local LLM)
│   │   ├── intent_router.py      # Deteksi tool relevan (keyword-based)
│   │   ├── context_gatherer.py   # Jalankan tool relevan secara paralel
│   │   ├── context_builder.py    # Client MCP (HTTP)
│   │   ├── local_client.py       # Client Ollama, dengan retry
│   │   ├── router_client.py      # Client 9Router, dengan retry
│   │   ├── guardrails.py         # Validasi jawaban akhir
│   │   ├── langfuse_client.py    # Wrapper Langfuse SDK v4
│   │   └── data_masking.py       # Dibangun, TIDAK aktif di alur manapun saat ini
│   └── recommendation/
│       ├── policy_rules.py       # Deteksi rule-based (SQL murni)
│       ├── text_to_sql.py        # Natural language -> SQL, read-only
│       ├── schema_info.py        # Baca skema DB otomatis dari INFORMATION_SCHEMA
│       └── generate_cli.py       # CLI: policy_rules -> narasi AI
│
├── integration-layer/
│   └── db_client.py              # Koneksi MySQL, connection pooling (DBUtils)
│
├── mcp-servers/
│   └── data-warehouse-server/
│       └── server.py             # MCP server (streamable-http), port 8200
│
├── rag/
│   ├── indexer.py                # PDF SOP -> chunk (paragraf+tabel) -> Chroma
│   ├── retriever.py               # Cari chunk relevan dari Chroma
│   └── source_docs/               # Taruh file PDF SOP di sini
│
├── dashboard/
│   └── backend/api/v1/internal/
│       └── metrics.py            # Endpoint metrik non-AI (query langsung ke DB)
│
├── docs/
│   ├── PRD.md                    # Product requirements + status + keterbatasan
│   └── architecture.md            # Keputusan arsitektur teknis
│
├── .env.example
├── .gitignore
├── docker-compose.yml             # Langfuse + Postgres
└── requirements.txt
```

> Folder `note/` dan `test/` mungkin ada di repo dari eksplorasi terpisah — isi dan statusnya belum terverifikasi bersama dalam dokumentasi ini. Cek langsung isinya sebelum mengandalkannya.

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Backend | FastAPI + Uvicorn |
| Database | MySQL (phpMyAdmin), data dummy |
| Vector DB | ChromaDB (persistent, folder `rag/vector_store/`) |
| Local LLM | Ollama — `phi4-mini` (CPU-only) |
| Embedding | `nomic-embed-text` (via Ollama) |
| LLM Router | 9Router (`localhost:20128`, OpenAI-compatible) |
| Protokol data | MCP (Model Context Protocol), transport `streamable-http` |
| Observability | Langfuse (Docker, port 3001) — SDK v4 |
| Parsing PDF | `pypdf` (teks) + `pdfplumber` (tabel) |
| DB driver | PyMySQL + `DBUtils.PooledDB` |
| HTTP client | `httpx` + `tenacity` (retry) |

## Instalasi & Setup

### Prasyarat
1. Python 3.14
2. Ollama (native di Windows)
3. MySQL/phpMyAdmin (port 3306)
4. 9Router jalan di port 20128
5. Docker (untuk Langfuse)

### Langkah

```bash
cp .env.example .env
```

Isi `.env` — **JANGAN pernah commit file `.env` ke git**:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=nama_database_anda
DB_READONLY_USER=dashboard_readonly
DB_READONLY_PASSWORD=

NINEROUTER_BASE_URL=http://localhost:20128/v1
NINEROUTER_API_KEY=
NINEROUTER_MODEL=free_tier

LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=http://localhost:3001
```

```bash
pip install -r requirements.txt

ollama pull phi4-mini
ollama pull nomic-embed-text
```

Index dokumen SOP (taruh PDF di `rag/source_docs/` dulu):
```bash
cd rag
python indexer.py
```

### Menjalankan service (urutan penting — MCP server duluan)

**Terminal 1 — MCP server:**
```bash
cd mcp-servers/data-warehouse-server
python server.py
```

**Terminal 2 — Langfuse (opsional, untuk monitoring):**
```bash
docker compose up -d langfuse-db langfuse
```

**Terminal 3 — Orchestrator:**
```bash
cd ai-orchestration/orchestrator
uvicorn orchestrator:app --reload --port 8100
```

## Cara Pakai

### Chatbot CLI
```bash
cd ai-orchestration/orchestrator
python chat_cli.py
```

Contoh pertanyaan:
- `berapa karyawan yang terlambat bulan ini?`
- `apa aturan lembur?`
- `apakah ada yang lembur melebihi ketentuan SOP?` (gabung SOP + data)

Command manual (debug 1 komponen):
```
!sensitif <pertanyaan>   -> paksa Local LLM saja
!sql <pertanyaan>         -> paksa SQL Tool saja
!sop <pertanyaan>         -> paksa RAG saja
```

### API

```bash
curl -X POST http://localhost:8100/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "berapa total task bulan ini?", "sensitive": false}'
```

Response:
```json
{
  "answer": "...",
  "path_used": "router:business_rules+mcp+rag+sql",
  "model_used": "9router"
}
```

**Health check:**
```bash
curl http://localhost:8100/health
```

**Riwayat (butuh Langfuse aktif dengan API key terisi):**
```bash
curl http://localhost:8100/history?limit=10
```

### AI Recommendation (rule-based)
```bash
cd ai-orchestration/recommendation
python generate_cli.py
```
Output: hasil deteksi SQL (teks polos) diikuti narasi ringkas dari AI berdasarkan angka itu.

## Skema Database

| Tabel | Kolom utama |
|---|---|
| `employees` | `id`, `name`, `division_id` |
| `divisions` | `id`, `department_id`, `name` |
| `departments` | `id`, `name` |
| `attendance` | `employee_id`, `work_date`, `clock_in`, `clock_out` |
| `daily_tasks` | `employee_id`, `work_date`, `total_tasks`, `total_hours` |
| `sop_settings` | `batas_jam_masuk`, `jam_kerja_normal_selesai` |

Saat ini pakai data dummy. Integration layer untuk menarik data dari aplikasi internal sungguhan **belum dibangun**.

## Keterbatasan & Risiko (jujur, per hari ke-5)

1. **`MAX_DISTANCE_THRESHOLD` di `retriever.py` belum dikalibrasi** (masih `999`, efektif tidak menyaring hasil RAG yang tidak relevan)
2. **Langfuse belum diverifikasi end-to-end** — `/history` belum dites berhasil membaca data asli
3. **Data masking (Presidio) dibangun tapi tidak aktif** — dihapus dari alur atas keputusan pemilik project; nama karyawan terkirim apa adanya ke 9Router untuk jalur non-sensitif
4. **9Router adalah dependency eksternal yang mekanismenya tidak sepenuhnya diketahui** — tidak dikonfirmasi provider apa yang ada di baliknya
5. **Tidak ada autentikasi** di endpoint `/analyze` — terbuka tanpa proteksi
6. **Belum ada frontend** — semua akses lewat CLI/curl
7. **Scope Guard menambah 1 panggilan LLM ekstra** di setiap request (latency bertambah)
8. **Belum ada automated test** (`pytest`)
9. **Konkurensi belum diuji dengan beban nyata** — estimasi batas ~5 user simultan masih teori
10. **`git init`/riwayat commit perlu diaudit** — pastikan tidak ada kredensial (`.env`) yang pernah ter-commit

## Troubleshooting

**"Cannot connect to Ollama"** → `ollama serve`

**"MySQL connection failed"** → cek `.env`, test manual `mysql -u root -p`

**"MCP server not responding"** → pastikan `python server.py` di `mcp-servers/data-warehouse-server/` sedang jalan di terminal terpisah

**Error di `chat_cli.py` yang tidak sesuai perilaku kode** → proses lama sering masih pakai versi kode sebelum diedit; restart total (bukan cuma tanya ulang)

**Reset index SOP:**
```bash
cd rag
rm -rf vector_store/
python indexer.py
```

## Dokumentasi Tambahan

- `docs/PRD.md` — requirement lengkap + status tiap fitur
- `docs/architecture.md` — keputusan arsitektur beserta alasannya

## License

Internal use only.