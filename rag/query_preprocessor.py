"""
Query preprocessor untuk ekspansi sinonim dan normalisasi query bahasa Indonesia
"""

SYNONYM_GROUPS = {
    "aturan": ["aturan", "ketentuan", "peraturan", "kebijakan", "regulasi", "kaidah"],
    "lembur": ["lembur", "overtime", "kerja lembur", "jam lembur"],
    "cuti": ["cuti", "izin", "leave", "off"],
    "gaji": ["gaji", "upah", "penghasilan", "salary", "pembayaran"],
    "karyawan": ["karyawan", "pegawai", "staff", "pekerja", "employee"],
    "jam kerja": ["jam kerja", "waktu kerja", "jadwal kerja", "shift"],
    "absen": ["absen", "absensi", "kehadiran", "attendance", "presensi"],
    "terlambat": ["terlambat", "telat", "late"],
    "resign": ["resign", "mengundurkan diri", "keluar", "berhenti"],
    "kinerja": ["kinerja", "performa", "performance", "produktivitas"],
    "training": ["training", "pelatihan", "workshop", "kursus"],
    "bonus": ["bonus", "insentif", "tunjangan", "kompensasi"],
    "kontrak": ["kontrak", "perjanjian", "agreement"],
    "PHK": ["PHK", "pemutusan hubungan kerja", "pemecatan", "terminasi"],
    "tugas": ["tugas", "pekerjaan", "job", "task", "assignment"],
    "deadline": ["deadline", "tenggat", "batas waktu", "due date"],
    "proyek": ["proyek", "project", "program"],
    "meeting": ["meeting", "rapat", "pertemuan"],
    "laporan": ["laporan", "report", "dokumentasi"],
    "evaluasi": ["evaluasi", "penilaian", "assessment", "review"],
}

SYNONYM_MAP = {}
for canonical, synonyms in SYNONYM_GROUPS.items():
    for syn in synonyms:
        SYNONYM_MAP[syn.lower()] = canonical


def expand_query(query: str) -> list[str]:
    """
    Ekspansi query dengan sinonim. Return list query variations.
    """
    query_lower = query.lower()
    variations = [query]
    
    for synonym, canonical in SYNONYM_MAP.items():
        if synonym in query_lower:
            for replacement in SYNONYM_GROUPS[canonical]:
                if replacement.lower() != synonym:
                    new_query = query_lower.replace(synonym, replacement)
                    variations.append(new_query)
    
    return list(set(variations))


def normalize_query(query: str) -> str:
    """
    Normalisasi query dengan mengganti sinonim ke bentuk canonical.
    """
    query_lower = query.lower()
    normalized = query_lower
    
    for synonym, canonical in SYNONYM_MAP.items():
        if synonym in normalized:
            normalized = normalized.replace(synonym, canonical)
    
    return normalized
