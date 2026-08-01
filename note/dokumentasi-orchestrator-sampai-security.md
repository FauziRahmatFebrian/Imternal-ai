# Dokumentasi teknis — AI Orchestrator sampai Security & Governance

Lanjutan dari dokumentasi Local LLM sebelumnya. Urutan di dokumen ini mengikuti
urutan dependency yang sudah disepakati (bukan urutan asli di matrix), jadi
sebagian ditandai kapan sebaiknya dibangun.

---

## 1. AI Orchestrator

### Fungsi
Menerima permintaan dari dashboard backend ("analisis performa bulan ini"),
mengumpulkan konteks (lewat RAG/MCP), memutuskan langkah apa yang perlu diambil,
memanggil LLM Router, lalu mengembalikan hasil yang sudah diformat untuk dashboard.

### Struktur yang disarankan

```
ai-orchestration/
  orchestrator/
    orchestrator.py       # entrypoint, terima request dari dashboard backend
    context_builder.py    # panggil RAG + MCP untuk kumpulkan konteks
    guardrails.py         # validasi input/output sebelum & sesudah panggil LLM
    client.py             # client ke LLM Router (LiteLLM)
    session_store.py      # simpan riwayat percakapan/analisis (kalau perlu multi-turn)
```

### Rekomendasi tools

| Kebutuhan | Rekomendasi | Alasan |
|---|---|---|
| Orchestrator ringan, alur linear (kumpulkan konteks → panggil LLM → format hasil) | **Custom service pakai FastAPI**, tanpa framework agent besar | Kebutuhan Anda saat ini (analisis bulanan, insight dashboard) belum tentu butuh multi-agent. Framework besar menambah kompleksitas ops yang tidak sebanding manfaatnya di awal. |
| Orchestrator dengan alur bercabang/multi-step yang kompleks (butuh "pikir dulu, cek data, pikir lagi") | **LangGraph** atau **Haystack** | Keduanya open-source, mendukung alur bercabang dan sudah terintegrasi baik dengan RAG. |
| Kalau nanti benar-benar butuh banyak agent yang saling berkomunikasi | **CrewAI** atau **AutoGen** | Tapi ini eskalasi kompleksitas — jangan mulai dari sini kalau kebutuhan Anda masih "satu alur analisis per permintaan". |

**Rekomendasi saya untuk Month 2 (awal):** mulai dari custom FastAPI service dulu. Alasannya: kebutuhan AI Anda sendiri masih "exploratory" (sesuai yang Anda konfirmasi sebelumnya) — memilih framework orchestration yang berat sebelum tahu pola pemakaian sebenarnya berisiko over-engineering. Naik ke LangGraph/Haystack kalau pola kebutuhannya sudah lebih jelas dan memang butuh percabangan logika.

[Medium confidence — pemetaan tool ke use case ini berdasarkan karakteristik umum masing-masing framework yang saya tahu, bukan benchmark langsung untuk kasus Anda. Framework agent juga rilis versi baru sering; cek dokumentasi resmi masing-masing sebelum commit.]

---

## 2. LLM Router

### Fungsi
Menentukan permintaan AI diproses oleh model mana — Local LLM (Ollama) atau Cloud LLM
(OpenRouter) — berdasarkan aturan yang Anda tentukan, bukan hardcode di setiap tempat
yang memanggil LLM. Router ini juga jadi titik tunggal untuk cost tracking, fallback
kalau satu model gagal, dan rate limiting.

### Struktur yang disarankan

```
ai-orchestration/router-config/
  litellm_config.yaml     # daftar model + parameter koneksinya
  routing_policy.md        # dokumentasi aturan kapan pakai model mana (lihat di bawah)
```

### Rekomendasi tools

| Kebutuhan | Rekomendasi | Alasan |
|---|---|---|
| Router utama | **LiteLLM** | Satu interface untuk banyak provider, sudah punya cost tracking dan fallback bawaan, kompatibel format OpenAI sehingga mudah diintegrasikan ke orchestrator. |
| Kalau nanti butuh strategi routing berbasis skor/evaluasi otomatis (bukan aturan manual) | **RouteLLM** | Framework riset untuk cost-aware routing, lebih cocok dieksplorasi setelah Anda punya cukup data pemakaian nyata untuk melatih/mengevaluasi strategi routing-nya. |

