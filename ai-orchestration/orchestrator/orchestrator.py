from fastapi import FastAPI
from schemas import AnalyzeRequest, AnalyzeResponse
from decision import choose_path
from local_client import call_local, LOCAL_MODEL_NAME
from router_client import call_router
from langfuse_client import start_generation, log_result
from guardrails import validate_answer
from intent_router import detect_intents
from context_gatherer import gather_context

app = FastAPI(title="AI Orchestrator")

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    from scope_guard import is_in_scope

    if not await is_in_scope(req.query):
        return AnalyzeResponse(
            answer="Maaf, pertanyaan ini di luar cakupan sistem ini. Sistem ini hanya menjawab pertanyaan seputar operasional internal perusahaan (kehadiran, task, SOP, dsb).",
            path_used="rejected:out_of_scope",
            model_used="none",
        )

    path = choose_path(req.sensitive)
    with start_generation(req.query, req.sensitive) as generation:
        if path == "local_direct":
            answer = await call_local(req.query)
            model_used = LOCAL_MODEL_NAME
            stage = "local_direct"
        else:
            intents = detect_intents(req.query)
            context = await gather_context(req.query, intents)
            prompt = (
                f"Konteks data (dari beberapa sumber: {', '.join(sorted(intents))}):\n{context}\n\n"
                f"Pertanyaan: {req.query}\n\n"
                "Jawab berdasarkan konteks di atas. Kalau informasinya tidak "
                "cukup, katakan dengan jujur bagian mana yang tidak tersedia."
            )
            answer, _ = await call_router(prompt)
            model_used = "9router"
            stage = "+".join(sorted(intents))
        validation = validate_answer(answer, "")
        final_answer = validation["answer"]
        log_result(generation, f"{path}:{stage}", model_used, final_answer)
    return AnalyzeResponse(answer=final_answer, path_used=f"{path}:{stage}", model_used=model_used)


@app.get("/health")
async def health():
    import asyncio
    import httpx
    import os
    checks = {}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://localhost:11434/api/tags")
            checks["ollama"] = "ok" if r.status_code == 200 else f"error (status {r.status_code})"
    except Exception as e:
        checks["ollama"] = f"mati atau tidak terjangkau ({type(e).__name__})"
    try:
        from db_client import get_connection
        conn = await asyncio.to_thread(get_connection)
        conn.close()
        checks["mysql"] = "ok"
    except Exception as e:
        checks["mysql"] = f"gagal konek ({type(e).__name__})"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://127.0.0.1:8200/mcp")
            checks["mcp_server"] = "ok (server merespons)"
    except Exception as e:
        checks["mcp_server"] = f"tidak dapat menyambungkan ({type(e).__name__})"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            base_url = os.getenv("NINEROUTER_BASE_URL", "http://localhost:20128/v1")
            r = await client.get(f"{base_url}/models",
                                   headers={"Authorization": f"Bearer {os.getenv('NINEROUTER_API_KEY', '')}"})
            checks["9router"] = "ok" if r.status_code < 500 else f"error (status {r.status_code})"
    except Exception as e:
        checks["9router"] = f"mati atau tidak terjangkau ({type(e).__name__})"
    all_ok = all(v == "ok" or v.startswith("ok") for v in checks.values())
    return {
        "status": "ok" if all_ok else "sebagian bermasalah",
        "services": checks,
    }

@app.get("/history")
async def history(limit: int = 20):
    from langfuse_client import langfuse
    try:
        traces = langfuse.api.trace.list(limit=limit)
    except Exception as e:
        return {"error": f"Gagal mengambil riwayat dari Langfuse: {e}"}
    result = []
    for t in traces.data:
        result.append({
            "id": t.id,
            "waktu": str(t.timestamp),
            "pertanyaan": t.input,
            "jawaban": t.output,
            "detail": t.metadata,
        })
    return {"jumlah": len(result), "riwayat": result}