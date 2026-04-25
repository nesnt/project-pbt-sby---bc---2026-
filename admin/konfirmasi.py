"""
admin/konfirmasi.py - Panel Konfirmasi Pesanan (Terima / Tolak)
Aplikasi Business Center SMKN 13 Bandung
"""

import tkinter as tk
from tkinter import ttk, messagebox
from db import execute_query, get_connection

PRIMARY    = "#CC0000"
PRIMARY_DK = "#A00000"
WHITE      = "#FFFFFF"
LIGHT_GRAY = "#F5F5F5"
DARK_TEXT  = "#212121"
GRAY_TEXT  = "#757575"
ACCENT_G   = "#2E7D32"
ACCENT_G_DK= "#1B5E20"
ACCENT_B   = "#1565C0"
ROW_ALT    = "#FFF5F5"

STATUS_COLOR = {
    "pending":  "#E65100",
    "diterima": "#2E7D32",
    "ditolak":  "#B71C1C",
}


class KonfirmasiPanel(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=LIGHT_GRAY)
        self.dashboard    = dashboard
        self.selected_id  = None
        self._filter_val  = "semua"
        self._build()
        self._load_pesanan()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=WHITE, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📋  Konfirmasi Pesanan", font=("Segoe UI", 15, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(side="left", padx=24, pady=14)
        tk.Button(hdr, text="🔄 Refresh", font=("Segoe UI", 9),
                  bg=LIGHT_GRAY, fg=DARK_TEXT, relief="flat", padx=10, pady=5,
                  cursor="hand2", command=self._refresh).pack(side="right", padx=16)

        # Filter tabs
        tab_bar = tk.Frame(self, bg=WHITE)
        tab_bar.pack(fill="x", padx=20, pady=(8, 0))

        self.filter_btns = {}
        filters = [("Semua", "semua"), ("⏳ Pending", "pending"),
                   ("✅ Diterima", "diterima"), ("❌ Ditolak", "ditolak")]
        for label, key in filters:
            btn = tk.Button(tab_bar, text=label, font=("Segoe UI", 9, "bold"),
                            relief="flat", padx=12, pady=7, cursor="hand2",
                            command=lambda k=key: self._set_filter(k))
            btn.pack(side="left", padx=(0, 4))
            self.filter_btns[key] = btn
        self._set_filter("semua", init=True)

        # Splitter: kiri = daftar pesanan, kanan = detail
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=LIGHT_GRAY, sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=20, pady=12)

        # ── Panel kiri: tabel pesanan ──────────────────────────────────────
        left_panel = tk.Frame(paned, bg=WHITE)
        paned.add(left_panel, minsize=380)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Pesanan.Treeview",
                        font=("Segoe UI", 9), rowheight=30,
                        background=WHITE, fieldbackground=WHITE, foreground=DARK_TEXT)
        style.configure("Pesanan.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background=PRIMARY, foreground=WHITE, relief="flat")
        style.map("Pesanan.Treeview",
                  background=[("selected", "#FFD6D6")],
                  foreground=[("selected", DARK_TEXT)])

        cols = ("ID", "Tanggal", "Total", "Status")
        self.tree = ttk.Treeview(left_panel, columns=cols,
                                  show="headings", style="Pesanan.Treeview")
        self.tree.heading("ID",      text="ID")
        self.tree.heading("Tanggal", text="Tanggal & Jam")
        self.tree.heading("Total",   text="Total Harga")
        self.tree.heading("Status",  text="Status")

        self.tree.column("ID",      width=55,  anchor="center")
        self.tree.column("Tanggal", width=160, anchor="center")
        self.tree.column("Total",   width=120, anchor="e")
        self.tree.column("Status",  width=90,  anchor="center")

        sb_left = ttk.Scrollbar(left_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb_left.set)
        sb_left.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=(8, 0), pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_pesanan_select)

        # ── Panel kanan: detail pesanan + aksi ────────────────────────────
        right_panel = tk.Frame(paned, bg=LIGHT_GRAY)
        paned.add(right_panel, minsize=260)

        # Info pesanan
        self.info_frame = tk.Frame(right_panel, bg=WHITE)
        self.info_frame.pack(fill="x", padx=8, pady=(8, 4))

        self.lbl_id     = tk.Label(self.info_frame, text="Pilih pesanan →",
                                    font=("Segoe UI", 12, "bold"),
                                    bg=WHITE, fg=DARK_TEXT, anchor="w")
        self.lbl_id.pack(fill="x", padx=12, pady=(12, 2))

        self.lbl_status = tk.Label(self.info_frame, text="",
                                    font=("Segoe UI", 10),
                                    bg=WHITE, fg=GRAY_TEXT, anchor="w")
        self.lbl_status.pack(fill="x", padx=12, pady=(0, 12))

        # Header detail items
        tk.Label(right_panel, text="Detail Item:", font=("Segoe UI", 10, "bold"),
                 bg=LIGHT_GRAY, fg=DARK_TEXT, anchor="w").pack(
                     fill="x", padx=8, pady=(4, 0))

        detail_frame = tk.Frame(right_panel, bg=WHITE)
        detail_frame.pack(fill="both", expand=True, padx=8, pady=4)

        style.configure("Detail.Treeview",
                        font=("Segoe UI", 9), rowheight=26,
                        background=WHITE, fieldbackground=WHITE, foreground=DARK_TEXT)
        style.configure("Detail.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background=ACCENT_B, foreground=WHITE, relief="flat")

        det_cols = ("Barang", "Jml", "Subtotal")
        self.tree_detail = ttk.Treeview(detail_frame, columns=det_cols,
                                         show="headings", style="Detail.Treeview")
        self.tree_detail.heading("Barang",   text="Nama Barang")
        self.tree_detail.heading("Jml",      text="Jml")
        self.tree_detail.heading("Subtotal", text="Subtotal")
        self.tree_detail.column("Barang",   width=140, anchor="w")
        self.tree_detail.column("Jml",      width=40,  anchor="center")
        self.tree_detail.column("Subtotal", width=90,  anchor="e")

        sb_det = ttk.Scrollbar(detail_frame, orient="vertical", command=self.tree_detail.yview)
        self.tree_detail.configure(yscrollcommand=sb_det.set)
        sb_det.pack(side="right", fill="y")
        self.tree_detail.pack(fill="both", expand=True)

        # Total footer
        self.lbl_total = tk.Label(right_panel, text="Total: -",
                                   font=("Segoe UI", 11, "bold"),
                                   bg=LIGHT_GRAY, fg=PRIMARY, anchor="e")
        self.lbl_total.pack(fill="x", padx=12, pady=(4, 6))

        # Tombol aksi
        aksi_frame = tk.Frame(right_panel, bg=LIGHT_GRAY)
        aksi_frame.pack(fill="x", padx=8, pady=(0, 10))

        self.btn_terima = tk.Button(
            aksi_frame, text="✅  TERIMA", font=("Segoe UI", 11, "bold"),
            bg=ACCENT_G, fg=WHITE, relief="flat", pady=10, cursor="hand2",
            state="disabled", activebackground=ACCENT_G_DK, activeforeground=WHITE,
            command=self._terima_pesanan
        )
        self.btn_terima.pack(fill="x", pady=(0, 6))

        self.btn_tolak = tk.Button(
            aksi_frame, text="❌  TOLAK", font=("Segoe UI", 11, "bold"),
            bg=PRIMARY, fg=WHITE, relief="flat", pady=10, cursor="hand2",
            state="disabled", activebackground=PRIMARY_DK, activeforeground=WHITE,
            command=self._tolak_pesanan
        )
        self.btn_tolak.pack(fill="x")

    # ── Filter ────────────────────────────────────────────────────────────────
    def _set_filter(self, key: str, init: bool = False):
        self._filter_val = key
        for k, btn in self.filter_btns.items():
            if k == key:
                btn.config(bg=PRIMARY, fg=WHITE)
            else:
                btn.config(bg=LIGHT_GRAY, fg=DARK_TEXT)
        if not init:
            self._load_pesanan()

    # ── Data ──────────────────────────────────────────────────────────────────
    def _load_pesanan(self):
        self.selected_id = None
        self._clear_detail()
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            if self._filter_val == "semua":
                rows = execute_query(
                    "SELECT id_pesanan, tanggal, total_harga, status FROM pesanan ORDER BY tanggal DESC",
                    fetch=True
                )
            else:
                rows = execute_query(
                    "SELECT id_pesanan, tanggal, total_harga, status FROM pesanan WHERE status=%s ORDER BY tanggal DESC",
                    (self._filter_val,), fetch=True
                )
            for i, r in enumerate(rows):
                total = f"Rp {r['total_harga']:,.0f}"
                tag   = r["status"]
                self.tree.insert("", "end", iid=str(r["id_pesanan"]),
                                 values=(r["id_pesanan"], str(r["tanggal"])[:19],
                                         total, r["status"].upper()),
                                 tags=(tag, "alt" if i % 2 == 0 else ""))

            self.tree.tag_configure("pending",  foreground="#E65100")
            self.tree.tag_configure("diterima", foreground=ACCENT_G)
            self.tree.tag_configure("ditolak",  foreground=PRIMARY_DK)
            self.tree.tag_configure("alt",      background=ROW_ALT)
        except Exception as e:
            messagebox.showerror("Error DB", str(e))

    def _on_pesanan_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_id = int(sel[0])
        self._load_detail(self.selected_id)

    def _load_detail(self, id_pesanan: int):
        self._clear_detail()
        try:
            pesanan = execute_query(
                "SELECT * FROM pesanan WHERE id_pesanan=%s", (id_pesanan,), fetch=True
            )
            if not pesanan:
                return
            p = pesanan[0]
            status = p["status"]

            self.lbl_id.config(text=f"Pesanan #{p['id_pesanan']}")
            tgl    = str(p["tanggal"])[:19]
            total  = f"Rp {p['total_harga']:,.0f}"
            self.lbl_status.config(
                text=f"📅 {tgl}   |   Status: {status.upper()}",
                fg=STATUS_COLOR.get(status, GRAY_TEXT)
            )
            self.lbl_total.config(text=f"Total: {total}")

            # Aktifkan tombol hanya jika pending
            if status == "pending":
                self.btn_terima.config(state="normal")
                self.btn_tolak.config(state="normal")
            else:
                self.btn_terima.config(state="disabled")
                self.btn_tolak.config(state="disabled")

            # Detail items
            detail_rows = execute_query(
                """SELECT dp.jumlah, dp.subtotal, b.nama_barang
                   FROM detail_pesanan dp
                   JOIN barang b ON dp.id_barang = b.id_barang
                   WHERE dp.id_pesanan = %s""",
                (id_pesanan,), fetch=True
            )
            for dr in detail_rows:
                sub = f"Rp {dr['subtotal']:,.0f}"
                self.tree_detail.insert("", "end",
                                        values=(dr["nama_barang"], dr["jumlah"], sub))
        except Exception as e:
            messagebox.showerror("Error DB", str(e))

    def _clear_detail(self):
        for item in self.tree_detail.get_children():
            self.tree_detail.delete(item)
        self.lbl_id.config(text="Pilih pesanan →")
        self.lbl_status.config(text="", fg=GRAY_TEXT)
        self.lbl_total.config(text="Total: -")
        self.btn_terima.config(state="disabled")
        self.btn_tolak.config(state="disabled")

    # ── Aksi ──────────────────────────────────────────────────────────────────
    def _terima_pesanan(self):
        if not self.selected_id:
            return
        if not messagebox.askyesno("Konfirmasi",
                                    f"Terima pesanan #{self.selected_id}?\n\nStok barang akan dikurangi.",
                                    parent=self):
            return
        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Ambil detail pesanan
            cursor.execute(
                "SELECT id_barang, jumlah FROM detail_pesanan WHERE id_pesanan=%s",
                (self.selected_id,)
            )
            details = cursor.fetchall()

            # Cek stok cukup
            for d in details:
                cursor.execute("SELECT nama_barang, stok FROM barang WHERE id_barang=%s", (d["id_barang"],))
                barang = cursor.fetchone()
                if barang["stok"] < d["jumlah"]:
                    messagebox.showwarning(
                        "Stok Tidak Cukup",
                        f"Stok \"{barang['nama_barang']}\" tidak cukup!\n"
                        f"Tersedia: {barang['stok']}, Dibutuhkan: {d['jumlah']}",
                        parent=self
                    )
                    cursor.close()
                    conn.close()
                    return

            # Kurangi stok semua item
            for d in details:
                cursor.execute(
                    "UPDATE barang SET stok = stok - %s WHERE id_barang=%s",
                    (d["jumlah"], d["id_barang"])
                )

            # Update status pesanan
            cursor.execute(
                "UPDATE pesanan SET status='diterima' WHERE id_pesanan=%s",
                (self.selected_id,)
            )
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Berhasil",
                                f"✅ Pesanan #{self.selected_id} DITERIMA!\nStok berhasil dikurangi.",
                                parent=self)
            self._refresh()

        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _tolak_pesanan(self):
        if not self.selected_id:
            return
        if not messagebox.askyesno("Konfirmasi",
                                    f"Tolak pesanan #{self.selected_id}?\n\nStok tidak akan berubah.",
                                    parent=self):
            return
        try:
            execute_query(
                "UPDATE pesanan SET status='ditolak' WHERE id_pesanan=%s",
                (self.selected_id,)
            )
            messagebox.showinfo("Info",
                                f"❌ Pesanan #{self.selected_id} DITOLAK.",
                                parent=self)
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _refresh(self):
        self.selected_id = None
        self._clear_detail()
        self._load_pesanan()
