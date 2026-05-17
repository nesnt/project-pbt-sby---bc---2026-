
import os
import sys
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, storage
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

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
    "images_folder": "images",
    "api_url": "http://127.0.0.1:8000"
}

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)

with open(CONFIG_FILE, "r") as f:
    config_data = json.load(f)

# Direktori Gambar (Bisa Absolut atau Network LAN)
img_val = config_data.get("images_folder", "images")
if os.path.isabs(img_val) or img_val.startswith(r"\\"):
    IMAGES_DIR = img_val
else:
    IMAGES_DIR = os.path.join(BASE_DIR, img_val)

os.makedirs(IMAGES_DIR, exist_ok=True)

# URL API
API_URL = config_data.get("api_url", "http://127.0.0.1:8000")

# Inisialisasi Firebase
# Mencari file JSON di folder migrate yang merupakan file kredensial (biasanya nama file mengandung 'firebase-adminsdk')
MIGRATE_DIR = os.path.join(BASE_DIR, "migrate")
json_files = [f for f in os.listdir(MIGRATE_DIR) if f.endswith('.json') and 'firebase-adminsdk' in f]

if json_files:
    # Mengambil file JSON pertama yang ditemukan di folder migrate
    CRED_FILE = os.path.join(MIGRATE_DIR, json_files[0])
else:
    # Fallback ke nama file lama atau default jika tidak ditemukan
    CRED_FILE = os.path.join(MIGRATE_DIR, "kredensial_firebase.json")

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(CRED_FILE)
        firebase_admin.initialize_app(cred)
        print(f"Firebase berhasil diinisialisasi menggunakan: {os.path.basename(CRED_FILE)}")
    except Exception as e:
        print(f"Gagal inisialisasi Firebase: {e}")

# Inisialisasi Google Drive
DRIVE_FOLDER_ID = "1sPuG3yZAI-8hlxUX1hKXX3JA4anAVGLo"
drive_service = None

# Path untuk file OAuth
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "migrate", "config_gdrive", "client_secret_566200628496-j4aftfn1hfc7id1c7ju35csr38mnl97m.apps.googleusercontent.com.json")
TOKEN_FILE = os.path.join(BASE_DIR, "migrate", "token.json")
SCOPES = ['https://www.googleapis.com/auth/drive']

try:
    creds = None
    # Cari token.json yang sudah tersimpan
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Jika tidak ada token valid, minta user login (OAuth Flow)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.path.exists(CLIENT_SECRET_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                # Simpan token untuk sesi berikutnya
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            else:
                print(f"File client_secret tidak ditemukan: {CLIENT_SECRET_FILE}")

    if creds:
        drive_service = build('drive', 'v3', credentials=creds)
        print("Google Drive API (OAuth2) berhasil diinisialisasi")
except Exception as e:
    print(f"Gagal inisialisasi Google Drive (OAuth2): {e}")

try:
    db_firestore = firestore.client()
except Exception:
    db_firestore = None

def get_db():
    return db_firestore

def get_drive_service():
    return drive_service

def get_connection():
    """Stub for backward compatibility"""
    return db_firestore

def execute_query(query: str, params: tuple = (), fetch: bool = False):
    """Stub to raise error since we use Firebase now"""
    raise NotImplementedError("Gunakan get_db() untuk Firestore")

def run_migrations():
<<<<<<< HEAD
    """
    Jalankan migrasi database otomatis saat aplikasi start.
    Aman dijalankan berulang kali (idempotent).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # ── 1. Kolom 'foto' di tabel barang ─────────────────────────────
        cursor.execute("""
            SELECT COUNT(*) AS c FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'bc_smkn13'
              AND TABLE_NAME   = 'barang'
              AND COLUMN_NAME  = 'foto'
        """)
        if cursor.fetchone()["c"] == 0:
            cursor.execute(
                "ALTER TABLE barang ADD COLUMN foto VARCHAR(255) DEFAULT NULL"
            )
            conn.commit()
            print("[Migration] Kolom 'foto' ditambahkan ke tabel barang.")

        # ── 2. Kolom payment di tabel pesanan ────────────────────────────        # Kolom Payment
        new_cols = [
            ("nama_pembeli",      "VARCHAR(100)"),
            ("payment_status",     "VARCHAR(20) DEFAULT 'unpaid'"),
            ("payment_method",     "VARCHAR(50)"),
            ("transaction_id",     "VARCHAR(100)"),
            ("snap_token",         "VARCHAR(255)"),
            ("payment_proof",      "VARCHAR(255)"),
            ("confirmed_by_admin", "VARCHAR(100)"),
            ("confirmed_at",       "DATETIME"),
        ]
        for col, definition in new_cols:
            cursor.execute("""
                SELECT COUNT(*) AS c FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'bc_smkn13'
                  AND TABLE_NAME   = 'pesanan'
                  AND COLUMN_NAME  = %s
            """, (col,))
            if cursor.fetchone()["c"] == 0:
                cursor.execute(
                    f"ALTER TABLE pesanan ADD COLUMN {col} {definition}"
                )
                conn.commit()
                print(f"[Migration] Kolom '{col}' ditambahkan ke tabel pesanan.")

    except Exception as e:
        print(f"[Migration Warning] {e}")
    finally:
        cursor.close()
        conn.close()
=======
    pass
>>>>>>> 099d9731109ffb4053743896f150a6ec4c3aae72
