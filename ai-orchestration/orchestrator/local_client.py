import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

OLLAMA_URL = "http://localhost:11434/api/generate"
LOCAL_MODEL_NAME = "phi4-mini"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
)
async def call_local(query: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": LOCAL_MODEL_NAME,
                "prompt": query,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")