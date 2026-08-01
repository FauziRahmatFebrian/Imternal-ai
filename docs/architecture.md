# Catatan arsitektur & roadmap

## Perubahan penting (dicatat supaya tidak bingung baca kode lama)
- Router awalnya direncanakan pakai **LiteLLM**, sekarang diganti **9Router**
  (service milik Anda sendiri, OpenAI-compatible, di localhost:20128).
  `router_client.py` dan `generate_cli.py` sudah disesuaikan.
- `litellm_config.yaml` di `ai-orchestration/router-config/` sekarang
  **tidak lagi dipakai** -- dibiarkan ada sebagai arsip, boleh dihapus.
- MCP server sekarang pakai transport **HTTP** (`streamable-http`), bukan
  subprocess/stdio -- karena stdio tidak stabil dijalankan dari dalam
  uvicorn di Windows. MCP server harus dijalankan manual di terminal
  terpisah sebelum Orchestrator dijalankan.
- MCP server `get_monthly_task_counts` sekarang query ke **MySQL asli**
  (data dummy di phpMyAdmin), bukan data hardcode lagi.

## Ringkasan alur saat ini
1. Aplikasi internal -> integration layer -> data warehouse (MySQL, saat ini
   data dummy hasil generate).
2. AI Orchestrator: terima request -> ambil konteks dari MCP (data MySQL asli)
   -> decision.py pilih jalur:
   - **local_direct**: panggil Ollama langsung (`phi4-mini`), untuk data sensitif.
   - **router**: panggil lewat 9Router, untuk request umum.
3. Setiap request dicatat ke Langfuse (kalau service Langfuse jalan).
4. AI Recommendation (`ai-orchestration/recommendation/`): `policy_rules.py`
   mendeteksi kondisi (keterlambatan, lembur, penurunan task) murni lewat SQL
   dan aturan dari `sop_settings`, baru hasilnya dirangkai jadi narasi lewat
   9Router di `generate_cli.py` -- LLM tidak pernah menghitung sendiri.
5. RAG (`rag/`): khusus dokumen SOP (PDF), pakai Chroma + embedding
   `nomic-embed-text` lewat Ollama. Belum tersambung ke context_builder.py.

## Keputusan yang masih berlaku dari diskusi sebelumnya
- Data sensitif tidak boleh lewat jalur router/cloud tanpa masking (Presidio
  atau setara) -- ini jadi lebih relevan sekarang karena 9Router berpotensi
  mengarah ke provider cloud pihak ketiga.
- Metrik non-AI (chart biasa) tidak lewat AI Orchestrator sama sekali --
  query langsung ke data warehouse.
