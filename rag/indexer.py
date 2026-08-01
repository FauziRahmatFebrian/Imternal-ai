import os
import re
import requests
import chromadb
import pdfplumber
from pypdf import PdfReader

SOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_docs")
VECTOR_STORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_store")
OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text"
MAX_CHUNK_SIZE = 800


def read_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_table_chunks(path: str) -> list[str]:
    chunks = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue  # skip tabel kosong atau cuma header tanpa isi

                headers = [h.strip() if h else f"kolom{i}" for i, h in enumerate(table[0])]

                for row in table[1:]:
                    if not any(cell and cell.strip() for cell in row):
                        continue  # skip baris kosong
                    row_text = ", ".join(
                        f"{headers[i]}: {cell.strip()}"
                        for i, cell in enumerate(row)
                        if cell and cell.strip()
                    )
                    chunks.append(f"[Tabel di halaman {page_num}] {row_text}")

    return chunks


def _is_probable_header(paragraph: str) -> bool:
    single_line = "\n" not in paragraph.strip()
    return single_line and len(paragraph) < 80 and not paragraph.rstrip().endswith((".", ":"))


def chunk_text(text: str, max_chunk_size: int = MAX_CHUNK_SIZE) -> list[str]:
    raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    merged = []
    i = 0
    while i < len(raw_paragraphs):
        para = raw_paragraphs[i]
        if _is_probable_header(para) and i + 1 < len(raw_paragraphs):
            merged.append(para + "\n" + raw_paragraphs[i + 1])
            i += 2
        else:
            merged.append(para)
            i += 1

    chunks = []
    current = ""
    for para in merged:
        if len(current) + len(para) <= max_chunk_size:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)

    return chunks


def embed(text: str) -> list[float]:
    response = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": EMBED_MODEL, "input": text},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]

def detect_team_from_filename(filename: str) -> str:
    name = os.path.splitext(filename)[0].lower()
    if name.startswith("sop_"):
        team_part = name[len("sop_"):]
        return team_part.replace("_", " ").replace("-", " ").title()
    return "Umum"


def main():
    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    collection = client.get_or_create_collection("sop_docs")

    pdf_files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"Tidak ada file PDF di {SOURCE_DIR}/ — taruh SOP di sana dulu.")
        return

    for filename in pdf_files:
        path = os.path.join(SOURCE_DIR, filename)
        print(f"Memproses {filename}...")
        tim = detect_team_from_filename(filename)
        print(f"  -> terdeteksi sebagai SOP tim: {tim}")

        # 1. Teks prosa biasa -> chunk berbasis paragraf
        text = read_pdf_text(path)
        text_chunks = chunk_text(text)
        print(f"  -> {len(text_chunks)} chunk teks biasa")

        # 2. Tabel -> chunk per baris (STRUKTUR terjaga)
        table_chunks = extract_table_chunks(path)
        print(f"  -> {len(table_chunks)} chunk dari tabel")

        all_chunks = [(c, "teks") for c in text_chunks] + [(c, "tabel") for c in table_chunks]

        for i, (chunk, chunk_type) in enumerate(all_chunks):
            chunk_id = f"{filename}-{chunk_type}-{i}"
            chunk_with_label = f"[SOP Tim {tim}] {chunk}"
            vector = embed(chunk_with_label)
            collection.upsert(
                ids=[chunk_id],
                embeddings=[vector],
                documents=[chunk_with_label],
                metadatas=[{"source": filename, "tim": tim, "chunk_index": i, "type": chunk_type}],
            )
        print(f"  -> selesai di-index ({len(all_chunks)} chunk total)")

    print("Indexing selesai.")


if __name__ == "__main__":
    main()