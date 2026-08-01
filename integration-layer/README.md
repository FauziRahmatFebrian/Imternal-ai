# Integration layer

Konektor untuk menarik data dari tiap aplikasi internal via API/DB yang sudah tersedia.
Ini fondasi Month 1 — harus siap sebelum RAG dan AI Orchestrator dibangun.

## Rencana struktur (isi nanti)
- `connectors/` — satu file per aplikasi sumber data (mis. `task_app_connector.py`)
- `scheduler.py` — jadwal tarik data berkala (cron/queue)
- `schema/` — definisi skema tabel di data warehouse tujuan

## Prinsip
- Jangan panggil aplikasi sumber langsung dari dashboard frontend/backend —
  selalu lewat data warehouse yang diisi oleh layer ini.
- Catat setiap job tarik data (waktu, jumlah row, status) untuk kebutuhan
  Monitoring & Observability nantinya.
