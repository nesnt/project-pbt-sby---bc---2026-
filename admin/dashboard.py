"""
admin/dashboard.py - Dashboard utama admin
Aplikasi Business Center SMKN 13 Bandung
"""

import tkinter as tk
from tkinter import messagebox
from db import get_db

# ─── Palet Warna ─────────────────────────────────────────────────────────────
PRIMARY    = "#CC0000"
PRIMARY_DK = "#A00000"
SIDEBAR_BG = "#1A1A2E"
SIDEBAR_HV = "#16213E"
WHITE      = "#FFFFFF"
LIGHT_GRAY = "#F5F5F5"
DARK_TEXT  = "#212121"
GRAY_TEXT  = "#757575"
ACCENT_G   = "#2E7D32"
ACCENT_B   = "#1565C0"
CARD_COLORS = ["#CC0000", "#1565C0", "#2E7D32", "#6A1B9A"]


class AdminDashboard(tk.Toplevel):
    def __init__(self, master, admin_data: dict):
        super().__init__(master)
        self.master       = master
        self.admin_data   = admin_data
        self.active_frame = None
        self.sidebar_btns = {}

        self.title("Admin Dashboard — Business Center SMKN 13")
        self.geometry("1060x640")
        self.configure(bg=LIGHT_GRAY)
        self._center(1060, 640)
        self._build_ui()
        self._show_home()
        self.grab_set()

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Layout utama ──────────────────────────────────────────────────────────
    def _build_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo sidebar
        logo_frame = tk.Frame(self.sidebar, bg=PRIMARY, height=80)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        tk.Label(logo_frame, text="🏫  BC Admin", font=("Segoe UI", 13, "bold"),
                 bg=PRIMARY, fg=WHITE).pack(expand=True)

        tk.Label(self.sidebar, text=f"Halo, {self.admin_data['username']} 👋",
                 font=("Segoe UI", 9), bg=SIDEBAR_BG, fg="#AAAAAA").pack(pady=(12, 16))

        # Menu item
        menus = [
            ("🏠  Dashboard",        "home"),
            ("📦  Kelola Barang",    "barang"),
            ("📋  Konfirmasi Pesanan","konfirmasi"),
        ]
        for label, key in menus:
            btn = tk.Button(
                self.sidebar, text=label,
                font=("Segoe UI", 10), anchor="w",
                bg=SIDEBAR_BG, fg="#CCCCCC",
                relief="flat", bd=0,
                padx=20, pady=12, cursor="hand2",
                activebackground=SIDEBAR_HV, activeforeground=WHITE,
                command=lambda k=key: self._navigate(k)
            )
            btn.pack(fill="x")
            self.sidebar_btns[key] = btn

        # Divider
        tk.Frame(self.sidebar, bg="#333355", height=1).pack(fill="x", pady=10, padx=16)

        # Logout
        tk.Button(self.sidebar, text="🚪  Logout",
                  font=("Segoe UI", 10), anchor="w",
                  bg=SIDEBAR_BG, fg="#FF6B6B",
                  relief="flat", bd=0, padx=20, pady=12, cursor="hand2",
                  activebackground="#3D0000", activeforeground=WHITE,
                  command=self._logout).pack(fill="x", side="bottom", pady=(0, 8))

        # Area konten kanan
        self.content_area = tk.Frame(self, bg=LIGHT_GRAY)
        self.content_area.pack(side="left", fill="both", expand=True)

    # ── Navigasi ──────────────────────────────────────────────────────────────
    def _navigate(self, key: str):
        for k, btn in self.sidebar_btns.items():
            btn.config(bg=PRIMARY if k == key else SIDEBAR_BG,
                       fg=WHITE   if k == key else "#CCCCCC")
        if self.active_frame:
            self.active_frame.destroy()

        if key == "home":
            self._show_home()
        elif key == "barang":
            self._show_barang()
        elif key == "konfirmasi":
            self._show_konfirmasi()

    def _show_home(self):
        for k, btn in self.sidebar_btns.items():
            btn.config(bg=PRIMARY if k == "home" else SIDEBAR_BG,
                       fg=WHITE   if k == "home" else "#CCCCCC")
        if self.active_frame:
            self.active_frame.destroy()
        self.active_frame = HomeDashboard(self.content_area, self)
        self.active_frame.pack(fill="both", expand=True)

    def _show_barang(self):
        if self.active_frame:
            self.active_frame.destroy()
        from admin.barang import BarangPanel
        self.active_frame = BarangPanel(self.content_area, self)
        self.active_frame.pack(fill="both", expand=True)

    def _show_konfirmasi(self):
        if self.active_frame:
            self.active_frame.destroy()
        from admin.konfirmasi import KonfirmasiPanel
        self.active_frame = KonfirmasiPanel(self.content_area, self)
        self.active_frame.pack(fill="both", expand=True)

    def _logout(self):
        if messagebox.askyesno("Logout", "Yakin ingin keluar dari dashboard admin?", parent=self):
            self.destroy()
            self.master.deiconify()


