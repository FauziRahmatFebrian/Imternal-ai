from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    query: str
    sensitive: bool = False


class AnalyzeResponse(BaseModel):
    answer: str
    path_used: str
    model_used: str
