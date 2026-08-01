# Dashboard AI Monitoring Internal

Dashboard monitoring operasional internal dengan kemampuan query natural language menggunakan AI. Sistem ini memungkinkan manajemen untuk bertanya tentang kehadiran, produktivitas, dan kepatuhan SOP dalam bahasa alami, dengan insight yang dihasilkan dari kombinasi rule-based detection dan AI.

**Status:** Day 5 Prototype — Fungsional via CLI, belum ada frontend

## Fitur Utama

- **Natural Language Query**: Tanya data operasional dalam bahasa Indonesia/Inggris
- **Dual-Path AI**: Sensitive data diproses local (Ollama), general queries via 9Router
- **Context-Aware**: Kombinasi data warehouse (MCP), dokumen SOP (RAG), dan business rules
- **Rule-Based Recommendations**: Deteksi keterlambatan, overtime, produktivitas berbasis SQL
- **Text-to-SQL**: Konversi pertanyaan natural language ke SQL query dengan safety validation
- **Scope Guard**: Filter otomatis pertanyaan di luar topik operasional
- **Health Monitoring**: Endpoint untuk cek status semua service dependencies

## Arsitektur

```
User Query → Scope Guard → Dual-Path Router:
  ├─ Local Path (sensitive=true)  → Ollama phi4-mini
  └─ Router Path (sensitive=false):
       ├─ Intent Detection (keyword-based)
       ├─ Context Gathering (parallel):
       │   ├─ MCP Server (data warehouse)
       │   ├─ RAG (SOP documents)
       │   ├─ Business Rules (SQL detection)
       │   └─ Text-to-SQL Tool
       ├─ Context Assembly
       └─ 9Router (LLM generation)
```

**Prinsip Desain:**
- AI **tidak menghitung angka** — semua metrik dari SQL, LLM hanya menarasikan
- Data sensitif **hanya lewat Local LLM** — 9Router tidak dipercaya untuk PII
- Fail-safe validation dengan guardrails
- Connection pooling & retry logic untuk fault tolerance

## Struktur Project

```
├── ai-orchestration/
│   ├── orchestrator/          # FastAPI service (port 8100)
│   │   ├── orchestrator.py    # Main API: /analyze, /health, /history
│   │   ├── decision.py        # Route sensitive vs general queries
│   │   ├── intent_router.py   # Keyword-based intent detection
│   │   ├── context_gatherer.py # Parallel context fetching
│   │   ├── guardrails.py      # Answer validation
│   │   ├── scope_guard.py     # Out-of-scope filter
│   │   └── chat_cli.py        # Interactive CLI untuk testing
│   └── recommendation/        # Rule-based AI recommendations
│       ├── policy_rules.py    # SQL-based detection rules
│       ├── text_to_sql.py     # Natural language → SQL
│       └── generate_cli.py    # SQL findings → narrative
│
├── integration-layer/         # Database connection layer
│   └── db_client.py          # MySQL connection pooling
│
├── mcp-servers/              # Model Context Protocol servers
│   └── data-warehouse-server/ # FastMCP HTTP server (port 8200)
│       └── server.py         # Tools: task counts, data freshness
│
├── rag/                      # RAG untuk dokumen SOP
│   ├── indexer.py           # PDF → ChromaDB embeddings
│   ├── retriever.py         # Similarity search
│   └── query_preprocessor.py # Synonym expansion (belum integrasi)
│
├── dashboard/               # Frontend & backend (skeleton)
│   └── backend/api/v1/internal/metrics.py
│
├── docs/                    # Dokumentasi
│   ├── prd.md              # PRD lengkap dengan limitasi
│   └── architecture.md      # Keputusan arsitektur
│
└── note/                    # Dokumentasi tambahan
    └── dokumentasi-orchestrator-sampai-security.md
```

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| **Backend** | FastAPI + Uvicorn |
| **Database** | MySQL (phpMyAdmin, dummy data) |
| **Vector DB** | ChromaDB (persistent, file-based) |
| **Local LLM** | Ollama (phi4-mini, CPU-only) |
| **Embeddings** | nomic-embed-text (via Ollama) |
| **LLM Router** | 9Router (localhost:20128) |
| **Protocol** | MCP v1.9.0 (Model Context Protocol) |
| **Observability** | Langfuse (Docker, port 3001) |
| **PDF Parsing** | pypdf + pdfplumber |
| **DB Driver** | PyMySQL + DBUtils (pooling) |
| **HTTP Client** | httpx + tenacity (retry) |

