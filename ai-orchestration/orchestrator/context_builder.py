"""
Context builder — menyambungkan AI Orchestrator ke MCP server lewat HTTP.

Sekarang pakai RETRY untuk error koneksi/timeout.
"""
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_SERVER_URL = "http://127.0.0.1:8200/mcp"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, ConnectionError)),
)
async def get_context_from_mcp() -> str:
    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_monthly_task_counts", {"months_back": 3})
            text_parts = [c.text for c in result.content if hasattr(c, "text")]
            return "\n".join(text_parts) if text_parts else "(tidak ada data dari MCP)"