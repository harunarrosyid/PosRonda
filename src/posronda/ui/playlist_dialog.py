"""
PosRonda Playlist Creator Dialog
Dialog interaktif untuk membuat Playlist baru di YouTube Channel secara langsung.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

class CreatePlaylistDialog(tk.Toplevel):
    def __init__(self, parent, yt_cfg, on_success_callback):
        super().__init__(parent)
        self.title("Buat Playlist YouTube Baru - PosRonda")
        self.configure(bg="#0b0f19")
        self.transient(parent)
        self.grab_set()

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 520, 340
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.resizable(False, False)

        self.yt_cfg = yt_cfg
        self.on_success = on_success_callback

        self._build_ui()

    def _build_ui(self):
        f_head = tk.Frame(self, bg="#1e1b4b", padx=16, pady=10)
        f_head.pack(fill="x")
        tk.Label(
            f_head,
            text="➕ Buat Playlist Baru di Channel YouTube",
            bg="#1e1b4b", fg="#818cf8",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")
        tk.Label(
            f_head,
            text="Playlist akan dibuat otomatis di YouTube Studio & langsung dipilih sebagai target arsip CCTV.",
            bg="#1e1b4b", fg="#94a3b8",
            font=("Segoe UI", 8)
        ).pack(anchor="w")

        f_body = tk.Frame(self, bg="#0b0f19", padx=16, pady=12)
        f_body.pack(fill="both", expand=True)

        # 1. Judul Playlist
        tk.Label(f_body, text="Judul Playlist (Playlist Title):", bg="#0b0f19", fg="#cbd5e1", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(2, 2))
        self.ent_pl_title = tk.Entry(
            f_body, font=("Segoe UI", 9),
            bg="#1e293b", fg="#ffffff", insertbackground="#38bdf8",
            relief="flat", highlightthickness=1, highlightbackground="#334155"
        )
        self.ent_pl_title.insert(0, "Arsip CCTV PosRonda 2026")
        self.ent_pl_title.pack(fill="x", pady=(0, 8))

        # 2. Deskripsi Playlist
        tk.Label(f_body, text="Deskripsi Playlist (Opsional):", bg="#0b0f19", fg="#cbd5e1", font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 2))
        self.ent_pl_desc = tk.Entry(
            f_body, font=("Segoe UI", 9),
            bg="#1e293b", fg="#ffffff", insertbackground="#38bdf8",
            relief="flat", highlightthickness=1, highlightbackground="#334155"
        )
        self.ent_pl_desc.insert(0, "Kompilasi arsip rekaman siaran CCTV PosRonda 24 jam.")
        self.ent_pl_desc.pack(fill="x", pady=(0, 8))

        # 3. Privasi
        tk.Label(f_body, text="Pengaturan Privasi (Privacy Status):", bg="#0b0f19", fg="#cbd5e1", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(2, 2))
        self.cmb_priv = ttk.Combobox(
            f_body,
            values=[
                "unlisted (Tidak Publik - Hanya pemilik link / Rekomendasi Utama)",
                "public (Publik - Terlihat di pencarian channel YouTube)",
                "private (Pribadi - Hanya akun Google ini)"
            ],
            state="readonly"
        )
        self.cmb_priv.set("unlisted (Tidak Publik - Hanya pemilik link / Rekomendasi Utama)")
        self.cmb_priv.pack(fill="x", pady=(0, 14))

        # Bottom Bar
        f_bot = tk.Frame(self, bg="#0f172a", padx=14, pady=10, highlightthickness=1, highlightbackground="#1e293b")
        f_bot.pack(side="bottom", fill="x")

        self.btn_submit = tk.Button(
            f_bot,
            text="💾 Simpan & Buat Playlist",
            bg="#0284c7", fg="#ffffff",
            activebackground="#0369a1", activeforeground="#ffffff",
            font=("Segoe UI", 8, "bold"),
            relief="flat", padx=12, pady=3,
            cursor="hand2",
            command=self.submit_create
        )
        self.btn_submit.pack(side="right", padx=(6, 0))

        btn_cancel = tk.Button(
            f_bot,
            text="Batal",
            bg="#334155", fg="#cbd5e1",
            activebackground="#475569", activeforeground="#ffffff",
            font=("Segoe UI", 8),
            relief="flat", padx=10, pady=3,
            cursor="hand2",
            command=self.destroy
        )
        btn_cancel.pack(side="right")

    def submit_create(self):
        title = self.ent_pl_title.get().strip()
        desc = self.ent_pl_desc.get().strip()
        priv_raw = self.cmb_priv.get()
        priv = "unlisted"
        if "public" in priv_raw:
            priv = "public"
        elif "private" in priv_raw:
            priv = "private"

        if not title:
            messagebox.showwarning("Judul Kosong", "Harap masukkan judul playlist!", parent=self)
            return

        self.btn_submit.config(text="⏳ Membuat di YouTube...", state="disabled")

        def run_create():
            try:
                try:
                    from posronda.network.youtube_manager import YouTubeManager
                except ImportError:
                    from youtube_manager import YouTubeManager

                yt = YouTubeManager(self.yt_cfg)
                ok, new_pl, err = yt.create_playlist(title, desc, priv)
                if ok and new_pl:
                    self.after(0, lambda: self._on_success(new_pl))
                else:
                    self.after(0, lambda: self._on_failure(err or "Gagal membuat playlist"))
            except Exception as e:
                import traceback
                self.after(0, lambda: self._on_failure(traceback.format_exc()))

        threading.Thread(target=run_create, daemon=True).start()

    def _on_success(self, new_pl):
        messagebox.showinfo(
            "Playlist Berhasil Dibuat",
            f"✔ Playlist YouTube Berhasil Dibuat!\n\n"
            f"• Judul: {new_pl['title']}\n"
            f"• ID: {new_pl['id']}\n"
            f"• Privasi: {new_pl['privacy'].title()}\n\n"
            f"Playlist ini telah otomatis dipilih sebagai target arsip rekaman CCTV.",
            parent=self
        )
        if self.on_success:
            self.on_success(new_pl)
        self.destroy()

    def _on_failure(self, err_text):
        self.btn_submit.config(text="💾 Simpan & Buat Playlist", state="normal")
        try:
            from posronda.ui.error_dialog import show_error_dialog
            show_error_dialog(
                self,
                "Gagal Membuat Playlist",
                "Terjadi kesalahan saat memproses pembuatan playlist melalui YouTube Data API.",
                error_details=err_text,
                action_url="https://studio.youtube.com",
                action_url_label="🌐 Buka YouTube Studio"
            )
        except Exception:
            messagebox.showerror("Gagal Membuat Playlist", str(err_text), parent=self)
