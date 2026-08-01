# Dashboard (backend + frontend)

- `backend/` — API yang diakses frontend. Untuk metrik biasa (mis. jumlah submit task
  per bulan), backend query langsung ke data warehouse — TIDAK lewat AI.
  AI Orchestrator hanya dipanggil untuk permintaan yang memang butuh analisis/insight.
- `frontend/` — tampilan chart + panel insight AI untuk tim manajemen.

Status: skeleton, isi bertahap mengikuti roadmap Month 1-3.
