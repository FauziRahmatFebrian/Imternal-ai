# AI Orchestrator — skeleton awal

Orchestrator ini punya DUA jalur pemanggilan AI, sesuai yang Anda minta:

1. **Local direct** (`local_client.py`) — panggil Ollama langsung di localhost,
   tanpa lewat router. Dipakai untuk request yang ditandai sensitif, supaya
   TIDAK ADA kemungkinan data itu ikut ke cloud, bahkan secara tidak sengaja.
2. **Router** (`router_client.py`) — panggil lewat LiteLLM (`litellm` service
   di docker-compose). Ini jalur default untuk request umum. Sekarang router
   ini cuma mengarah ke model local juga (karena Cloud LLM belum diaktifkan),
   tapi strukturnya sudah siap kalau nanti model cloud ditambahkan di
   `litellm_config.yaml` — kode orchestrator TIDAK PERLU diubah saat itu terjadi.

`decision.py` yang menentukan request masuk jalur mana, berdasarkan flag
`sensitive` yang dikirim si pemanggil (nanti diisi otomatis oleh
`context_builder.py` saat itu dibangun — untuk sekarang masih manual).

## Cara jalan

Prasyarat: Ollama sudah jalan (`ollama serve`, biasanya otomatis jalan setelah
instalasi) dan model `phi4-mini` sudah di-pull.

```bash
pip install -r requirements.txt
uvicorn orchestrator:app --reload --port 8100
```

Test lewat jalur local direct:
```bash
curl -X POST http://localhost:8100/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Ringkas dalam 1 kalimat: apa itu dashboard monitoring", "sensitive": true}'
```

Test lewat jalur router (butuh service `litellm` di docker-compose sudah jalan):
```bash
curl -X POST http://localhost:8100/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Ringkas dalam 1 kalimat: apa itu dashboard monitoring", "sensitive": false}'
```

## Struktur file

```
orchestrator.py     # entrypoint FastAPI, endpoint /analyze
schemas.py           # bentuk request/response
decision.py          # pilih jalur: local_direct atau router
local_client.py      # panggil Ollama langsung (jalur sensitif)
router_client.py      # panggil lewat LiteLLM (jalur umum)
requirements.txt
```

Belum termasuk di skeleton ini (sesuai roadmap, dibangun belakangan):
`context_builder.py` (RAG+MCP), `guardrails.py`, `session_store.py`.
