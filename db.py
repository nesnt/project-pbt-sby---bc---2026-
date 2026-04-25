"""
db.py - Modul koneksi database MySQL + Migrasi otomatis
Aplikasi Business Center SMKN 13 Bandung
"""

import pymysql
import os
import sys
import json

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEFAULT_CONFIG = {
    "db_host": "localhost",
    "db_user": "root",
    "db_password": "",
    "db_name": "bc_smkn13",
    "images_folder": "images"  # Bisa diisi path network seperti "\\\\192.168.1.15\\images"
}

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)

with open(CONFIG_FILE, "r") as f:
    config_data = json.load(f)

# Konfigurasi Database Dinamis
DB_CONFIG = {
    "host":     config_data.get("db_host", "localhost"),
    "user":     config_data.get("db_user", "root"),
    "password": config_data.get("db_password", ""),
    "database": config_data.get("db_name", "bc_smkn13"),
    "charset":  "utf8mb4",
}

# Direktori Gambar (Bisa Absolut atau Network LAN)
img_val = config_data.get("images_folder", "images")
if os.path.isabs(img_val) or img_val.startswith(r"\\"):
    IMAGES_DIR = img_val
else:
    IMAGES_DIR = os.path.join(BASE_DIR, img_val)

os.makedirs(IMAGES_DIR, exist_ok=True)


def get_connection():
    """Mengembalikan objek koneksi MySQL menggunakan PyMySQL."""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            charset=DB_CONFIG["charset"],
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        raise ConnectionError(f"Gagal terhubung ke database:\n{e}")

def execute_query(query: str, params: tuple = (), fetch: bool = False):
    """
    Helper untuk menjalankan query DML/DQL.
    - fetch=False → INSERT/UPDATE/DELETE (mengembalikan lastrowid)
    - fetch=True  → SELECT (mengembalikan list of dict)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Query error:\n{e}\nQuery: {query}")
    finally:
        cursor.close()
        conn.close()

def run_migrations():
    """
    Jalankan migrasi database otomatis saat aplikasi start.
    Aman dijalankan berulang kali (idempotent).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Tambah kolom 'foto' ke tabel barang jika belum ada
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'bc_smkn13'
              AND TABLE_NAME   = 'barang'
              AND COLUMN_NAME  = 'foto'
        """)
        if cursor.fetchone()["COUNT(*)"] == 0:
            cursor.execute(
                "ALTER TABLE barang ADD COLUMN foto VARCHAR(255) DEFAULT NULL"
            )
            conn.commit()
            print("[Migration] Kolom 'foto' ditambahkan ke tabel barang.")
    except Exception as e:
        print(f"[Migration Warning] {e}")
    finally:
        cursor.close()
        conn.close()
