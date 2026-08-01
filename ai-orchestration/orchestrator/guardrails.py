MAX_ANSWER_LENGTH = 2000     
MIN_ANSWER_LENGTH = 3           

SUSPICIOUS_PHRASES = [
    "sebagai AI", "saya adalah model bahasa", "saya tidak memiliki akses",
    "maaf, saya tidak bisa membantu",
]

def validate_answer(answer: str, context: str) -> dict:
    if not answer or len(answer.strip()) < MIN_ANSWER_LENGTH:
        return {
            "valid": False,
            "reason": "Jawaban kosong atau terlalu pendek.",
            "answer": "Maaf, sistem tidak berhasil menghasilkan jawaban. Coba ulangi pertanyaan.",
        }
    if len(answer) > MAX_ANSWER_LENGTH:
        return {
            "valid": False,
            "reason": f"Jawaban terlalu panjang ({len(answer)} karakter).",
            "answer": answer[:MAX_ANSWER_LENGTH] + "... (dipotong, jawaban terlalu panjang)",
        }

    lowered = answer.lower()
    for phrase in SUSPICIOUS_PHRASES:
        if phrase.lower() in lowered:
            return {
                "valid": False,
                "reason": f"Jawaban mengandung frasa mencurigakan: '{phrase}'",
                "answer": "Sistem tidak dapat memproses pertanyaan ini dengan baik. Coba pertanyaan lain.",
            }

    return {"valid": True, "reason": None, "answer": answer}