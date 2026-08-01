import os
from dotenv import load_dotenv
from langfuse import get_client

load_dotenv()

langfuse = get_client()

def start_generation(query: str, sensitive: bool):
    return langfuse.start_as_current_observation(
        name="ai-orchestrator-analyze",
        as_type="generation",
        input={"query": query, "sensitive": sensitive},
    )
def log_result(generation, path_used: str, model_used: str, answer: str):
    generation.update(
        output={"answer": answer},
        metadata={"path_used": path_used, "model_used": model_used},
    )
    langfuse.flush()