**Rekomendasi saya: mulai dengan aturan routing manual dan sederhana dulu**, bukan otomatis berbasis model. Contoh aturan yang masuk akal untuk Month 2:

1. Default semua request ke **Local LLM**.
2. Alihkan ke **Cloud LLM** hanya kalau: (a) task ditandai butuh reasoning kompleks oleh orchestrator, DAN (b) data masking (lihat bagian 10.3) sudah dijalankan pada konteks yang dikirim.
3. **Aturan keras yang tidak boleh dilanggar oleh logika apapun di atas:** kalau konteks mengandung data personal karyawan yang belum di-mask, request TIDAK BOLEH ke Cloud LLM, apapun alasannya — fallback ke Local LLM meskipun hasilnya mungkin kurang optimal.

Aturan nomor 3 sengaja saya tulis sebagai hard rule, bukan preferensi — ini titik paling berisiko kalau logika routing di-override oleh alasan lain (mis. "supaya jawaban lebih bagus").

[Medium confidence pada perbandingan tool — berdasarkan pengetahuan umum saya, bukan pengujian langsung. LiteLLM sendiri sudah saya verifikasi repo-nya secara langsung sebelumnya, jadi bagian itu high confidence.]

---

## 3. RAG

### Struktur yang disarankan

```
rag/
  indexer.py           # proses data dari data warehouse -> embedding
  retriever.py          # dipanggil oleh context_builder.py
  chunking_config.py    # aturan pemotongan dokumen/data jadi potongan kecil
  vector_store/         # konfigurasi vector database
```

### Rekomendasi tools

- **Framework RAG:** LlamaIndex (fokus RAG) atau LangChain (lebih luas, RAG + orchestration).
- **Vector database:** ada beberapa opsi populer (Qdrant, pgvector di atas Postgres yang mungkin sudah Anda pakai, Chroma untuk skala kecil). Kalau tim Anda sudah pakai Postgres, **pgvector** paling praktis karena tidak menambah service baru.

[Medium confidence, perlu verifikasi — ruang vector database berubah cepat dan pilihan terbaik tergantung volume data Anda yang belum saya tahu. Jangan pilih vector DB sebelum tahu perkiraan jumlah dokumen/data yang akan di-index.]

**Catatan dependency (pengingat dari diskusi sebelumnya):** jangan mulai bagian ini sebelum `integration-layer` sudah menghasilkan data yang konsisten di data warehouse.

---

## 4. MCP

### Struktur yang disarankan

```
mcp-servers/
  data-warehouse-server/   # akses terkontrol ke data warehouse
  internal-docs-server/    # akses ke dokumen internal (kalau ada)
```

### Rekomendasi
Gunakan SDK resmi Model Context Protocol untuk membuat server sendiri per domain
data, daripada AI Orchestrator memanggil setiap sumber data dengan cara berbeda-beda.
Cek repo referensi resmi MCP servers untuk contoh implementasi sebelum menulis dari nol.

[Medium confidence pada detail SDK terbaru — cek dokumentasi resmi modelcontextprotocol.io untuk versi API terkini sebelum implementasi.]

---

## 5. Cloud LLM (OpenRouter)

### Fungsi
Sumber tambahan kapasitas untuk request yang butuh reasoning lebih kuat daripada
yang bisa diberikan Local LLM di hardware Anda saat ini. OpenRouter sendiri bukan
LLM tunggal, tapi agregator yang meneruskan request ke banyak provider model
(OpenAI, Anthropic, dll.) lewat satu API — jadi kalau Anda ganti model, tidak perlu
ganti banyak kode.

### Struktur yang disarankan

Tidak perlu folder baru — cukup tambahan blok di file yang sudah ada:

```
ai-orchestration/router-config/
  litellm_config.yaml   # tambahkan blok model baru untuk OpenRouter di sini
```