# ─── Halaman Home Dashboard ───────────────────────────────────────────────────
class HomeDashboard(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=LIGHT_GRAY)
        self.dashboard = dashboard
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=WHITE, height=60)
        hdr.pack(fill="x", padx=0, pady=0)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Dashboard", font=("Segoe UI", 16, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(side="left", padx=24, pady=14)

        import datetime
        now = datetime.datetime.now().strftime("%A, %d %B %Y")
        tk.Label(hdr, text=now, font=("Segoe UI", 9),
                 bg=WHITE, fg=GRAY_TEXT).pack(side="right", padx=24)

        # Statistik cards
        stats_frame = tk.Frame(self, bg=LIGHT_GRAY)
        stats_frame.pack(fill="x", padx=20, pady=20)

        stats = self._get_stats()
        cards_data = [
            ("📦", "Total Barang",      str(stats["barang"]),    CARD_COLORS[0]),
            ("⏳", "Pesanan Pending",   str(stats["pending"]),   CARD_COLORS[1]),
            ("✅", "Pesanan Diterima", str(stats["diterima"]),   CARD_COLORS[2]),
            ("❌", "Pesanan Ditolak",  str(stats["ditolak"]),    CARD_COLORS[3]),
        ]
        for i, (icon, label, value, color) in enumerate(cards_data):
            self._make_stat_card(stats_frame, icon, label, value, color, col=i)

        # Akses cepat
        quick = tk.Frame(self, bg=WHITE, relief="flat")
        quick.pack(fill="x", padx=20, pady=(0, 20))
        tk.Label(quick, text="Akses Cepat", font=("Segoe UI", 12, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(anchor="w", padx=16, pady=(14, 10))

        btn_row = tk.Frame(quick, bg=WHITE)
        btn_row.pack(padx=16, pady=(0, 16), anchor="w")

        tk.Button(btn_row, text="➕  Tambah Barang", font=("Segoe UI", 10, "bold"),
                  bg=PRIMARY, fg=WHITE, relief="flat", padx=16, pady=8, cursor="hand2",
                  command=lambda: self.dashboard._navigate("barang")).pack(side="left", padx=(0, 10))
        tk.Button(btn_row, text="📋  Lihat Pesanan Pending", font=("Segoe UI", 10, "bold"),
                  bg=ACCENT_B, fg=WHITE, relief="flat", padx=16, pady=8, cursor="hand2",
                  command=lambda: self.dashboard._navigate("konfirmasi")).pack(side="left")

        # Tabel pesanan terbaru
        recent_frame = tk.Frame(self, bg=WHITE)
        recent_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        tk.Label(recent_frame, text="Pesanan Terbaru", font=("Segoe UI", 12, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(anchor="w", padx=16, pady=(14, 8))

        self._build_recent_table(recent_frame)

    def _make_stat_card(self, parent, icon, label, value, color, col):
        card = tk.Frame(parent, bg=color, height=110, relief="flat")
        card.grid(row=0, column=col, padx=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(col, weight=1)
        card.pack_propagate(False)

        tk.Label(card, text=icon, font=("Segoe UI", 22),
                 bg=color, fg=WHITE).pack(pady=(14, 2))
        tk.Label(card, text=value, font=("Segoe UI", 20, "bold"),
                 bg=color, fg=WHITE).pack()
        tk.Label(card, text=label, font=("Segoe UI", 9),
                 bg=color, fg="#FFDDDD").pack()

    def _get_stats(self) -> dict:
        try:
            db = get_db()
            # In Firestore, getting counts can be done with count() queries if supported,
            # or by retrieving the snapshot length.
            barang_len = len(db.collection('barang').get())
            pending_len = len(db.collection('pesanan').where('status', '==', 'pending').get())
            diterima_len = len(db.collection('pesanan').where('status', '==', 'diterima').get())
            ditolak_len = len(db.collection('pesanan').where('status', '==', 'ditolak').get())
            
            return {
                "barang":   barang_len,
                "pending":  pending_len,
                "diterima": diterima_len,
                "ditolak":  ditolak_len,
            }
        except Exception as e:
            print(f"Error _get_stats: {e}")
            return {"barang": 0, "pending": 0, "diterima": 0, "ditolak": 0}

    def _build_recent_table(self, parent):
        import tkinter.ttk as ttk

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Recent.Treeview",
                        font=("Segoe UI", 9), rowheight=28,
                        background=WHITE, fieldbackground=WHITE,
                        foreground=DARK_TEXT)
        style.configure("Recent.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background=PRIMARY, foreground=WHITE)
        style.map("Recent.Treeview", background=[("selected", "#FFE0E0")])

        cols = ("ID", "Tanggal", "Total", "Status")
        tv   = ttk.Treeview(parent, columns=cols, show="headings",
                            style="Recent.Treeview", height=6)
        tv.heading("ID",      text="ID Pesanan")
        tv.heading("Tanggal", text="Tanggal")
        tv.heading("Total",   text="Total Harga")
        tv.heading("Status",  text="Status")

        tv.column("ID",      width=90,  anchor="center")
        tv.column("Tanggal", width=160, anchor="center")
        tv.column("Total",   width=130, anchor="e")
        tv.column("Status",  width=100, anchor="center")

        sb = ttk.Scrollbar(parent, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, 16))
        tv.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        try:
            from firebase_admin import firestore
            db = get_db()
            docs = db.collection('pesanan').order_by('tanggal', direction=firestore.Query.DESCENDING).limit(10).stream()
            
            for doc in docs:
                r = doc.to_dict()
                total = f"Rp {r.get('total_harga', 0):,.0f}"
                tv.insert("", "end", values=(doc.id[:8], r.get("tanggal", ""), total, r.get("status", "").upper()))
        except Exception as e:
            print(f"Error recent_table: {e}")