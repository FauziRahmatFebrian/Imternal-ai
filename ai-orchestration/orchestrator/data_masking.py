import os
import sys

from presidio_analyzer import AnalyzerEngine, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "integration-layer"))
from db_client import get_connection

_analyzer = None
_anonymizer = None


def get_employee_names() -> list[str]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM employees")
            rows = cur.fetchall()
        return [row["name"] for row in rows if row.get("name")]
    finally:
        conn.close()


def _build_analyzer() -> AnalyzerEngine:
    nlp_configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }
    provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
    nlp_engine = provider.create_engine()

    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

    names = get_employee_names()
    employee_recognizer = PatternRecognizer(
        supported_entity="EMPLOYEE_NAME",
        deny_list=names,
    )
    analyzer.registry.add_recognizer(employee_recognizer)
    return analyzer


def _get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        _analyzer = _build_analyzer()
    return _analyzer


def _get_anonymizer() -> AnonymizerEngine:
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _anonymizer


def mask_text(text: str) -> str:
    """
    Deteksi & mask nama karyawan (dan email/no telepon kalau kebetulan
    ada) di dalam teks. Dipanggil SEBELUM teks apapun dikirim ke 9Router.
    """
    if not text:
        return text

    analyzer = _get_analyzer()
    anonymizer = _get_anonymizer()

    results = analyzer.analyze(
        text=text,
        language="en",
        entities=["EMPLOYEE_NAME", "EMAIL_ADDRESS", "PHONE_NUMBER"],
    )
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text


if __name__ == "__main__":
    sample = "Budi Santoso terlambat 3 kali, hubungi di budi@perusahaan.com untuk klarifikasi."
    print("Sebelum:", sample)
    print("Sesudah:", mask_text(sample))