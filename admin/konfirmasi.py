"""
admin/konfirmasi.py - Panel Konfirmasi Pesanan (Terima / Tolak)
Aplikasi Business Center SMKN 13 Bandung
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
<<<<<<< HEAD
import pymysql.cursors
from db import execute_query, get_connection
from midtrans_webhook import reduce_stock
=======
from db import get_db
>>>>>>> 099d9731109ffb4053743896f150a6ec4c3aae72

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

PAY_COLOR = {
    "unpaid":  "#E65100",
    "pending": "#1565C0",
    "paid":    "#2E7D32",
    "failed":  "#B71C1C",
    "expired": "#757575",
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
                  cursor="hand2", command=self._refresh).pack(side="right", padx=4)
        tk.Button(hdr, text="🗑  Hapus Semua Histori", font=("Segoe UI", 9, "bold"),
                  bg="#B71C1C", fg=WHITE, relief="flat", padx=10, pady=5,
                  cursor="hand2", command=self._hapus_semua_histori).pack(side="right", padx=(16, 4))

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

        cols = ("ID", "Tanggal", "Total", "Status", "Pembayaran")
        self.tree = ttk.Treeview(left_panel, columns=cols,
                                  show="headings", style="Pesanan.Treeview")
        self.tree.heading("ID",         text="ID")
        self.tree.heading("Tanggal",    text="Tanggal & Jam")
        self.tree.heading("Total",      text="Total Harga")
        self.tree.heading("Status",     text="Status")
        self.tree.heading("Pembayaran", text="Pay. Status")

        self.tree.column("ID",         width=45,  anchor="center")
        self.tree.column("Tanggal",    width=145, anchor="center")
        self.tree.column("Total",      width=110, anchor="e")
        self.tree.column("Status",     width=80,  anchor="center")
        self.tree.column("Pembayaran", width=90,  anchor="center")

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
        self.lbl_total.pack(fill="x", padx=12, pady=(4, 2))

        # Info pembayaran Midtrans
        self.lbl_payment = tk.Label(right_panel, text="",
                                    font=("Segoe UI", 8),
                                    bg=LIGHT_GRAY, fg=GRAY_TEXT,
                                    anchor="w", justify="left", wraplength=280)
        self.lbl_payment.pack(fill="x", padx=12, pady=(0, 4))

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

        self.btn_confirm_cash = tk.Button(
            aksi_frame, text="💰 KONFIRMASI BAYAR CASH", font=("Segoe UI", 10, "bold"),
            bg="#2E7D32", fg=WHITE, relief="flat", pady=8, cursor="hand2",
            state="disabled", command=self._confirm_cash_manual
        )
        self.btn_confirm_cash.pack(fill="x", pady=(0, 10))
        self.btn_confirm_cash.pack_forget() # Sembunyi default

        self.btn_tolak = tk.Button(
            aksi_frame, text="❌  TOLAK", font=("Segoe UI", 11, "bold"),
            bg=PRIMARY, fg=WHITE, relief="flat", pady=10, cursor="hand2",
            state="disabled", activebackground=PRIMARY_DK, activeforeground=WHITE,
            command=self._tolak_pesanan
        )
        self.btn_tolak.pack(fill="x", pady=(0, 6))

        tk.Frame(aksi_frame, bg="#DDDDDD", height=1).pack(fill="x", pady=(4, 6))

        self.btn_hapus = tk.Button(
            aksi_frame, text="🗑  Hapus Pesanan Ini", font=("Segoe UI", 9, "bold"),
            bg="#37474F", fg=WHITE, relief="flat", pady=7, cursor="hand2",
            state="disabled", activebackground="#263238", activeforeground=WHITE,
            command=self._hapus_pesanan
        )
        self.btn_hapus.pack(fill="x")

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
<<<<<<< HEAD
            base_q = (
                "SELECT id_pesanan, tanggal, total_harga, status, "
                "payment_status, payment_method, nama_pembeli "
                "FROM pesanan"
            )
            if self._filter_val == "semua":
                rows = execute_query(base_q + " ORDER BY tanggal DESC", fetch=True)
            else:
                rows = execute_query(
                    base_q + " WHERE status=%s ORDER BY tanggal DESC",
                    (self._filter_val,), fetch=True
                )
            for i, r in enumerate(rows):
                total    = f"Rp {r['total_harga']:,.0f}"
                tag      = r["status"]
                pay_st   = (r.get("payment_status") or "unpaid").upper()
                self.tree.insert("", "end", iid=str(r["id_pesanan"]),
                                 values=(
                                     r["id_pesanan"],
                                     str(r["tanggal"])[:19],
                                     total,
                                     r["status"].upper(),
                                     pay_st,
                                 ),
=======
            from firebase_admin import firestore
            db = get_db()
            if self._filter_val == "semua":
                docs = db.collection('pesanan').order_by('tanggal', direction=firestore.Query.DESCENDING).stream()
            else:
                docs = db.collection('pesanan').where('status', '==', self._filter_val).order_by('tanggal', direction=firestore.Query.DESCENDING).stream()
                
            for i, doc in enumerate(docs):
                r = doc.to_dict()
                total = f"Rp {r.get('total_harga', 0):,.0f}"
                tag   = r.get("status", "")
                self.tree.insert("", "end", iid=doc.id,
                                 values=(doc.id[:8], str(r.get("tanggal", ""))[:19],
                                         total, tag.upper()),
>>>>>>> 099d9731109ffb4053743896f150a6ec4c3aae72
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
        self.selected_id = str(sel[0])
        self._load_detail(self.selected_id)

    def _load_detail(self, id_pesanan: str):
        self._clear_detail()
        try:
            db = get_db()
            doc = db.collection('pesanan').document(id_pesanan).get()
            if not doc.exists:
                return
<<<<<<< HEAD
            p = pesanan[0]
            status    = p["status"]
            pay_st    = p.get("payment_status") or "unpaid"
            pay_meth  = p.get("payment_method") or "-"
            tx_id     = p.get("transaction_id") or "-"
            nama_pmb  = p.get("nama_pembeli") or "-"

            self.lbl_id.config(text=f"Pesanan #{p['id_pesanan']}  |  {nama_pmb}")
            tgl   = str(p["tanggal"])[:19]
            total = f"Rp {p['total_harga']:,.0f}"
=======
            p = doc.to_dict()
            status = p.get("status", "")

            self.lbl_id.config(text=f"Pesanan #{id_pesanan[:8]}")
            tgl    = str(p.get("tanggal", ""))[:19]
            total  = f"Rp {p.get('total_harga', 0):,.0f}"
>>>>>>> 099d9731109ffb4053743896f150a6ec4c3aae72
            self.lbl_status.config(
                text=f"📅 {tgl}   |   Status: {status.upper()}",
                fg=STATUS_COLOR.get(status, GRAY_TEXT)
            )
            self.lbl_total.config(text=f"Total: {total}")

            # ── Info pembayaran Midtrans ──────────────────────────────────
            pay_clr = PAY_COLOR.get(pay_st, GRAY_TEXT)
            if hasattr(self, "lbl_payment"):
                self.lbl_payment.config(
                    text=f"💳 Pembayaran: {pay_st.upper()}  |  Metode: {pay_meth.upper()}\n"
                         f"🆔 Trans ID: {tx_id}",
                    fg=pay_clr
                )

            # Tombol Konfirmasi Cash
            if pay_meth.upper() == "CASH" and pay_st == "waiting_confirmation":
                self.btn_confirm_cash.pack(fill="x", pady=(0, 10), after=self.btn_terima)
                self.btn_confirm_cash.config(state="normal")
            else:
                self.btn_confirm_cash.pack_forget()

            # Aktifkan tombol sesuai status
            if status == "pending":
                self.btn_terima.config(state="normal")
                self.btn_tolak.config(state="normal")
                self.btn_hapus.config(state="disabled")
            else:
                self.btn_terima.config(state="disabled")
                self.btn_tolak.config(state="disabled")
                self.btn_hapus.config(state="normal")

            # Detail items
            detail_rows = p.get('detail_pesanan', [])
            for dr in detail_rows:
                sub = f"Rp {dr.get('subtotal', 0):,.0f}"
                self.tree_detail.insert("", "end",
                                        values=(dr.get("nama_barang", ""), dr.get("jumlah", 0), sub))
        except Exception as e:
            messagebox.showerror("Error DB", str(e))

    def _confirm_cash_manual(self):
        if not self.selected_id: return
        if messagebox.askyesno("Konfirmasi", f"Konfirmasi pembayaran CASH untuk Pesanan #{self.selected_id}?\n\nStatus akan berubah menjadi PAID dan stok akan dikurangi."):
            try:
                # Update status pembayaran
                execute_query(
                    "UPDATE pesanan SET payment_status='paid', status='diterima', confirmed_at=NOW() WHERE id_pesanan=%s",
                    (self.selected_id,)
                )
                # Kurangi stok
                reduce_stock(self.selected_id)
                messagebox.showinfo("Sukses", f"Pesanan #{self.selected_id} telah lunas (PAID).")
                self._load_pesanan()
                self._load_detail(self.selected_id)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _clear_detail(self):
        for item in self.tree_detail.get_children():
            self.tree_detail.delete(item)
        self.lbl_id.config(text="Pilih pesanan →")
        self.lbl_status.config(text="", fg=GRAY_TEXT)
        self.lbl_total.config(text="Total: -")
        if hasattr(self, "lbl_payment"):
            self.lbl_payment.config(text="", fg=GRAY_TEXT)
        self.btn_terima.config(state="disabled")
        self.btn_tolak.config(state="disabled")
        self.btn_hapus.config(state="disabled")

    # ── Aksi ──────────────────────────────────────────────────────────────────
    def _terima_pesanan(self):
        if not self.selected_id:
            return
        if not messagebox.askyesno("Konfirmasi",
                                    f"Terima pesanan #{self.selected_id}?\n\nStok barang akan dikurangi.",
                                    parent=self):
            return
        try:
            from firebase_admin import firestore
            db = get_db()
            doc_ref = db.collection('pesanan').document(self.selected_id)
            doc = doc_ref.get()
            if not doc.exists: return
            p = doc.to_dict()
            details = p.get('detail_pesanan', [])

            # Cek stok cukup
            for d in details:
                b_doc = db.collection('barang').document(d["id_barang"]).get()
                if not b_doc.exists: continue
                b = b_doc.to_dict()
                if b.get("stok", 0) < d["jumlah"]:
                    messagebox.showwarning(
                        "Stok Tidak Cukup",
                        f"Stok \"{b.get('nama_barang', '')}\" tidak cukup!\n"
                        f"Tersedia: {b.get('stok', 0)}, Dibutuhkan: {d['jumlah']}",
                        parent=self
                    )
                    return

            # Kurangi stok semua item dan update status
            batch = db.batch()
            for d in details:
                b_ref = db.collection('barang').document(d["id_barang"])
                batch.update(b_ref, {'stok': firestore.Increment(-d["jumlah"])})

            batch.update(doc_ref, {'status': 'diterima'})
            batch.commit()

            messagebox.showinfo("Berhasil",
                                f"✅ Pesanan #{self.selected_id[:8]} DITERIMA!\nStok berhasil dikurangi.",
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
            db = get_db()
            db.collection('pesanan').document(self.selected_id).update({'status': 'ditolak'})
            messagebox.showinfo("Info",
                                f"❌ Pesanan #{self.selected_id[:8]} DITOLAK.",
                                parent=self)
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _hapus_pesanan(self):
        """Hapus satu pesanan terpilih (hanya diterima/ditolak)."""
        if not self.selected_id:
            return
        if not messagebox.askyesno(
            "Hapus Pesanan",
            f"Hapus histori pesanan #{self.selected_id[:8]} secara permanen?",
            parent=self
        ):
            return
        try:
            db = get_db()
            db.collection('pesanan').document(self.selected_id).delete()
            
            messagebox.showinfo(
                "Berhasil",
                f"🗑  Pesanan #{self.selected_id[:8]} berhasil dihapus.",
                parent=self
            )
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _hapus_semua_histori(self):
        """Hapus semua pesanan berstatus diterima atau ditolak."""
        try:
            db = get_db()
            # Firestore tidak support query IN dengan stream secara langsung untuk delete massal yang efisien tanpa loop,
            # tapi kita bisa ambil ID-nya dulu.
            docs = db.collection('pesanan').where('status', 'in', ['diterima', 'ditolak']).stream()
            doc_ids = [d.id for d in docs]
            jumlah = len(doc_ids)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        if jumlah == 0:
            messagebox.showinfo(
                "Info",
                "Tidak ada histori yang bisa dihapus.\n(Pesanan pending tidak akan dihapus.)",
                parent=self
            )
            return

        if not messagebox.askyesno(
            "Hapus Semua Histori",
            f"Akan menghapus {jumlah} pesanan (diterima & ditolak) secara permanen.\n"
            "Pesanan berstatus PENDING tidak akan terpengaruh.\n\nLanjutkan?",
            parent=self
        ):
            return

        try:
            batch = db.batch()
            for did in doc_ids:
                batch.delete(db.collection('pesanan').document(did))
            batch.commit()

            messagebox.showinfo(
                "Berhasil",
                f"🗑  {jumlah} histori pesanan berhasil dihapus.",
                parent=self
            )
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _refresh(self):
        self.selected_id = None
        self._clear_detail()
        self._load_pesanan()
