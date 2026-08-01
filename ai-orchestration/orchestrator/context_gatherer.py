import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recommendation"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "rag"))

from context_builder import get_context_from_mcp
from policy_rules import run_all_detections
from generate_cli import format_findings_as_text
from text_to_sql import run_text_to_sql
from retriever import get_relevant_chunks, format_chunks_as_context


async def get_business_rules_context(question: str = "") -> str:
    findings = await asyncio.to_thread(run_all_detections)
    return "[Business Rules]\n" + format_findings_as_text(findings)


async def get_mcp_context(question: str = "") -> str:
    result = await get_context_from_mcp()
    return "[MCP - data warehouse]\n" + result


async def get_sql_context(question: str) -> str:
    result = await asyncio.to_thread(run_text_to_sql, question)
    if not result["success"]:
        return f"[SQL Tool]\n(tidak berhasil: {result['reason']})"
    return f"[SQL Tool]\nQuery: {result['sql']}\nHasil: {result['rows']}"


async def get_rag_context(question: str) -> str:
    chunks = await asyncio.to_thread(get_relevant_chunks, question)
    if not chunks:
        return "[RAG - dokumen SOP]\n(tidak ditemukan bagian relevan)"
    return "[RAG - dokumen SOP]\n" + format_chunks_as_context(chunks)

TOOL_FUNCTIONS = {
    "business_rules": get_business_rules_context,
    "mcp": get_mcp_context,
    "sql": get_sql_context,
    "rag": get_rag_context,
}

async def gather_context(question: str, intents: set[str]) -> str:
    tasks = [TOOL_FUNCTIONS[intent](question) for intent in intents if intent in TOOL_FUNCTIONS]
    results = await asyncio.gather(*tasks)
    return "\n\n".join(results)