Contoh tambahan konfigurasi (mengaktifkan blok yang di Month 1 masih dikomentari):

```yaml
model_list:
  - model_name: local-default
    litellm_params:
      model: ollama/REPLACE_WITH_MODEL_NAME
      api_base: http://ollama:11434

  - model_name: cloud-fallback
    litellm_params:
      model: openrouter/REPLACE_WITH_MODEL_NAME
      api_key: os.environ/OPENROUTER_API_KEY
      max_budget: 50            # batas biaya, sesuaikan dengan anggaran Anda
      budget_duration: 30d
```

### Syarat sebelum diaktifkan (bukan sekadar rekomendasi, ini prasyarat)

1. **Data masking (bagian 10.3) sudah berjalan** di `context_builder.py` — bukan opsional.
2. **Batas biaya (`max_budget`) sudah diset** di config LiteLLM, supaya tidak ada
   kejutan tagihan kalau ada bug yang memicu request berulang.
3. **Aturan routing hard rule** (lihat bagian 2, poin 3) sudah diimplementasikan di
   logika routing, bukan cuma didokumentasikan.

Kalau salah satu dari tiga hal ini belum siap, blok `cloud-fallback` di atas
sebaiknya tetap dikomentari — meskipun secara teknis mudah diaktifkan dalam hitungan
detik, konsekuensinya (data internal keluar tanpa pagar) tidak sepadan dengan
kecepatan aktivasinya.

[High confidence pada mekanisme teknis (format config LiteLLM untuk OpenRouter) karena ini konsisten dengan dokumentasi LiteLLM yang sudah saya verifikasi. Nilai `max_budget` di atas hanya contoh angka — sesuaikan dengan anggaran nyata Anda, bukan diikuti apa adanya.]

---

## 6. Chatbot

### Struktur
Chatbot di sini sebaiknya **bukan aplikasi terpisah**, tapi panel di dalam dashboard
yang sama, memanggil AI Orchestrator — supaya semua log, guardrails, dan governance
yang sudah dibangun untuk orchestrator otomatis berlaku juga ke chatbot.

### Rekomendasi tools
Kalau ingin cepat: **Open WebUI** (chat interface open-source untuk model lokal/API)
bisa dipasang cepat untuk testing internal. Tapi untuk versi produksi yang terintegrasi
ke dashboard, lebih baik bangun panel chat sendiri di frontend dashboard supaya
konsisten dengan desain dan otentikasi yang sudah ada.

---

## 7. AI Recommendation

### Fungsi (berdasarkan definisi yang Anda berikan)
Panel rekomendasi yang muncul di **tampilan awal/landing page** dashboard, berisi
insight yang dihasilkan AI untuk tim manajemen — dilihat pertama kali saat dashboard
dibuka, bukan sesuatu yang harus ditanya lewat chatbot.

Karena ini landing page, ada satu keputusan desain yang menentukan semuanya:
**apakah rekomendasi dihasilkan real-time tiap kali dashboard dibuka, atau
dihasilkan terjadwal dan disimpan (cache)?**

| Pendekatan | Kelebihan | Kekurangan |
|---|---|---|
| Generate real-time tiap dashboard dibuka | Selalu paling baru | Setiap orang buka dashboard = 1 request ke LLM. Kalau 10 orang buka bersamaan di pagi hari, itu 10 request bersamaan — masuk ke masalah concurrency Ollama yang sudah dibahas di dokumentasi Local LLM sebelumnya. Juga menambah waktu loading landing page. |
| Generate terjadwal (mis. tiap pagi jam 6), simpan hasilnya, dashboard tinggal tampilkan | Landing page tetap cepat dibuka, beban ke LLM terkontrol dan bisa diprediksi | Rekomendasi tidak "detik ini juga", tapi untuk insight bulanan/mingguan biasanya tidak masalah |

**Rekomendasi saya: generate terjadwal, bukan real-time.** Sifat data yang dijadikan
dasar rekomendasi (mis. "jumlah submit task per bulan") memang tidak berubah tiap detik,
jadi tidak ada alasan kuat untuk generate ulang tiap kali halaman dibuka. Ini juga
konsisten dengan keputusan menghindari beban concurrency berlebih pada Local LLM.