## Instalasi & Setup

### Prerequisites

1. **Python 3.14**
2. **Ollama** (native Windows installation)
3. **MySQL/phpMyAdmin** (port 3306)
4. **9Router** (running on port 20128)
5. **Docker** (untuk Langfuse, opsional)

### Langkah Instalasi

1. **Clone & Setup Environment**
```bash
cd "C:\Goodeva\project\Dashboard Internal"
cp .env.example .env
```

2. **Edit `.env`** dengan konfigurasi Anda:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database
DB_READONLY_USER=readonly_user
DB_READONLY_PASSWORD=readonly_password

NINEROUTER_BASE_URL=http://localhost:20128/v1
NINEROUTER_API_KEY=your_api_key
NINEROUTER_MODEL=free_tier

LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3001
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup Ollama Models**
```bash
ollama pull phi4-mini
ollama pull nomic-embed-text
```

5. **Index SOP Documents** (jika ada PDF di folder tertentu)
```bash
cd rag
python indexer.py
```

6. **Start Services**

Terminal 1 - Langfuse (opsional):
```bash
docker compose up -d
```

Terminal 2 - MCP Server:
```bash
cd mcp-servers/data-warehouse-server
python server.py
```

Terminal 3 - AI Orchestrator:
```bash
cd ai-orchestration/orchestrator
uvicorn orchestrator:app --reload --port 8100
```

## Cara Menggunakan

### Via CLI (Interactive Chat)

```bash
cd ai-orchestration/orchestrator
python chat_cli.py
```

Contoh pertanyaan:
- "Berapa karyawan yang terlambat bulan ini?"
- "Siapa yang paling produktif minggu lalu?"
- "Bagaimana SOP untuk handling komplain pelanggan?"
- "Show me overtime trends untuk divisi IT"

### Via API (curl/Postman)

**Endpoint:** `POST http://localhost:8100/analyze`

```bash
curl -X POST http://localhost:8100/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Berapa total task yang diselesaikan bulan ini?",
    "sensitive": false
  }'
```

Response:
```json
{
  "answer": "Berdasarkan data dari data warehouse, total task yang diselesaikan bulan ini adalah 1,234 task...",
  "path_used": "router",
  "model_used": "free_tier",
  "langfuse_url": "http://localhost:3001/trace/..."
}
```

**Health Check:**
```bash
curl http://localhost:8100/health
```

**Query History:**
```bash
curl http://localhost:8100/history?limit=10
```

### AI Recommendation (Rule-Based)

Generate recommendations berdasarkan SQL detection:

```bash
cd ai-orchestration/recommendation
python generate_cli.py
```

Output contoh:
```
=== REKOMENDASI AI MONITORING KARYAWAN ===

📊 RINGKASAN SINGKAT
Dari 150 karyawan yang dipantau:
- 12 karyawan terlambat ≥3x bulan ini (perlu teguran)
- 8 karyawan overtime berlebihan >20 jam/bulan (risiko burnout)
- 5 karyawan produktivitas rendah <5 task/minggu

🚨 TEMUAN PRIORITAS TINGGI
1. John Doe (Marketing) - Terlambat 5x, produktivitas turun 40%
   Rekomendasi: One-on-one meeting, evaluasi workload
...
```

### Text-to-SQL Testing

```bash
cd ai-orchestration/recommendation
python text_to_sql.py
```

Masukkan pertanyaan natural language, sistem akan generate SQL query dengan safety validation.

## Database Schema

Tabel utama yang digunakan:

