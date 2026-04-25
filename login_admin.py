"""
login_admin.py - Halaman login khusus admin
Aplikasi Business Center SMKN 13 Bandung
"""

import tkinter as tk
from tkinter import messagebox
import hashlib
from db import execute_query

PRIMARY    = "#CC0000"
PRIMARY_DK = "#A00000"
WHITE      = "#FFFFFF"
LIGHT_GRAY = "#F5F5F5"
DARK_TEXT  = "#212121"
GRAY_TEXT  = "#757575"
SHADOW     = "#E8E8E8"


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


class LoginAdmin(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Login Admin — Business Center")
        self.geometry("420x480")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self._center(420, 480)
        self._build_ui()
        self.grab_set()

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=PRIMARY, height=110)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🔒", font=("Segoe UI", 30),
                 bg=PRIMARY, fg=WHITE).pack(pady=(18, 2))
        tk.Label(hdr, text="Login Admin", font=("Segoe UI", 16, "bold"),
                 bg=PRIMARY, fg=WHITE).pack()

        # ── Form Card ─────────────────────────────────────────────────────────
        card = tk.Frame(self, bg=WHITE, padx=36, pady=28)
        card.pack(expand=True, fill="both")

        tk.Label(card, text="Username", font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(0, 4))

        self.entry_user = tk.Entry(card, font=("Segoe UI", 12), relief="solid",
                                   bd=1, fg=DARK_TEXT, bg=LIGHT_GRAY)
        self.entry_user.pack(fill="x", ipady=8, pady=(0, 16))
        self.entry_user.focus()

        tk.Label(card, text="Password", font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(0, 4))

        pw_frame = tk.Frame(card, bg=WHITE)
        pw_frame.pack(fill="x", pady=(0, 24))

        self.entry_pass = tk.Entry(pw_frame, font=("Segoe UI", 12), relief="solid",
                                   bd=1, show="●", fg=DARK_TEXT, bg=LIGHT_GRAY)
        self.entry_pass.pack(side="left", fill="x", expand=True, ipady=8)

        self.show_pw = False
        self.btn_eye = tk.Button(pw_frame, text="👁", font=("Segoe UI", 10),
                                  bg=LIGHT_GRAY, relief="flat", bd=0,
                                  command=self._toggle_pw, cursor="hand2")
        self.btn_eye.pack(side="left", padx=(4, 0), ipady=8)

        # ── Tombol Login ──────────────────────────────────────────────────────
        self.btn_login = tk.Button(
            card, text="Masuk →", font=("Segoe UI", 12, "bold"),
            bg=PRIMARY, fg=WHITE, relief="flat", bd=0,
            pady=10, cursor="hand2",
            activebackground=PRIMARY_DK, activeforeground=WHITE,
            command=self._login
        )
        self.btn_login.pack(fill="x")

        tk.Button(card, text="← Kembali", font=("Segoe UI", 10),
                  bg=WHITE, fg=GRAY_TEXT, relief="flat", bd=0,
                  cursor="hand2", command=self.destroy).pack(pady=(14, 0))

        # ── Bind Enter ────────────────────────────────────────────────────────
        self.bind("<Return>", lambda e: self._login())

        # ── Hover efek tombol ─────────────────────────────────────────────────
        self.btn_login.bind("<Enter>", lambda e: self.btn_login.config(bg=PRIMARY_DK))
        self.btn_login.bind("<Leave>", lambda e: self.btn_login.config(bg=PRIMARY))

    def _toggle_pw(self):
        self.show_pw = not self.show_pw
        self.entry_pass.config(show="" if self.show_pw else "●")

    def _login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Peringatan", "Username dan password harus diisi!", parent=self)
            return

        try:
            rows = execute_query(
                "SELECT id_user, username, role FROM users WHERE username=%s AND password=%s",
                (username, hash_password(password)),
                fetch=True
            )
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        if rows:
            admin_data = rows[0]
            self.destroy()
            from admin.dashboard import AdminDashboard
            dash = AdminDashboard(self.master, admin_data)
            dash.protocol("WM_DELETE_WINDOW", lambda: self._on_dashboard_close(dash))
        else:
            messagebox.showerror("Gagal Login", "Username atau password salah!", parent=self)
            self.entry_pass.delete(0, "end")

    def _on_dashboard_close(self, dash):
        dash.destroy()
        self.master.deiconify()