### Struktur yang disarankan

```
ai-orchestration/
  recommendation/
    generator.py          # dijalankan terjadwal, hasilkan rekomendasi
    prompt_templates.py    # template prompt untuk konsistensi format output
    trigger_rules.py        # aturan sederhana kapan sesuatu layak jadi "rekomendasi"
dashboard/backend/
  api/v1/internal/
    recommendations.py      # endpoint yang tinggal serve hasil tersimpan ke frontend
```

`generator.py` dijadwalkan lewat scheduler yang sama dengan `integration-layer`
(lihat bagian 8) — masuk akal dijalankan setelah data harian/bulanan selesai ditarik.

### Pendekatan yang disarankan: hybrid, bukan murni "tanya LLM"

Ini bagian paling penting untuk diperhatikan. Kalau AI Orchestrator hanya diberi
prompt "buatkan rekomendasi untuk tim manajemen" tanpa batasan, risikonya LLM bisa
mengarang angka atau kesimpulan yang terdengar meyakinkan tapi tidak akurat —
ini fatal untuk konten yang muncul di landing page dan dibaca manajemen sebagai fakta.

Pendekatan yang lebih aman:

1. **`trigger_rules.py` (rule-based, bukan AI) yang mendeteksi kondisi layak disorot** —
   contoh: "submit task tim X turun lebih dari 20% dibanding bulan lalu", "ada N task
   overdue lebih dari 2 minggu". Ini logika sederhana berbasis angka dari data warehouse,
   bukan AI.
2. **LLM hanya bertugas menjelaskan/merangkai narasi** dari kondisi yang sudah terdeteksi
   di langkah 1 — bukan menentukan sendiri apa yang penting. Semua angka yang disebutkan
   LLM di narasinya harus diambil dari data yang diberikan lewat RAG/context, bukan dari
   "pengetahuan umum" model.
3. Kalau tidak ada kondisi yang terdeteksi di langkah 1 pada periode tertentu, panel
   rekomendasi menampilkan pesan netral ("tidak ada perubahan signifikan bulan ini"),
   **bukan memaksa LLM mengarang sesuatu supaya panelnya tidak kosong.**

Pendekatan ini membuat rekomendasi bisa diverifikasi — setiap klaim di narasinya bisa
ditelusuri balik ke angka yang memicunya, bukan sekadar "kata AI".

[High confidence pada risiko halusinasi angka pada pendekatan "murni tanya LLM" — ini pola kegagalan yang sudah dikenal luas untuk sistem yang menampilkan output LLM sebagai fakta ke pengguna non-teknis. Confidence menurun ke medium untuk detail ambang batas di `trigger_rules.py` (mis. angka "20%") karena itu perlu disesuaikan dengan konteks bisnis Anda, bukan angka baku.]

---

## 8. Internal System Integration

### Fungsi
Menarik data dari tiap aplikasi internal (task management, CRM, dsb.) secara berkala
lewat API/DB yang sudah tersedia, lalu menyimpannya dalam bentuk konsisten di data
warehouse. Ini fondasi paling awal — baik dashboard non-AI (chart biasa) maupun RAG
sama-sama bergantung pada layer ini.

### Struktur yang disarankan

```
integration-layer/
  connectors/
    task_app_connector.py     # satu file per aplikasi sumber data
    crm_connector.py
    ...
  scheduler.py                 # jadwal tarik data berkala
  schema/
    tasks.sql                  # definisi tabel tujuan di data warehouse
    ...
  sync_log.py                  # catat setiap job: waktu jalan, jumlah row, status
```

### Rekomendasi tools

