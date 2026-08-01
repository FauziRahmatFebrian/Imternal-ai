# MCP server — data warehouse (skeleton)

Server MCP pertama untuk project ini. Tujuannya: memberi AI Orchestrator cara
terstandar mengambil data dari data warehouse, tanpa orchestrator perlu tahu
detail query SQL-nya.

## Status jujur di skeleton ini
`integration-layer` belum jalan, jadi data warehouse asli belum ada.
Tool-tool di `server.py` untuk sekarang mengembalikan **data dummy**, cukup
untuk membuktikan alur (Orchestrator -> MCP -> jawaban terstruktur) sudah benar.
Ganti fungsi dummy dengan query SQL asli begitu integration-layer + data
warehouse-nya siap — struktur tool-nya (nama, parameter) tidak perlu berubah.

## Tools yang tersedia

- `get_monthly_task_counts` — jumlah submit task per bulan (contoh awal dari
  diskusi kita). Dummy dulu, nanti diganti query SQL asli.
- `get_data_freshness` — kapan data terakhir berhasil ditarik integration-layer.
  Ini penting untuk transparansi: kalau data sudah basi (mis. gagal sync 3
  hari), AI Orchestrator/dashboard sebaiknya tahu itu, bukan diam-diam
  menganalisis data lama seolah-olah baru.

## Cara jalan

```bash
pip install -r requirements.txt
python server.py
```

Untuk tes cepat pakai MCP Inspector (bawaan SDK):
```bash
mcp dev server.py
```
Ini membuka UI browser tempat Anda bisa coba panggil tool tanpa perlu
menyambungkannya ke Orchestrator dulu — cara paling gampang memastikan
server ini jalan sebelum diintegrasikan.
