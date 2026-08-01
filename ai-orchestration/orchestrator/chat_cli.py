import asyncio
from local_client import call_local
from router_client import call_router
from intent_router import detect_intents
from scope_guard import is_in_scope
from context_gatherer import gather_context, get_sql_context, get_rag_context
from context_gatherer import gather_context, get_sql_context, get_rag_context


async def ask_auto(question: str) -> tuple[str, set[str]]:
    if not await is_in_scope(question):
        return (
            "Maaf, pertanyaan ini di luar cakupan sistem ini. Sistem ini "
            "hanya menjawab pertanyaan seputar operasional internal perusahaan.",
            {"rejected"},
        )

    intents = detect_intents(question)
    context = await gather_context(question, intents)

    prompt = (
        f"Konteks data (dari sumber: {', '.join(sorted(intents))}):\n{context}\n\n"
        f"Pertanyaan: {question}\n\n"
        "Jawab berdasarkan konteks di atas. Kalau informasinya tidak "
        "cukup, katakan dengan jujur bagian mana yang tidak tersedia."
    )
    answer, _ = await call_router(prompt)
    return answer, intents


async def main():
    print("=== Chatbot CLI - Dashboard AI Monitoring ===")
    print("Pertanyaan biasa otomatis dianalisis, tool relevan dipanggil paralel.")
    print("Perintah manual (debug 1 komponen): '!sensitif <q>', '!sql <q>', '!sop <q>', 'exit'\n")

    while True:
        user_input = input("Anda: ").strip()

        if user_input.lower() in ("exit", "keluar"):
            print("Sampai jumpa.")
            break

        if not user_input:
            continue

        if user_input.startswith("!sensitif "):
            question = user_input[len("!sensitif "):]
            print("AI: (memproses lewat Local LLM saja...)")
            answer = await call_local(question)
            print(f"AI: {answer}\n")
            continue

        if user_input.startswith("!sql "):
            question = user_input[len("!sql "):]
            print("AI: (memproses lewat SQL Tool saja...)")
            context = await get_sql_context(question)
            prompt = f"Konteks:\n{context}\n\nPertanyaan: {question}\n\nJawab berdasarkan konteks di atas."
            answer, _ = await call_router(prompt)
            print(f"AI: {answer}\n")
            continue

        if user_input.startswith("!sop "):
            question = user_input[len("!sop "):]
            print("AI: (memproses lewat RAG saja...)")
            context = await get_rag_context(question)
            prompt = f"Konteks:\n{context}\n\nPertanyaan: {question}\n\nJawab berdasarkan konteks di atas, sebutkan sumbernya."
            answer, _ = await call_router(prompt)
            print(f"AI: {answer}\n")
            continue

        # Jalur otomatis: intent router + context gatherer paralel
        print("AI: (mendeteksi tool relevan...)")
        try:
            answer, intents = await ask_auto(user_input)
            print(f"AI: [tool dipakai: {', '.join(sorted(intents))}]")
            print(f"AI: {answer}\n")
        except Exception as e:
            print(f"AI: (terjadi error: {e})\n")


if __name__ == "__main__":
    asyncio.run(main()
                )