| Kebutuhan | Rekomendasi | Alasan |
|---|---|---|
| Penjadwalan job tarik data, skala kecil-menengah | **APScheduler** (Python) atau cron biasa | Sederhana, tidak menambah service baru — cukup untuk jumlah aplikasi sumber yang masih terbatas. |
| Kalau jumlah pipeline data bertambah banyak dan butuh monitoring dependency antar-job | **Airflow**, **Dagster**, atau **Prefect** | Baru relevan kalau integration-layer sudah punya cukup banyak connector sehingga sulit dikelola manual — jangan mulai dari sini kalau baru 2-3 sumber data. |
| Kalau aplikasi sumber Anda termasuk SaaS umum (bukan aplikasi custom internal) | **Airbyte** | Sudah punya banyak connector siap pakai untuk SaaS populer, bisa menghemat waktu dibanding menulis connector sendiri — tapi perlu dicek dulu apakah aplikasi internal Anda termasuk yang didukung. |

**Rekomendasi saya untuk Month 1: mulai dari custom connector + APScheduler.** Alasan:
Anda sudah konfirmasi datanya berasal dari API/database yang sudah tersedia, tapi
sifatnya kemungkinan besar aplikasi internal custom (bukan SaaS umum seperti Salesforce),
sehingga Airbyte belum tentu punya connector siap pakai. Menulis connector sendiri
yang sederhana lebih cepat daripada mempelajari dan menyesuaikan framework ETL besar
di awal.

### Prinsip desain yang perlu dipegang

- **Jangan** panggil aplikasi sumber langsung dari dashboard frontend/backend — selalu
  lewat data warehouse yang diisi layer ini, supaya aplikasi sumber tidak kelebihan beban
  tiap kali dashboard dibuka.
- **Incremental sync**, bukan tarik ulang semua data tiap kali — tandai data yang sudah
  ditarik (mis. berdasarkan timestamp `updated_at`) supaya proses berjalan cepat dan
  tidak membebani aplikasi sumber.
- **Idempotent** — kalau job gagal di tengah jalan dan dijalankan ulang, hasilnya tidak
  boleh menghasilkan data duplikat.
- Catat setiap job (`sync_log.py`) karena ini input penting untuk Monitoring &
  Observability nantinya — kalau satu connector diam-diam gagal selama seminggu,
  Anda perlu tahu dari log ini, bukan dari laporan manual tim yang datanya "terasa aneh".

[High confidence pada prinsip desain (incremental sync, idempotent, logging) — ini praktik umum ETL/data engineering yang sudah stabil, bukan sesuatu yang berubah cepat. Confidence menurun ke medium untuk pilihan tool spesifik (Airbyte/Airflow/dsb.) karena landscape tool ini terus berubah — cek versi dan status maintenance masing-masing sebelum memilih.]

---

## 9. API for SaaS

### Struktur
```
dashboard/backend/
  api/
    v1/
      internal/    # dipakai frontend dashboard sendiri
      external/    # kalau memang perlu diakses sistem SaaS lain
```

### Rekomendasi
FastAPI (Python) untuk backend API — sudah konsisten dengan tools lain di stack ini
(LiteLLM, kemungkinan integration-layer). Tambahkan API gateway (mis. Traefik) di
depan kalau nanti perlu rate limiting dan TLS terpusat.

---

## 10. Security & Governance (dengan enkripsi)

Ini bagian yang saya sarankan **dipindah ke Month 1**, bukan Month 3 seperti matrix
awal — alasannya sudah dijelaskan di dokumen sebelumnya (Cloud LLM aktif Month 2,
jadi pagar keamanan harus sudah ada sebelum itu).

### 10.1 Enkripsi data in transit (data yang sedang dikirim antar service)

- Semua komunikasi antar service (dashboard ↔ orchestrator ↔ router ↔ LLM) sebaiknya
  lewat **HTTPS/TLS**, termasuk di jaringan internal — jangan asumsikan "internal jadi
  aman tanpa enkripsi".
- Cara praktis: pasang reverse proxy (**Traefik** atau **Caddy**) di depan semua service
  di docker-compose Anda. Keduanya bisa otomatis urus sertifikat TLS, termasuk untuk
  domain internal/self-signed cert saat masih di localhost.
- Untuk request ke Cloud LLM (OpenRouter), TLS sudah otomatis ditangani karena itu
  API eksternal berbasis HTTPS — tapi pastikan library yang dipakai tidak menonaktifkan
  verifikasi sertifikat (jangan set `verify=False` di client HTTP manapun).

