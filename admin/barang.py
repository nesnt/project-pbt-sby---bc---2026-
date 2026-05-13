"""
admin/barang.py - Panel Kelola Barang (CRUD) + Foto Produk
Aplikasi Business Center SMKN 13 Bandung
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import shutil

from db import execute_query, IMAGES_DIR

PRIMARY    = "#CC0000"
PRIMARY_DK = "#A00000"
WHITE      = "#FFFFFF"
LIGHT_GRAY = "#F5F5F5"
DARK_TEXT  = "#212121"
GRAY_TEXT  = "#757575"
ACCENT_G   = "#2E7D32"
ACCENT_G_DK= "#1B5E20"
ROW_ALT    = "#FFF5F5"


# ─── Helper validasi input ────────────────────────────────────────────────────
def _make_digit_validator(root):
    """Return (vcmd, 'key') untuk Entry agar hanya menerima digit."""
    def _validate(new_val):
        return new_val == "" or new_val.isdigit()
    vcmd = (root.register(_validate), "%P")
    return vcmd


def _apply_harga_x1000(entry: tk.Entry, preview_lbl: tk.Label = None):
    """FocusOut: ambil angka di entry, kalikan 1000, tulis kembali."""
    raw = entry.get().strip()
    if raw.isdigit() and raw != "":
        nilai = int(raw) * 1000
        entry.delete(0, "end")
        entry.insert(0, str(nilai))
        if preview_lbl:
            preview_lbl.config(text=f"= Rp {nilai:,.0f}")
    elif preview_lbl:
        preview_lbl.config(text="")


def _on_harga_keyrelease(entry: tk.Entry, preview_lbl: tk.Label):
    """KeyRelease: tampilkan preview × 1000 secara realtime."""
    raw = entry.get().strip()
    if raw.isdigit() and raw != "":
        preview_lbl.config(text=f"→ Rp {int(raw) * 1000:,.0f}")
    else:
        preview_lbl.config(text="")


def load_thumbnail(foto: str, size=(50, 50)):
    """Muat gambar produk sebagai PhotoImage. Return None jika tidak ada."""
    if not foto:
        return None
    path = os.path.join(IMAGES_DIR, foto)
    if not os.path.isfile(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img.thumbnail(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


class BarangPanel(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=LIGHT_GRAY)
        self.dashboard    = dashboard
        self.selected_id  = None
        self._thumb_refs  = {}   # simpan referensi agar tidak di-GC
        self._build()
        self._load_data()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=WHITE, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Kelola Barang", font=("Segoe UI", 15, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(side="left", padx=24, pady=14)
        tk.Button(hdr, text="+ Tambah Barang", font=("Segoe UI", 10, "bold"),
                  bg=ACCENT_G, fg=WHITE, relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._open_form_tambah).pack(side="right", padx=20, pady=12)
                  
        tk.Button(hdr, text="Update Cepat", font=("Segoe UI", 10, "bold"),
                  bg="#FF8F00", fg=WHITE, relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._open_form_update_cepat).pack(side="right", pady=12)

        # ── Search bar ────────────────────────────────────────────────────────
        sb = tk.Frame(self, bg=LIGHT_GRAY)
        sb.pack(fill="x", padx=20, pady=(10, 0))
        tk.Label(sb, text="Cari:", font=("Segoe UI", 10),
                 bg=LIGHT_GRAY, fg=DARK_TEXT).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter())
        tk.Entry(sb, textvariable=self.search_var,
                 font=("Segoe UI", 10), width=28, relief="solid", bd=1).pack(
                     side="left", padx=8, ipady=5)

        # ── Treeview ──────────────────────────────────────────────────────────
        table_frame = tk.Frame(self, bg=WHITE)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Barang.Treeview",
                        font=("Segoe UI", 10), rowheight=52,
                        background=WHITE, fieldbackground=WHITE, foreground=DARK_TEXT)
        style.configure("Barang.Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background=PRIMARY, foreground=WHITE, relief="flat")
        style.map("Barang.Treeview",
                  background=[("selected", "#FFD6D6")],
                  foreground=[("selected", DARK_TEXT)])

        cols = ("Nama Barang", "Harga", "Stok")
        self.tree = ttk.Treeview(table_frame, columns=cols,
                                  show="tree headings", style="Barang.Treeview")
        self.tree.heading("#0",         text="Foto")
        self.tree.heading("Nama Barang",text="Nama Barang")
        self.tree.heading("Harga",      text="Harga")
        self.tree.heading("Stok",       text="Stok")

        self.tree.column("#0",          width=65,  anchor="center", stretch=tk.NO)
        self.tree.column("Nama Barang", width=280, anchor="w")
        self.tree.column("Harga",       width=150, anchor="e")
        self.tree.column("Stok",        width=80,  anchor="center")

        sb2 = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── Action bar bawah ──────────────────────────────────────────────────
        act = tk.Frame(self, bg=WHITE)
        act.pack(fill="x", padx=20, pady=(0, 10))

        self.btn_edit = tk.Button(act, text="Edit Barang",
                                   font=("Segoe UI", 10, "bold"),
                                   bg="#1565C0", fg=WHITE, relief="flat",
                                   padx=14, pady=7, cursor="hand2",
                                   state="disabled", command=self._open_form_edit)
        self.btn_edit.pack(side="left", padx=(16, 8), pady=10)

        self.btn_hapus = tk.Button(act, text="Hapus Barang",
                                    font=("Segoe UI", 10, "bold"),
                                    bg=PRIMARY, fg=WHITE, relief="flat",
                                    padx=14, pady=7, cursor="hand2",
                                    state="disabled", command=self._hapus)
        self.btn_hapus.pack(side="left", pady=10)

        self.lbl_info = tk.Label(act, text="Pilih baris untuk edit/hapus",
                                  font=("Segoe UI", 9), bg=WHITE, fg=GRAY_TEXT)
        self.lbl_info.pack(side="right", padx=16)

    # ── Data ──────────────────────────────────────────────────────────────────
    def _load_data(self):
        self.all_data = []
        try:
            self.all_data = execute_query(
                "SELECT id_barang, nama_barang, harga_barang, stok, foto FROM barang ORDER BY id_barang",
                fetch=True
            )
        except Exception as e:
            messagebox.showerror("Error DB", str(e))
        self._render_table(self.all_data)

    def _render_table(self, data):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._thumb_refs.clear()

        for i, row in enumerate(data):
            thumb = load_thumbnail(row.get("foto"), size=(44, 44))
            harga = f"Rp {row['harga_barang']:,.0f}"
            tag   = "alt" if i % 2 == 0 else ""

            if thumb:
                self._thumb_refs[str(row["id_barang"])] = thumb
                self.tree.insert("", "end", iid=str(row["id_barang"]),
                                 image=thumb, text="",
                                 values=(row["nama_barang"], harga, row["stok"]),
                                 tags=(tag,))
            else:
                self.tree.insert("", "end", iid=str(row["id_barang"]),
                                 text="📦",
                                 values=(row["nama_barang"], harga, row["stok"]),
                                 tags=(tag,))

        self.tree.tag_configure("alt", background=ROW_ALT)

    def _filter(self):
        kw = self.search_var.get().lower()
        filtered = [r for r in self.all_data if kw in r["nama_barang"].lower()]
        self._render_table(filtered)

    def _on_select(self, _):
        sel = self.tree.selection()
        if sel:
            self.selected_id = int(sel[0])
            self.btn_edit.config(state="normal")
            self.btn_hapus.config(state="normal")
            nama = self.tree.item(sel[0])["values"][0]
            self.lbl_info.config(text=f"Dipilih: {nama}")
        else:
            self.selected_id = None
            self.btn_edit.config(state="disabled")
            self.btn_hapus.config(state="disabled")
            self.lbl_info.config(text="Pilih baris untuk edit/hapus")

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def _open_form_tambah(self):
        BarangForm(self, mode="tambah")

    def _open_form_edit(self):
        if not self.selected_id:
            return
        try:
            rows = execute_query("SELECT * FROM barang WHERE id_barang=%s",
                                 (self.selected_id,), fetch=True)
            if rows:
                BarangForm(self, mode="edit", data=rows[0])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_form_update_cepat(self):
        UpdateCepatForm(self)

    def _hapus(self):
        if not self.selected_id:
            return
        nama = self.tree.item(str(self.selected_id))["values"][0]
        if messagebox.askyesno("Hapus Barang", f"Yakin hapus barang:\n\"{nama}\"?", icon="warning"):
            try:
                execute_query("DELETE FROM barang WHERE id_barang=%s", (self.selected_id,))
                messagebox.showinfo("Berhasil", "Barang berhasil dihapus.")
                self.selected_id = None
                self._load_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def refresh(self):
        self.selected_id = None
        self._load_data()


# ─── Form Tambah / Edit Barang ────────────────────────────────────────────────
class BarangForm(tk.Toplevel):
    def __init__(self, panel: BarangPanel, mode: str, data: dict = None):
        super().__init__(panel)
        self.panel       = panel
        self.mode        = mode
        self.data        = data or {}
        self._foto_path  = None   # path file asli yang dipilih
        self._foto_nama  = self.data.get("foto") or None  # nama file di images/
        self._img_ref    = None   # simpan PhotoImage agar tidak GC

        title = "Tambah Barang" if mode == "tambah" else "Edit Barang"
        self.title(title)
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self._center(480, 520)
        self._build()
        self.grab_set()
        self.transient(panel)

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        title_text = "Tambah Barang Baru" if self.mode == "tambah" else "Edit Data Barang"
        hdr = tk.Frame(self, bg=PRIMARY, height=55)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=title_text, font=("Segoe UI", 12, "bold"),
                 bg=PRIMARY, fg=WHITE).pack(expand=True)

        body = tk.Frame(self, bg=WHITE, padx=28, pady=18)
        body.pack(fill="both", expand=True)

        # ── Field teks ────────────────────────────────────────────────────────
        vcmd = _make_digit_validator(self)

        # Nama Barang
        tk.Label(body, text="Nama Barang", font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(0, 2))
        self.entries = {}
        ent_nama = tk.Entry(body, font=("Segoe UI", 11), relief="solid", bd=1, bg=LIGHT_GRAY)
        ent_nama.pack(fill="x", ipady=7, pady=(0, 10))
        self.entries["nama"] = ent_nama

        # Harga — hanya angka + ×1000 saat focus out
        tk.Label(body, text="Harga (Rp)  ✦ ketik angka → otomatis ×1000",
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(0, 2))
        ent_harga = tk.Entry(body, font=("Segoe UI", 11), relief="solid", bd=1,
                             bg=LIGHT_GRAY, validate="key", validatecommand=vcmd)
        ent_harga.pack(fill="x", ipady=7, pady=(0, 2))
        self.entries["harga"] = ent_harga

        self.lbl_harga_preview = tk.Label(body, text="",
                                           font=("Segoe UI", 9, "italic"),
                                           bg=WHITE, fg="#1565C0", anchor="e")
        self.lbl_harga_preview.pack(fill="x", pady=(0, 8))

        ent_harga.bind("<KeyRelease>",
                       lambda e: _on_harga_keyrelease(ent_harga, self.lbl_harga_preview))
        ent_harga.bind("<FocusOut>",
                       lambda e: _apply_harga_x1000(ent_harga, self.lbl_harga_preview))

        # Stok — hanya angka
        tk.Label(body, text="Stok", font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(0, 2))
        ent_stok = tk.Entry(body, font=("Segoe UI", 11), relief="solid", bd=1,
                            bg=LIGHT_GRAY, validate="key", validatecommand=vcmd)
        ent_stok.pack(fill="x", ipady=7, pady=(0, 10))
        self.entries["stok"] = ent_stok

        if self.mode == "edit" and self.data:
            self.entries["nama"].insert(0,  self.data.get("nama_barang", ""))
            # Harga edit: tampilkan nilai asli (sudah dalam ribuan)
            harga_asli = str(int(self.data.get("harga_barang", 0)))
            self.entries["harga"].insert(0, harga_asli)
            self.lbl_harga_preview.config(text=f"= Rp {int(harga_asli):,.0f}")
            self.entries["stok"].insert(0,  str(self.data.get("stok", "")))

        # ── Foto ──────────────────────────────────────────────────────────────
        tk.Label(body, text="Foto Produk", font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(0, 4))

        foto_row = tk.Frame(body, bg=WHITE)
        foto_row.pack(fill="x", pady=(0, 12))

        # Preview box
        self.preview_frame = tk.Frame(foto_row, bg=LIGHT_GRAY, width=100, height=100,
                                       relief="solid", bd=1)
        self.preview_frame.pack(side="left")
        self.preview_frame.pack_propagate(False)

        self.lbl_preview = tk.Label(self.preview_frame, text="Belum ada\nfoto",
                                     font=("Segoe UI", 8), bg=LIGHT_GRAY, fg=GRAY_TEXT,
                                     justify="center")
        self.lbl_preview.place(relx=0.5, rely=0.5, anchor="center")

        # Tombol foto
        btn_col = tk.Frame(foto_row, bg=WHITE)
        btn_col.pack(side="left", padx=12, fill="y")

        tk.Button(btn_col, text="Pilih Foto",
                  font=("Segoe UI", 9, "bold"),
                  bg="#1565C0", fg=WHITE, relief="flat",
                  padx=12, pady=6, cursor="hand2",
                  command=self._pilih_foto).pack(pady=(8, 6))

        self.btn_hapus_foto = tk.Button(btn_col, text="Hapus Foto",
                                         font=("Segoe UI", 9),
                                         bg=LIGHT_GRAY, fg=PRIMARY, relief="flat",
                                         padx=12, pady=6, cursor="hand2",
                                         command=self._hapus_foto)
        self.btn_hapus_foto.pack()

        self.lbl_foto_nama = tk.Label(btn_col, text="Format: JPG, PNG, WEBP",
                                       font=("Segoe UI", 8), bg=WHITE, fg=GRAY_TEXT,
                                       justify="left")
        self.lbl_foto_nama.pack(pady=(6, 0))

        # Load preview jika edit dan sudah ada foto
        if self._foto_nama:
            self._show_preview_from_file(os.path.join(IMAGES_DIR, self._foto_nama))

        # ── Tombol aksi ───────────────────────────────────────────────────────
        btn_row = tk.Frame(body, bg=WHITE)
        btn_row.pack(fill="x", pady=(4, 0))

        tk.Button(btn_row, text="Batal", font=("Segoe UI", 10),
                  bg=LIGHT_GRAY, fg=DARK_TEXT, relief="flat", padx=14, pady=7,
                  cursor="hand2", command=self.destroy).pack(side="left")
        tk.Button(btn_row, text="Simpan", font=("Segoe UI", 10, "bold"),
                  bg=ACCENT_G, fg=WHITE, relief="flat", padx=14, pady=7,
                  cursor="hand2", command=self._simpan).pack(side="right")

        self.entries["nama"].focus()
        self.bind("<Return>", lambda e: self._simpan())

    # ── Foto helper ───────────────────────────────────────────────────────────
    def _pilih_foto(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Pilih Foto Produk",
            filetypes=[
                ("Gambar", "*.jpg *.jpeg *.png *.webp *.bmp *.gif"),
                ("Semua File", "*.*")
            ]
        )
        if not path:
            return
        self._foto_path = path
        ext  = os.path.splitext(path)[1].lower()
        nama = os.path.basename(path)
        self._foto_nama = nama
        self.lbl_foto_nama.config(text=nama[:28] + ("..." if len(nama) > 28 else ""))
        self._show_preview_from_file(path)

    def _show_preview_from_file(self, path: str):
        if not os.path.isfile(path):
            return
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((96, 96), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._img_ref = photo
            self.lbl_preview.config(image=photo, text="")
            self.lbl_preview.image = photo
        except Exception as e:
            self.lbl_foto_nama.config(text=f"Error: {e}")

    def _hapus_foto(self):
        self._foto_path = None
        self._foto_nama = None
        self._img_ref   = None
        self.lbl_preview.config(image="", text="Belum ada\nfoto")
        self.lbl_foto_nama.config(text="Format: JPG, PNG, WEBP")

    def _salin_foto_ke_images(self) -> str | None:
        """Salin foto yang dipilih ke folder images/, return nama file."""
        if not self._foto_path or not os.path.isfile(self._foto_path):
            return self._foto_nama  # kembalikan nama lama jika tidak ada pilihan baru

        ext  = os.path.splitext(self._foto_path)[1].lower()
        # Buat nama unik berdasarkan nama barang
        nama_barang = self.entries["nama"].get().strip().replace(" ", "_").lower()
        import time
        nama_file   = f"{nama_barang}_{int(time.time())}{ext}"
        dest        = os.path.join(IMAGES_DIR, nama_file)

        try:
            # Resize & simpan agar ukuran file kecil
            img = Image.open(self._foto_path).convert("RGB")
            img.thumbnail((600, 600), Image.LANCZOS)
            img.save(dest, quality=85)
            return nama_file
        except Exception:
            # Fallback: copy biasa jika gagal proses
            shutil.copy2(self._foto_path, dest)
            return nama_file

    # ── Simpan ────────────────────────────────────────────────────────────────
    def _simpan(self):
        # Pastikan harga sudah di-×1000 sebelum simpan
        _apply_harga_x1000(self.entries["harga"], self.lbl_harga_preview)

        nama  = self.entries["nama"].get().strip()
        harga = self.entries["harga"].get().strip()
        stok  = self.entries["stok"].get().strip()

        if not nama:
            messagebox.showwarning("Validasi", "Nama barang tidak boleh kosong!", parent=self)
            return
        try:
            harga_val = float(harga) if harga else 0.0
            stok_val  = int(stok)    if stok  else 0
            if harga_val < 0 or stok_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validasi", "Harga dan stok harus angka positif!", parent=self)
            return

        # Salin foto
        foto_file = self._salin_foto_ke_images()

        try:
            if self.mode == "tambah":
                execute_query(
                    "INSERT INTO barang (nama_barang, harga_barang, stok, foto) VALUES (%s,%s,%s,%s)",
                    (nama, harga_val, stok_val, foto_file)
                )
                messagebox.showinfo("Berhasil", "Barang berhasil ditambahkan!", parent=self)
            else:
                execute_query(
                    "UPDATE barang SET nama_barang=%s, harga_barang=%s, stok=%s, foto=%s WHERE id_barang=%s",
                    (nama, harga_val, stok_val, foto_file, self.data["id_barang"])
                )
                messagebox.showinfo("Berhasil", "Barang berhasil diperbarui!", parent=self)

            self.panel.refresh()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error DB", str(e), parent=self)

class UpdateCepatForm(tk.Toplevel):
    def __init__(self, panel: BarangPanel):
        super().__init__(panel)
        self.panel = panel
        self.all_barang = []
        self._foto_path = None
        self._foto_nama = None
        self._img_ref = None
        
        self.title("Update Cepat Stok & Foto")
        self.geometry("450x520")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self.transient(panel)
        self._center(450, 520)
        self._load_barang()
        self._build()
        self.grab_set()

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _load_barang(self):
        try:
            self.all_barang = execute_query("SELECT id_barang, nama_barang, foto FROM barang ORDER BY nama_barang", fetch=True)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _build(self):
        hdr = tk.Frame(self, bg="#FF8F00", height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Update Cepat (Stok & Foto)", font=("Segoe UI", 12, "bold"), bg="#FF8F00", fg=WHITE).pack(expand=True)

        body = tk.Frame(self, bg=WHITE, padx=20, pady=15)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Pilih Barang", font=("Segoe UI", 10, "bold"), bg=WHITE).pack(anchor="w")
        self.combo = ttk.Combobox(body, font=("Segoe UI", 11), state="readonly")
        
        self.combo["values"] = [f"[{b['id_barang']}] {b['nama_barang']}" for b in self.all_barang]
        self.combo.pack(fill="x", pady=(2, 15), ipady=5)
        self.combo.bind("<<ComboboxSelected>>", self._on_select_barang)

        tk.Label(body, text="Tambah Stok (opsional)", font=("Segoe UI", 10, "bold"), bg=WHITE).pack(anchor="w")
        vcmd_uc = _make_digit_validator(self)
        self.ent_stok = tk.Entry(body, font=("Segoe UI", 11), relief="solid", bd=1,
                                  bg=LIGHT_GRAY, validate="key", validatecommand=vcmd_uc)
        self.ent_stok.pack(fill="x", pady=(2, 15), ipady=7)

        tk.Label(body, text="Update Foto", font=("Segoe UI", 10, "bold"), bg=WHITE).pack(anchor="w", pady=(0, 4))

        foto_row = tk.Frame(body, bg=WHITE)
        foto_row.pack(fill="x", pady=(0, 15))

        self.preview_frame = tk.Frame(foto_row, bg=LIGHT_GRAY, width=100, height=100, relief="solid", bd=1)
        self.preview_frame.pack(side="left")
        self.preview_frame.pack_propagate(False)

        self.lbl_preview = tk.Label(self.preview_frame, text="Belum ada\nfoto", font=("Segoe UI", 8), bg=LIGHT_GRAY, fg=GRAY_TEXT, justify="center")
        self.lbl_preview.place(relx=0.5, rely=0.5, anchor="center")

        btn_col = tk.Frame(foto_row, bg=WHITE)
        btn_col.pack(side="left", padx=12, fill="y")
        tk.Button(btn_col, text="Pilih Foto", font=("Segoe UI", 9, "bold"), bg="#1565C0", fg=WHITE, relief="flat", padx=12, pady=6, cursor="hand2", command=self._pilih_foto).pack(pady=(8, 6))
        self.lbl_foto_nama = tk.Label(btn_col, text="", font=("Segoe UI", 8), bg=WHITE, fg=GRAY_TEXT, justify="left")
        self.lbl_foto_nama.pack(pady=(6, 0))

        btn_row = tk.Frame(body, bg=WHITE)
        btn_row.pack(fill="x", pady=(10, 0))
        tk.Button(btn_row, text="Batal", font=("Segoe UI", 10), bg=LIGHT_GRAY, fg=DARK_TEXT, relief="flat", padx=14, pady=7, cursor="hand2", command=self.destroy).pack(side="left")
        tk.Button(btn_row, text="Simpan Update", font=("Segoe UI", 10, "bold"), bg=ACCENT_G, fg=WHITE, relief="flat", padx=14, pady=7, cursor="hand2", command=self._simpan).pack(side="right")

    def _on_select_barang(self, _):
        idx = self.combo.current()
        if idx >= 0:
            b = self.all_barang[idx]
            self._foto_nama = b.get("foto")
            self._foto_path = None
            if self._foto_nama:
                self._show_preview_from_file(os.path.join(IMAGES_DIR, self._foto_nama))
            else:
                self.lbl_preview.config(image="", text="Belum ada\nfoto")
                self.lbl_foto_nama.config(text="Tidak ada foto.")

    def _pilih_foto(self):
        path = filedialog.askopenfilename(parent=self, title="Pilih Foto Baru", filetypes=[("Gambar", "*.jpg *.jpeg *.png *.webp *.bmp *.gif")])
        if not path: return
        self._foto_path = path
        nama = os.path.basename(path)
        self.lbl_foto_nama.config(text=nama)
        self._show_preview_from_file(path)

    def _show_preview_from_file(self, path: str):
        if not os.path.isfile(path): return
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((96, 96), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._img_ref = photo
            self.lbl_preview.config(image=photo, text="")
            self.lbl_preview.image = photo
        except Exception as e:
            self.lbl_foto_nama.config(text=f"Error: {e}")

    def _simpan(self):
        idx = self.combo.current()
        if idx < 0:
            messagebox.showwarning("Validasi", "Pilih barang terlebih dahulu!", parent=self)
            return

        b = self.all_barang[idx]
        id_b = b["id_barang"]
        
        tambah_stok = self.ent_stok.get().strip()
        stok_val = 0
        if tambah_stok:
            if not tambah_stok.isdigit() or int(tambah_stok) <= 0:
                messagebox.showwarning("Validasi", "Tambah stok harus angka positif!", parent=self)
                return
            stok_val = int(tambah_stok)

        new_foto = b.get("foto")
        if self._foto_path and os.path.isfile(self._foto_path):
            import time
            ext = os.path.splitext(self._foto_path)[1].lower()
            nama_file = f"update_{id_b}_{int(time.time())}{ext}"
            dest = os.path.join(IMAGES_DIR, nama_file)
            try:
                img = Image.open(self._foto_path).convert("RGB")
                img.thumbnail((600, 600), Image.LANCZOS)
                img.save(dest, quality=85)
                new_foto = nama_file
            except Exception:
                shutil.copy2(self._foto_path, dest)
                new_foto = nama_file

        try:
            query = "UPDATE barang SET foto=%s"
            params = [new_foto]
            if stok_val > 0:
                query += ", stok = stok + %s"
                params.append(stok_val)
                
            query += " WHERE id_barang=%s"
            params.append(id_b)
            
            execute_query(query, tuple(params))
            messagebox.showinfo("Berhasil", "Data berhasil diupdate!", parent=self)
            self.panel.refresh()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error DB", str(e), parent=self)
