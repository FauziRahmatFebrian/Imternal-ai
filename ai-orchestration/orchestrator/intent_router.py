KEYWORDS_SOP = ["aturan", "ketentuan", "sop", "kebijakan", "prosedur", "boleh", "diperbolehkan"]
KEYWORDS_BUSINESS_RULES = ["terlambat", "telat", "lembur", "produktivitas", "keterlambatan"]
KEYWORDS_SQL = ["berapa", "jumlah", "persen", "rata-rata", "daftar", "list", "siapa saja"]
KEYWORDS_MCP = ["task", "bulan", "produktivitas"]


def detect_intents(question: str) -> set[str]:
    lowered = question.lower()
    intents = set()
    if any(k in lowered for k in KEYWORDS_SOP):
        intents.add("rag")
    if any(k in lowered for k in KEYWORDS_BUSINESS_RULES):
        intents.add("business_rules")
    if any(k in lowered for k in KEYWORDS_SQL):
        intents.add("sql")
    if any(k in lowered for k in KEYWORDS_MCP):
        intents.add("mcp")
    intents.add("rag")

    if len(intents) == 1:  # cuma "rag" doang, tidak ada tool lain yang match
        intents.add("business_rules")
        intents.add("mcp")

    return intents