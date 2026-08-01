from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    query: str
    sensitive: bool = False


class AnalyzeResponse(BaseModel):
    answer: str
    path_used: str   # "local_direct" atau "router" — supaya kelihatan di log/response
    model_used: str
