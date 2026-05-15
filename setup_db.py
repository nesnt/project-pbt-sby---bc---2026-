"""
setup_db.py - Script setup database (jalankan sekali saja)
Aplikasi Business Center SMKN 13 Bandung

Cara pakai:
    python setup_db.py

Akan membuat:
  - Database: bc_smkn13
  - Tabel  : users, barang, pesanan, detail_pesanan
  - Admin  : username=admin, password=admin123
"""

import mysql.connector
from mysql.connector import Error
import hashlib

# ─── Konfigurasi koneksi awal (tanpa nama database) ──────────────────────────
INIT_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",          # Sesuaikan password MySQL Anda
}

DB_NAME = "bc_smkn13"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def run_setup():
    print("=" * 50)
    print("  Setup Database BC SMKN 13 Bandung")
    print("=" * 50)

    try:
        conn = mysql.connector.connect(**INIT_CONFIG)
        cursor = conn.cursor()

        # 1. Buat database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE `{DB_NAME}`;")
        print(f"[OK] Database '{DB_NAME}' siap.")

        # 2. Tabel users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id_user    INT AUTO_INCREMENT PRIMARY KEY,
                username   VARCHAR(50) UNIQUE NOT NULL,
                password   VARCHAR(255) NOT NULL,
                role       ENUM('admin') DEFAULT 'admin'
            ) ENGINE=InnoDB;
        """)
        print("[OK] Tabel 'users' siap.")

        # 3. Tabel barang
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS barang (
                id_barang    INT AUTO_INCREMENT PRIMARY KEY,
                nama_barang  VARCHAR(100) NOT NULL,
                harga_barang DECIMAL(10,2) NOT NULL,
                stok         INT NOT NULL DEFAULT 0,
                gambar       VARCHAR(225)
            ) ENGINE=InnoDB;
        """)
        print("[OK] Tabel 'barang' siap.")

        # 4. Tabel pesanan
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pesanan (
                id_pesanan  INT AUTO_INCREMENT PRIMARY KEY,
                tanggal     DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_harga DECIMAL(10,2) NOT NULL,
                status      ENUM('pending','diterima','ditolak') DEFAULT 'pending'
            ) ENGINE=InnoDB;
        """)
        print("[OK] Tabel 'pesanan' siap.")

        # 5. Tabel detail_pesanan
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detail_pesanan (
                id_detail   INT AUTO_INCREMENT PRIMARY KEY,
                id_pesanan  INT NOT NULL,
                id_barang   INT NOT NULL,
                jumlah      INT NOT NULL,
                subtotal    DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (id_pesanan) REFERENCES pesanan(id_pesanan) ON DELETE CASCADE,
                FOREIGN KEY (id_barang)  REFERENCES barang(id_barang)  ON DELETE RESTRICT
            ) ENGINE=InnoDB;
        """)
        print("[OK] Tabel 'detail_pesanan' siap.")

        # 6. Insert admin default (jika belum ada)
        cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE username = 'admin';")
        row = cursor.fetchone()
        if row[0] == 0:
            hashed = hash_password("admin123")
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, 'admin');",
                ("admin", hashed)
            )
            conn.commit()
            print("[OK] Admin default dibuat  =>  username: admin | password: admin123")
        else:
            print("[--] Admin sudah ada, dilewati.")

        # 7. Contoh data barang (jika tabel kosong)
        cursor.execute("SELECT COUNT(*) FROM barang;")
        if cursor.fetchone()[0] == 0:
            sample_barang = [
                ("Pensil 2B",      2500,  50),
                ("Bolpoin Hitam",  3000,  80),
                ("Buku Tulis 40",  8000,  30),
                ("Penghapus",      2000,  60),
                ("Penggaris 30cm", 5000,  25),
                ("Stabilo",        7500,  20),
                ("Spidol Hitam",   6000,  15),
                ("Kertas HVS/rim", 45000, 10),
            ]
            cursor.executemany(
                "INSERT INTO barang (nama_barang, harga_barang, stok) VALUES (%s, %s, %s);",
                sample_barang
            )
            conn.commit()
            print(f"[OK] {len(sample_barang)} contoh barang ditambahkan.")

        cursor.close()
        conn.close()

        print()
        print("=" * 50)
        print("  Setup selesai! Jalankan: python main.py")
        print("=" * 50)

    except Error as e:
        print(f"[ERROR] {e}")
        print("Pastikan MySQL berjalan dan konfigurasi di setup_db.py sudah benar.")


if __name__ == "__main__":
    run_setup()
