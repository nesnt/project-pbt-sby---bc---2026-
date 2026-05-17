"""
main.py - Entry point Aplikasi Business Center SMKN 13 Bandung
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Tambahkan path project ke sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# ─── Konstanta ────────────────────────────────────────────────────────────────
PRIMARY    = "#CC0000"
PRIMARY_DK = "#A00000"
WHITE      = "#FFFFFF"
LIGHT_GRAY = "#F2F2F2"
DARK_TEXT  = "#212121"
GRAY_TEXT  = "#757575"
ACCENT_G   = "#2E7D32"
ACCENT_G_DK= "#1B5E20"


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Business Center - SMKN 13 Bandung")
        self.geometry("560x420")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self._center(560, 420)
        self._build_ui()

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=PRIMARY, height=85)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="BUSINESS CENTER",
                 font=("Segoe UI", 20, "bold"),
                 bg=PRIMARY, fg=WHITE).pack(pady=(14, 0))
        tk.Label(hdr, text="SMKN 13 Bandung",
                 font=("Segoe UI", 10),
                 bg=PRIMARY, fg="#FFCCCC").pack()

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=WHITE)
        body.pack(expand=True, fill="both")

        tk.Label(body, text="Selamat Datang!",
                 font=("Segoe UI", 16, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(pady=(28, 4))
        tk.Label(body, text="Silakan pilih mode:",
                 font=("Segoe UI", 11),
                 bg=WHITE, fg=GRAY_TEXT).pack(pady=(0, 24))

        # ── Dua tombol utama ──────────────────────────────────────────────────
        btn_frame = tk.Frame(body, bg=WHITE)
        btn_frame.pack()

        # --- Tombol Transaksi ---
        frame_t = tk.Frame(btn_frame, bg=LIGHT_GRAY,
                           highlightbackground="#CCCCCC",
                           highlightthickness=1)
        frame_t.grid(row=0, column=0, padx=16)

        tk.Label(frame_t, text="Transaksi",
                 font=("Segoe UI", 14, "bold"),
                 bg=LIGHT_GRAY, fg=DARK_TEXT,
                 width=16, pady=10).pack()
        tk.Label(frame_t, text="Kasir / Pembeli\n(tanpa login)",
                 font=("Segoe UI", 9),
                 bg=LIGHT_GRAY, fg=GRAY_TEXT,
                 justify="center").pack(pady=(0, 8))

        btn_t = tk.Button(frame_t,
                          text="Masuk ke Transaksi",
                          font=("Segoe UI", 10, "bold"),
                          bg=ACCENT_G, fg=WHITE,
                          activebackground=ACCENT_G_DK,
                          activeforeground=WHITE,
                          relief="flat", bd=0,
                          padx=14, pady=8,
                          cursor="hand2",
                          command=self._open_transaksi)
        btn_t.pack(padx=16, pady=(0, 14))

        # --- Tombol Admin ---
        frame_a = tk.Frame(btn_frame, bg=LIGHT_GRAY,
                           highlightbackground="#CCCCCC",
                           highlightthickness=1)
        frame_a.grid(row=0, column=1, padx=16)

        tk.Label(frame_a, text="Admin",
                 font=("Segoe UI", 14, "bold"),
                 bg=LIGHT_GRAY, fg=DARK_TEXT,
                 width=16, pady=10).pack()
        tk.Label(frame_a, text="Kelola barang &\nkonfirmasi pesanan",
                 font=("Segoe UI", 9),
                 bg=LIGHT_GRAY, fg=GRAY_TEXT,
                 justify="center").pack(pady=(0, 8))

        btn_a = tk.Button(frame_a,
                          text="Login Admin",
                          font=("Segoe UI", 10, "bold"),
                          bg=PRIMARY, fg=WHITE,
                          activebackground=PRIMARY_DK,
                          activeforeground=WHITE,
                          relief="flat", bd=0,
                          padx=14, pady=8,
                          cursor="hand2",
                          command=self._open_admin_login)
        btn_a.pack(padx=16, pady=(0, 14))

        # Hover efek hanya pada frame pembungkus (BUKAN button)
        for card, btn, hover_col, normal_col in [
            (frame_t, btn_t, "#E8F5E9", LIGHT_GRAY),
            (frame_a, btn_a, "#FFEBEE", LIGHT_GRAY),
        ]:
            for lbl in card.winfo_children():
                if isinstance(lbl, tk.Label):
                    lbl.bind("<Enter>", lambda e, c=card, h=hover_col: c.config(bg=h))
                    lbl.bind("<Leave>", lambda e, c=card, n=normal_col: c.config(bg=n))
            card.bind("<Enter>", lambda e, c=card, h=hover_col: c.config(bg=h))
            card.bind("<Leave>", lambda e, c=card, n=normal_col: c.config(bg=n))

        # ── Footer ────────────────────────────────────────────────────────────
        tk.Label(self,
                 text="(c) 2024 Business Center SMKN 13 Bandung",
                 font=("Segoe UI", 8),
                 bg=WHITE, fg="#AAAAAA").pack(pady=10)

    # ── Navigasi ──────────────────────────────────────────────────────────────
    def _open_transaksi(self):
        try:
            from user.transaksi import TransaksiWindow
            self.withdraw()
            win = TransaksiWindow(self)
            win.protocol("WM_DELETE_WINDOW", lambda: self._on_child_close(win))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_admin_login(self):
        try:
            from login_admin import LoginAdmin
            self.withdraw()
            win = LoginAdmin(self)
            win.protocol("WM_DELETE_WINDOW", lambda: self._on_child_close(win))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_child_close(self, win):
        win.destroy()
        self.deiconify()


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        from db import get_connection, run_migrations
        conn = get_connection()
        conn.close()
        run_migrations()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Koneksi Database Gagal",
            f"{e}\n\nPastikan:\n1. MySQL sudah berjalan\n"
            "2. Konfigurasi di db.py sudah benar\n3. Sudah menjalankan setup_db.py"
        )
        sys.exit(1)

    # ── Jalankan Flask webhook server Midtrans di background ─────────────────
    try:
        from midtrans_webhook import ensure_webhook_running
        ensure_webhook_running()
    except Exception as _we:
        print(f"[Warning] Webhook Midtrans tidak bisa dijalankan: {_we}")

    app = MainApp()
    app.mainloop()