- **employees**: `id`, `name`, `division_id`
- **divisions**: `id`, `name`
- **attendance**: `employee_id`, `tanggal`, `clock_in`, `clock_out`
- **tasks**: `id`, `employee_id`, `submitted_at`, ...
- **daily_tasks**: `employee_id`, `work_date`, `total_tasks`, `total_hours`
- **sop_settings**: `batas_jam_masuk`, `jam_kerja_normal_selesai`

**Note:** Saat ini menggunakan dummy data. Integration layer untuk pull data dari aplikasi internal belum dibangun.

## Keterbatasan & Risiko

### Known Issues

1. **RAG threshold belum dikalibrasi** — `MAX_DISTANCE_THRESHOLD = 999` tidak filter hasil buruk
2. **Langfuse belum diverifikasi end-to-end** — Keys belum dikonfigurasi, `/history` belum ditest
3. **Data masking disabled** — Presidio code ada tapi dimatikan per keputusan owner, nama dikirim ke 9Router as-is
4. **9Router adalah black box** — Tidak tahu apakah forward ke cloud provider yang log data
5. **Tidak ada autentikasi** — Endpoint `/analyze` terbuka tanpa auth
6. **Tidak ada frontend** — Semua akses via CLI/curl only
7. **Scope guard menambah latency** — Setiap request di-prefilter dulu oleh LLM
8. **Tidak ada automated tests** — Semua validasi manual
9. **Concurrency belum ditest** — Klaim ~5 user concurrent belum divalidasi
10. **Belum ada git version control** — `git init` belum dilakukan

### Belum Dibangun

- Dashboard web UI (frontend)
- Real integration layer (ETL dari aplikasi internal)
- RBAC & audit logging
- API authentication & authorization
- Automated testing (pytest)
- Load testing
- HTTPS/TLS
- Secrets rotation

### Security Posture

**Sudah Ada:**
- Read-only DB user untuk text-to-SQL
- SQL injection prevention (whitelist SELECT, forbidden keywords)
- Retry dengan exponential backoff
- Connection pooling
- Answer validation

**Belum Ada:**
- API authentication
- Data masking (code ready tapi disabled)
- HTTPS/TLS
- Audit logging
- Rate limiting

## Hardware Requirements

System ini didesain untuk jalan di **laptop standar**:
- **CPU**: Intel HD 520 (atau equivalent)
- **RAM**: 16GB minimum
- **GPU**: Tidak diperlukan (CPU-only inference)
- **Storage**: ~5GB untuk models + vector DB

**Note:** phi4-mini dipilih karena bisa jalan di CPU tanpa GPU. Untuk performa lebih baik, gunakan GPU dan model lebih besar (phi4, llama3, dll).

## Dokumentasi Tambahan

Untuk detail lengkap, lihat:
- **PRD**: `docs/prd.md` — Product Requirements Document dengan roadmap
- **Architecture**: `docs/architecture.md` — Keputusan arsitektur & changelog
- **Technical Deep-Dive**: `note/dokumentasi-orchestrator-sampai-security.md` — Dokumentasi teknis 404 baris

## Troubleshooting

### Error: "Cannot connect to Ollama"
```bash
ollama serve
```

### Error: "MySQL connection failed"
Cek `.env` dan pastikan MySQL running:
```bash
mysql -u root -p
```

### Error: "MCP server not responding"
Restart MCP server:
```bash
cd mcp-servers/data-warehouse-server
python server.py
```

### Error: "9Router connection refused"
Pastikan 9Router running di port 20128

### ChromaDB Error
Hapus dan rebuild vector DB:
```bash
cd rag
rm -rf chroma_db/
python indexer.py
```

## Roadmap

| Fase | Status | Fokus |
|------|--------|-------|
| **Month 1** | ✅ Done | Integration layer, Local LLM, MCP dasar, monitoring dasar |
| **Month 2** | ✅ Done | RAG, LLM Router, AI Orchestrator, Chatbot CLI |
| **Month 3** | 🚧 In Progress | AI Recommendation, Dashboard UI, Security matang |

## Contributing

Project ini masih early-stage prototype. Belum ada git workflow atau contribution guidelines.

## License

Internal use only — Goodeva

## Contact

Untuk pertanyaan atau issue, hubungi tim development internal.
