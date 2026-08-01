# RAG — dokumen SOP

Vector DB yang dipakai: **Chroma**, mode "persistent" (data tersimpan di folder
`vector_store/`, tidak perlu service Docker terpisah). Embedding dibuat lewat
Ollama, model `nomic-embed-text` (~274MB, jauh lebih ringan dari phi4-mini
karena cuma untuk embedding, bukan chat).

## Cakupan
Untuk sekarang khusus dokumen SOP (teks bebas) — **bukan** untuk tabel
`kehadiran`/`tasks` di MySQL. Data tabel tetap lewat MCP + SQL biasa
(lihat mcp-servers/data-warehouse-server), sesuai prinsip yang sudah disepakati:
data terstruktur pakai query, data teks bebas pakai RAG.

## Cara pakai

1. Taruh file SOP (PDF) di `source_docs/`, misal `source_docs/sop_kehadiran_lembur.pdf`
2. Pastikan model embedding sudah di-pull:
   ```bash
   ollama pull nomic-embed-text
   ```
3. Jalankan indexer (sekali di awal, atau tiap kali SOP berubah):
   ```bash
   pip install -r requirements.txt
   python indexer.py
   ```
4. Test retrieval:
   ```bash
   python retriever.py "apa aturan lembur di SOP?"
   ```

## Struktur

```
rag/
  source_docs/         # taruh file PDF SOP di sini
  vector_store/          # otomatis terisi setelah indexer.py dijalankan, JANGAN commit ke git
  indexer.py             # baca PDF -> potong jadi chunk -> embed -> simpan ke Chroma
  retriever.py            # ambil chunk paling relevan untuk suatu pertanyaan
```
