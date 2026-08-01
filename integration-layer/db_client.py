"""
Koneksi ke MySQL (phpMyAdmin) tempat data dummy disimpan.
Sekarang pakai CONNECTION POOLING (DBUtils.PooledDB) -- sebelumnya tiap
panggilan get_connection() bikin koneksi baru dari nol ke MySQL, yang
boros kalau dipanggil berulang kali lewat endpoint API (bukan cuma
sesekali lewat CLI seperti sebelumnya).

Dipakai bersama oleh integration-layer, MCP server, policy_rules, dan
text_to_sql -- semuanya tetap panggil get_connection() seperti biasa,
tidak ada perubahan cara pakai di file lain.
"""
import os
import pymysql
from dbutils.pooled_db import PooledDB
from dotenv import load_dotenv

load_dotenv()

_pool = None


def _get_pool() -> PooledDB:
    global _pool
    if _pool is None:
        _pool = PooledDB(
            creator=pymysql,
            maxconnections=8,     # batas atas koneksi bersamaan ke MySQL
            mincached=2,           # koneksi siap pakai yang selalu tersedia
            maxcached=5,            # maksimal koneksi menganggur disimpan
            blocking=True,           # kalau pool penuh, tunggu -- bukan error
            ping=1,                    # cek koneksi masih hidup sebelum dipakai
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME"),
            cursorclass=pymysql.cursors.DictCursor,
        )
    return _pool


def get_connection():
    return _get_pool().connection()