"""
Retriever — ambil chunk SOP paling relevan, LENGKAP dengan sumbernya
(nama file dan tim), penting begitu ada lebih dari 1 dokumen SOP.
"""
import sys
import os
import requests
import chromadb

VECTOR_STORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_store")
OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text"
MAX_DISTANCE_THRESHOLD = 999


def embed(text: str) -> list[float]:
    response = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": EMBED_MODEL, "input": text},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


def get_relevant_chunks(query: str, top_k: int = 3) -> list[dict]:
    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    collection = client.get_or_create_collection("sop_docs")
    query_vector = embed(query)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    relevant = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        if dist <= MAX_DISTANCE_THRESHOLD:
            relevant.append({
                "text": doc,
                "source": meta.get("source", "tidak diketahui"),
                "tim": meta.get("tim", "Umum"),
                "distance": dist,
            })

    return relevant


def format_chunks_as_context(chunks: list[dict]) -> str:
    if not chunks:
        return "(tidak ditemukan bagian SOP yang relevan dengan pertanyaan ini)"
    parts = []
    for c in chunks:
        parts.append(f"[Sumber: {c['source']}, Tim: {c['tim']}]\n{c['text']}")
    return "\n\n".join(parts)


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "apa aturan lembur?"
    chunks = get_relevant_chunks(query)
    print(f"Query: {query}\n")
    for c in chunks:
        print(f"(distance: {c['distance']:.3f}, tim: {c['tim']})")
    print(format_chunks_as_context(chunks))