### 10.2 Enkripsi data at rest (data yang tersimpan)

- **Data warehouse & vector store:** aktifkan enkripsi disk di level infrastruktur
  (mis. LUKS di Linux, atau opsi encryption-at-rest bawaan kalau nanti pakai layanan
  cloud database). Postgres sendiri tidak otomatis mengenkripsi data di file-nya
  kecuali disk-nya dienkripsi atau pakai ekstensi tambahan.
- **Log & trace AI** (dari Langfuse) kemungkinan berisi isi percakapan/analisis yang
  sensitif — pastikan volume database Langfuse juga ada di disk yang terenkripsi.
- **Backup:** kalau ada proses backup database, pastikan file backup juga terenkripsi,
  bukan cuma database live-nya.

### 10.3 Data masking sebelum ke Cloud LLM

Ini titik paling kritis karena di sinilah data internal berpotensi "keluar rumah".

- Gunakan library deteksi & masking PII sebelum request dikirim ke OpenRouter, contoh:
  **Microsoft Presidio** (open-source, mendeteksi nama, email, nomor identitas, dll.,
  dan bisa mengganti dengan placeholder sebelum teks dikirim keluar).
- Terapkan aturan: kalau AI Orchestrator mendeteksi request butuh Cloud LLM dan
  konteksnya mengandung data sensitif (mis. nama karyawan, data personal), masking
  dijalankan dulu di `context_builder.py` sebelum diteruskan ke `client.py`.
- Alternatif yang lebih aman kalau datanya sangat sensitif: **jangan pakai Cloud LLM
  sama sekali untuk kategori data itu** — batasi Cloud LLM hanya untuk pertanyaan
  yang memang tidak butuh data personal karyawan.

[Medium confidence pada Presidio — saya cukup yakin ini tool yang tepat berdasarkan pengetahuan saya (ini proyek Microsoft yang cukup mapan), tapi saya tidak mengecek versi/status terbarunya hari ini. Verifikasi ulang di repo resminya sebelum implementasi.]

### 10.4 Secrets & key management

- **Jangan** simpan API key (OpenRouter, dsb.) langsung di file yang masuk git —
  `.env` sudah masuk `.gitignore` di skeleton sebelumnya, pertahankan itu.
- Untuk produksi, pertimbangkan secret manager (mis. **HashiCorp Vault**, atau kalau
  masih skala kecil, Docker secrets sudah cukup) daripada environment variable polos
  di server.
- Rotasi key secara berkala, terutama untuk key yang punya biaya per-request (Cloud LLM).

### 10.5 Access control & audit log

- Dashboard perlu **RBAC** (role-based access control) — tidak semua orang di tim
  manajemen perlu akses ke insight AI yang sama; sesuaikan dengan struktur organisasi.
- Setiap request ke AI (siapa yang tanya, kapan, data apa yang diakses) sebaiknya
  tercatat sebagai audit log — ini bisa memanfaatkan Langfuse yang sudah ada di stack
  untuk sisi AI, ditambah log akses biasa di level dashboard backend untuk sisi non-AI.

---

## 11. Monitoring & Observability (rekap singkat)

Sudah dibahas — **Langfuse** untuk sisi AI (tracing, cost, latency per request).
Untuk sisi infrastruktur umum (uptime service, resource server), itu di luar cakupan
Langfuse — kalau dibutuhkan, itu domain terpisah (mis. Prometheus + Grafana) yang
perlu didiskusikan sebagai kebutuhan sendiri, bukan digabung otomatis ke sini.

---

## Ringkasan hal yang masih perlu diverifikasi sebelum eksekusi

- Volume data aktual (untuk pilih vector database yang tepat di RAG).
- Definisi konkret "AI Recommendation" dari sisi kebutuhan bisnis.
- Ketersediaan infrastruktur untuk enkripsi disk (tanya tim infra).
- Versi terbaru semua tool yang disebut — ruang ini berubah cepat, jangan asumsikan
  nama/versi di dokumen ini masih yang paling baru saat Anda benar-benar eksekusi.
