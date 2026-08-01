import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

load_dotenv()

client = AsyncOpenAI(
    base_url=os.getenv("NINEROUTER_BASE_URL", "http://localhost:20128/v1"),
    api_key=os.getenv("NINEROUTER_API_KEY", ""),
)
DEFAULT_MODEL_NAME = os.getenv("NINEROUTER_MODEL", "free_tier")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
)
async def call_router(query: str, model_name: str = None) -> tuple[str, str]:
    model = model_name or DEFAULT_MODEL_NAME
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": query}],
    )
    answer = response.choices[0].message.content
    return answer, model