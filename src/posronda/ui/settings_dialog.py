"""
PosRonda Settings Dialog GUI
Panel Pengaturan Profesional & Auto-Discovery CCTV Ramah Pengguna Awam
Mendukung:
1. Pindai Kamera Otomatis (Cukup Masukkan Username & Password CCTV)
2. Manajemen Multi-Slot Kamera (4, 8, 12, hingga 16 Kamera)
3. Mode Patrol / Tour (Rotasi Otomatis Halaman Kamera Super Ringan di X230)
4. Multi-Target Siaran & Penyimpanan:
   - YouTube Live (Free Cloud Storage untuk Siskamling / Warga)
   - Private Media Server / Custom RTMP (Untuk Klien Bonafide - MediaMTX, SRS, NGINX, VPS)
   - Perekaman Lokal HDD / NAS Mandiri (Tanpa Internet / Keamanan Tinggi + Auto-Prune)
5. Hardware Engine X230 (Intel QuickSync GPU QSV & x264)
6. Teks OSD & Watermark
7. Notifikasi Telegram Bot
8. Lisensi Semi Open-Source Model WinRAR (Community & PRO Edition)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import requests
import threading
import time
import re

try:
    from posronda.network import onvif_scanner
    from posronda.core import config_manager
    from posronda.core.license_manager import LicenseManager
except ImportError:
    import onvif_scanner
    import config_manager
    from license_manager import LicenseManager

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, config, on_save_callback):
        super().__init__(parent)
        self.title("Pengaturan PosRonda v4.0 - Surveillance Hub Control Center")
        self.geometry("850x740")
        self.minsize(800, 700)
        self.configure(bg="#0b0f19")
        self.transient(parent)
        self.grab_set()

        self.cfg = config
        self.on_save = on_save_callback
        self.pwd_visible = False
        self.stream_key_visible = False
        self.scanned_cams = []
        self.cam_entries = []

        self.create_widgets()

    def create_widgets(self):
        # 1. Top Header Bar
        header = tk.Frame(self, bg="#0f172a", padx=16, pady=12, highlightthickness=1, highlightbackground="#1e293b")
        header.pack(fill="x")

        f_title = tk.Frame(header, bg="#0f172a")
        f_title.pack(side="left")

        lbl_app = tk.Label(
            f_title, 
            text="🛡️ PosRonda v4.0", 
            bg="#1e1b4b", fg="#818cf8", 
            font=("Segoe UI", 11, "bold"), 
            padx=8, pady=2
        )
        lbl_app.pack(side="left", padx=(0, 10))

        lbl_sub = tk.Label(
            f_title, 
            text="Pusat Konfigurasi Multi-Kamera, Private Media Server & Local Recording", 
            bg="#0f172a", fg="#94a3b8", 
            font=("Segoe UI", 9)
        )
        lbl_sub.pack(side="left")

        # License Pill on Header
        lic_info = LicenseManager.get_license_info()
        pill_bg = "#064e3b" if lic_info.get("is_pro") else "#1e293b"
        pill_fg = "#34d399" if lic_info.get("is_pro") else "#cbd5e1"
        lbl_lic_pill = tk.Label(
            header,
            text=f"● {lic_info.get('tier_name')}",
            bg=pill_bg, fg=pill_fg,
            font=("Segoe UI", 8, "bold"),
            padx=8, pady=3
        )
        lbl_lic_pill.pack(side="right")

        # 2. Notebook Styling (Modern Tabs)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#0b0f19", borderwidth=0)
        style.configure(
            "TNotebook.Tab", 
            background="#1e293b", 
            foreground="#cbd5e1", 
            padding=[14, 7], 
            font=("Segoe UI", 9, "bold"),
            borderwidth=0
        )
        style.map(
            "TNotebook.Tab", 
            background=[("selected", "#0284c7")], 
            foreground=[("selected", "#ffffff")]
        )

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=14, pady=10)

        # Tab 1: Kamera CCTV (Auto-Scan & Patrol)
        tab_cam = tk.Frame(notebook, bg="#0f172a", padx=16, pady=14)
        notebook.add(tab_cam, text="📷 Kamera & Patrol")
        self.build_cam_tab(tab_cam)

        # Tab 2: Server & Tujuan Siaran (YouTube / Private RTMP / Local NAS)
        tab_server = tk.Frame(notebook, bg="#0f172a", padx=16, pady=14)
        notebook.add(tab_server, text="🎯 Server & Siaran")
        self.build_server_tab(tab_server)

        # Tab 3: Kinerja & Hardware X230
        tab_perf = tk.Frame(notebook, bg="#0f172a", padx=16, pady=14)
        notebook.add(tab_perf, text="⚡ Kinerja Hardware")
        self.build_perf_tab(tab_perf)

        # Tab 4: Teks OSD & Layar
        tab_osd = tk.Frame(notebook, bg="#0f172a", padx=16, pady=14)
        notebook.add(tab_osd, text="✍️ OSD & Teks")
        self.build_osd_tab(tab_osd)

        # Tab 5: Notifikasi Telegram
        tab_tg = tk.Frame(notebook, bg="#0f172a", padx=16, pady=14)
        notebook.add(tab_tg, text="✈ Telegram")
        self.build_tg_tab(tab_tg)

        # Tab 6: Lisensi & Model WinRAR
        tab_lic = tk.Frame(notebook, bg="#0f172a", padx=16, pady=14)
        notebook.add(tab_lic, text="💎 Lisensi (WinRAR)")
        self.build_license_tab(tab_lic)

        # 3. Bottom Action Bar
        bottom_bar = tk.Frame(self, bg="#0b0f19", padx=16, pady=10)
        bottom_bar.pack(fill="x")

        lbl_esc_hint = tk.Label(
            bottom_bar,
            text="PosRonda Hub v4.0 • Autonomous Multi-Camera & Private Stream Engine",
            bg="#0b0f19", fg="#64748b", font=("Segoe UI", 8)
        )
        lbl_esc_hint.pack(side="left")

        btn_save = tk.Button(
            bottom_bar, 
            text="💾 Simpan & Terapkan Pengaturan", 
            bg="#059669", 
            fg="#ffffff", 
            activebackground="#10b981",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat", 
            padx=18, pady=7,
            cursor="hand2",
            command=self.save_all
        )
        btn_save.pack(side="right", padx=5)

        btn_cancel = tk.Button(
            bottom_bar, 
            text="Batal", 
            bg="#334155", 
            fg="#e2e8f0", 
            activebackground="#475569",
            activeforeground="#ffffff",
            font=("Segoe UI", 9),
            relief="flat", 
            padx=14, pady=7,
            cursor="hand2",
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=5)

    def build_cam_tab(self, parent):
        canvas = tk.Canvas(parent, bg="#0f172a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#0f172a")

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=780)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- CARD 1: Deteksi Kamera Otomatis Ramah Orang Awam ---
        card_scan = tk.Frame(scroll_frame, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        card_scan.pack(fill="x", pady=(0, 10))

        tk.Label(
            card_scan,
            text="🔍 Pindai & Sambungkan Kamera Otomatis (Untuk Pengguna Awam)",
            bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            card_scan,
            text="Cukup masukkan Username & Password kamera Anda, lalu klik tombol di bawah.\n"
                 "PosRonda akan melacak sinyal ONVIF & port RTSP di seluruh jaringan Wi-Fi/LAN Anda secara otomatis.",
            bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 8), justify="left"
        ).pack(anchor="w", pady=(2, 8))

        f_cred_row = tk.Frame(card_scan, bg="#1e293b")
        f_cred_row.pack(fill="x", pady=4)

        cams = self.cfg.get("cameras", [])
        def_user = self.cfg.get("default_camera_credentials", {}).get("username", "admin")
        def_pwd = self.cfg.get("default_camera_credentials", {}).get("password", "")
        def_port = str(self.cfg.get("default_camera_credentials", {}).get("default_port", 554))

        if not def_pwd and cams and cams[0].get("rtsp_url"):
            u, p, port, _ = onvif_scanner.extract_credentials_and_path(cams[0].get("rtsp_url"))
            if u: def_user = u
            if p: def_pwd = p
            if port: def_port = str(port)

        tk.Label(f_cred_row, text="Username:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.ent_cam_user = tk.Entry(f_cred_row, font=("Segoe UI", 9), width=12, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_cam_user.insert(0, def_user)
        self.ent_cam_user.pack(side="left", padx=(4, 12))

        tk.Label(f_cred_row, text="Password:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.ent_cam_pwd = tk.Entry(f_cred_row, font=("Segoe UI", 9), width=14, show="*", bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_cam_pwd.insert(0, def_pwd)
        self.ent_cam_pwd.pack(side="left", padx=(4, 4))

        self.btn_toggle_pwd = tk.Button(
            f_cred_row, text="👁️", bg="#334155", fg="#cbd5e1", relief="flat", font=("Segoe UI", 8),
            command=self.toggle_cam_password_visibility
        )
        self.btn_toggle_pwd.pack(side="left", padx=(0, 12))

        tk.Label(f_cred_row, text="Port RTSP:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9)).pack(side="left")
        self.ent_cam_port = tk.Entry(f_cred_row, font=("Segoe UI", 9), width=6, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_cam_port.insert(0, def_port)
        self.ent_cam_port.pack(side="left", padx=(4, 8))

        f_btn_scan = tk.Frame(card_scan, bg="#1e293b")
        f_btn_scan.pack(fill="x", pady=(10, 4))

        self.btn_auto_connect = tk.Button(
            f_btn_scan,
            text="🔍 PINDAI JARINGAN & SAMBUNGKAN SEMUA KAMERA OTOMATIS",
            bg="#0284c7", fg="#ffffff",
            activebackground="#0369a1", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=12, pady=6,
            cursor="hand2",
            command=self.run_auto_scan_and_connect
        )
        self.btn_auto_connect.pack(side="left", padx=(0, 8))

        self.lbl_scan_indicator = tk.Label(
            card_scan,
            text="Tekan tombol di atas untuk melacak seluruh kamera CCTV di jaringan lokal Anda.",
            bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 8)
        )
        self.lbl_scan_indicator.pack(anchor="w", pady=(4, 0))

        # --- CARD 2: Mode Patrol / Rotasi Halaman Kamera (> 4 Kamera) ---
        card_patrol = tk.Frame(scroll_frame, bg="#1e293b", padx=14, pady=10, highlightthickness=1, highlightbackground="#334155")
        card_patrol.pack(fill="x", pady=(0, 10))

        f_pat_top = tk.Frame(card_patrol, bg="#1e293b")
        f_pat_top.pack(fill="x")

        self.var_patrol_enabled = tk.BooleanVar(value=self.cfg.get("patrol", {}).get("enabled", False))
        chk_patrol = tk.Checkbutton(
            f_pat_top,
            text="🔄 Aktifkan Mode Patrol / Rotasi Halaman Kamera Otomatis (> 4 Kamera)",
            variable=self.var_patrol_enabled,
            bg="#1e293b", fg="#ffffff", selectcolor="#0f172a",
            activebackground="#1e293b", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold")
        )
        chk_patrol.pack(side="left")

        f_pat_opts = tk.Frame(card_patrol, bg="#1e293b")
        f_pat_opts.pack(fill="x", pady=(6, 2))

        tk.Label(f_pat_opts, text="Interval Rotasi:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8)).pack(side="left")
        self.cmb_patrol_interval = ttk.Combobox(
            f_pat_opts,
            values=["10 Detik", "15 Detik (Direkomendasikan)", "20 Detik", "30 Detik", "60 Detik"],
            state="readonly", width=22
        )
        cur_int = self.cfg.get("patrol", {}).get("interval_seconds", 15)
        self.cmb_patrol_interval.set(f"{cur_int} Detik" if cur_int != 15 else "15 Detik (Direkomendasikan)")
        self.cmb_patrol_interval.pack(side="left", padx=(4, 16))

        tk.Label(f_pat_opts, text="Tata Letak Layar:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8)).pack(side="left")
        self.cmb_patrol_layout = ttk.Combobox(
            f_pat_opts,
            values=["2x2 (4 Kamera per Halaman - Sangat Ringan)", "3x3 (9 Kamera Sekaligus)"],
            state="readonly", width=32
        )
        cur_lay = self.cfg.get("patrol", {}).get("layout", "2x2")
        self.cmb_patrol_layout.set("3x3 (9 Kamera Sekaligus)" if cur_lay == "3x3" else "2x2 (4 Kamera per Halaman - Sangat Ringan)")
        self.cmb_patrol_layout.pack(side="left", padx=4)

        lbl_pat_hint = tk.Label(
            card_patrol,
            text="💡 Sangat menghemat CPU/GPU! Jika punya 8 kamera, layar akan menampilkan Cam 1-4 lalu berganti ke Cam 5-8.\n"
                 "   Anda juga bisa berpindah halaman secara manual dengan menekan tombol [Spasi] atau [Tab] di keyboard.",
            bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 8), justify="left"
        )
        lbl_pat_hint.pack(anchor="w", pady=(4, 0))

        # --- CARD 3: Daftar Slot Kamera ---
        f_slots_head = tk.Frame(scroll_frame, bg="#0f172a")
        f_slots_head.pack(fill="x", pady=(4, 4))

        tk.Label(
            f_slots_head,
            text="📺 Slot Kamera CCTV PosRonda",
            bg="#0f172a", fg="#f8fafc", font=("Segoe UI", 10, "bold")
        ).pack(side="left")

        btn_add_slot = tk.Button(
            f_slots_head,
            text="➕ Tambah Slot Kamera",
            bg="#1e293b", fg="#38bdf8",
            activebackground="#0284c7", activeforeground="#ffffff",
            font=("Segoe UI", 8, "bold"), relief="flat", padx=8, pady=2,
            cursor="hand2", command=self.add_new_slot_ui
        )
        btn_add_slot.pack(side="right")

        self.f_slots_container = tk.Frame(scroll_frame, bg="#0f172a")
        self.f_slots_container.pack(fill="x")

        self.cam_entries = []
        cams_to_load = cams if cams else [{"name": f"Kamera {i+1}", "rtsp_url": ""} for i in range(4)]
        if len(cams_to_load) < 4:
            while len(cams_to_load) < 4:
                cams_to_load.append({"name": f"Kamera {len(cams_to_load)+1}", "rtsp_url": ""})

        for i, cam_data in enumerate(cams_to_load):
            self._create_single_slot_card(i, cam_data)

        # --- CARD 4: Hasil Deteksi Jaringan Lokal ---
        self.f_discovered_card = tk.Frame(scroll_frame, bg="#1e293b", padx=12, pady=10, highlightthickness=1, highlightbackground="#334155")
        self.f_discovered_card.pack(fill="x", pady=(10, 5))

        tk.Label(
            self.f_discovered_card,
            text="📡 Hasil Deteksi Kamera di Jaringan Lokal (Wi-Fi / LAN)",
            bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        self.f_discovered_list = tk.Frame(self.f_discovered_card, bg="#0f172a", padx=8, pady=6)
        self.f_discovered_list.pack(fill="x", pady=6)

        self.lbl_disc_status = tk.Label(
            self.f_discovered_list,
            text="Daftar kamera hasil scan akan muncul di sini. Anda bisa memasangkan ke Slot yang diinginkan.",
            bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 8)
        )
        self.lbl_disc_status.pack(anchor="w")

    def _create_single_slot_card(self, idx, cam_data):
        f_slot = tk.Frame(self.f_slots_container, bg="#1e293b", padx=10, pady=6, highlightthickness=1, highlightbackground="#334155")
        f_slot.pack(fill="x", pady=3)

        f_top = tk.Frame(f_slot, bg="#1e293b")
        f_top.pack(fill="x", pady=(0, 3))

        lbl_badge = tk.Label(
            f_top, 
            text=f"SLOT {idx+1:02d}", 
            bg="#312e81", fg="#a5b4fc", 
            font=("Segoe UI", 8, "bold"), 
            padx=6, pady=1
        )
        lbl_badge.pack(side="left", padx=(0, 8))

        tk.Label(f_top, text="Nama:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8)).pack(side="left")
        ent_name = tk.Entry(f_top, font=("Segoe UI", 8), width=22, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        ent_name.insert(0, cam_data.get("name", f"Kamera {idx+1}"))
        ent_name.pack(side="left", padx=(4, 10))

        btn_test_single = tk.Button(
            f_top,
            text="🧪 Uji Kamera",
            bg="#334155", fg="#38bdf8",
            activebackground="#475569", activeforeground="#ffffff",
            relief="flat", font=("Segoe UI", 7),
            padx=5, pady=1, cursor="hand2",
            command=lambda i=idx: self.test_single_camera(i)
        )
        btn_test_single.pack(side="left", padx=3)

        btn_clear = tk.Button(
            f_top,
            text="✖ Kosongkan",
            bg="#334155", fg="#f87171",
            activebackground="#475569", activeforeground="#ffffff",
            relief="flat", font=("Segoe UI", 7),
            padx=5, pady=1, cursor="hand2",
            command=lambda i=idx: self.clear_slot(i)
        )
        btn_clear.pack(side="left", padx=3)

        f_bottom = tk.Frame(f_slot, bg="#1e293b")
        f_bottom.pack(fill="x")

        tk.Label(f_bottom, text="RTSP URL:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8), width=10, anchor="w").pack(side="left")
        ent_url = tk.Entry(f_bottom, font=("Segoe UI", 8), bg="#0f172a", fg="#38bdf8", insertbackground="#38bdf8")
        ent_url.insert(0, cam_data.get("rtsp_url", ""))
        ent_url.pack(side="left", fill="x", expand=True, padx=4)

        self.cam_entries.append((ent_name, ent_url))

    def add_new_slot_ui(self):
        new_idx = len(self.cam_entries)
        if new_idx >= 16:
            messagebox.showinfo("Batas Maksimal", "Maksimal 16 slot kamera telah tercapai.", parent=self)
            return
        self._create_single_slot_card(new_idx, {"name": f"Kamera {new_idx+1}", "rtsp_url": ""})
        self.lbl_scan_indicator.config(text=f"✔ Slot {new_idx+1} berhasil ditambahkan!", fg="#4ade80")

    def toggle_cam_password_visibility(self):
        self.pwd_visible = not self.pwd_visible
        if self.pwd_visible:
            self.ent_cam_pwd.config(show="")
            self.btn_toggle_pwd.config(text="🙈")
        else:
            self.ent_cam_pwd.config(show="*")
            self.btn_toggle_pwd.config(text="👁️")

    def toggle_stream_key_visibility(self):
        self.stream_key_visible = not self.stream_key_visible
        if self.stream_key_visible:
            self.ent_stream_key.config(show="")
            self.btn_toggle_key.config(text="🙈")
        else:
            self.ent_stream_key.config(show="*")
            self.btn_toggle_key.config(text="👁️")

    def clear_slot(self, idx):
        if idx < len(self.cam_entries):
            ent_name, ent_url = self.cam_entries[idx]
            ent_url.delete(0, tk.END)
            self.lbl_scan_indicator.config(text=f"Slot {idx+1} berhasil dikosongkan.", fg="#f59e0b")

    def test_single_camera(self, idx):
        if idx >= len(self.cam_entries):
            return
        ent_name, ent_url = self.cam_entries[idx]
        url = ent_url.get().strip()
        cam_label = ent_name.get().strip() or f"Kamera {idx+1}"

        if not url:
            messagebox.showwarning("URL Kosong", f"Slot {cam_label} belum memiliki RTSP URL!", parent=self)
            return

        self.lbl_scan_indicator.config(text=f"⏳ Menguji sinyal ke {cam_label} ({url})...", fg="#38bdf8")

        def _do_test():
            ip = onvif_scanner.extract_ip(url)
            user, pwd, port, path = onvif_scanner.extract_credentials_and_path(url)
            ok, msg = onvif_scanner.probe_rtsp_path(ip, port, path, user, pwd, timeout=1.5)
            
            def _finish():
                if ok:
                    self.lbl_scan_indicator.config(text=f"✔ {cam_label} Berhasil Terhubung! Sinyal kamera aktif.", fg="#4ade80")
                    messagebox.showinfo("Tes Koneksi Sukses", f"✔ Sinyal {cam_label} DITEMUKAN & AKTIF!\n\nURL: {url}\nRespon: {msg}", parent=self)
                else:
                    self.lbl_scan_indicator.config(text=f"✖ {cam_label} Gagal: Kamera tidak merespons ({msg})", fg="#f87171")
                    messagebox.showerror("Gagal Terhubung", f"✖ Gagal menghubungi {cam_label}!\n\nURL: {url}\nStatus: {msg}", parent=self)
            self.after(0, _finish)

        threading.Thread(target=_do_test, daemon=True).start()

    def run_auto_scan_and_connect(self):
        user = self.ent_cam_user.get().strip()
        pwd = self.ent_cam_pwd.get().strip()
        try:
            port = int(self.ent_cam_port.get().strip())
        except Exception:
            port = 554

        self.btn_auto_connect.config(state="disabled", text="⏳ MEMINDAI ONVIF & JARINGAN...")
        self.lbl_scan_indicator.config(text="Sedang mengirim probe ONVIF WS-Discovery & memindai seluruh subnet lokal...", fg="#38bdf8")

        def _scan_thread():
            try:
                cams = onvif_scanner.scan_all_cameras(username=user, password=pwd, default_port=port, probe=True)
                
                def _on_done():
                    self.btn_auto_connect.config(state="normal", text="🔍 PINDAI JARINGAN & SAMBUNGKAN SEMUA KAMERA OTOMATIS")
                    self.scanned_cams = cams
                    self.render_discovered_cams(cams)

                    if not cams:
                        self.lbl_scan_indicator.config(
                            text="✖ Tidak ditemukan kamera CCTV dengan port RTSP/ONVIF aktif di jaringan ini.",
                            fg="#f87171"
                        )
                        messagebox.showwarning(
                            "Kamera Tidak Ditemukan",
                            "Tidak ditemukan kamera CCTV di jaringan Wi-Fi/LAN lokal Anda.\n\n"
                            "Tips:\n1. Pastikan laptop & CCTV satu jaringan Wi-Fi/router.\n2. Pastikan port RTSP kamera terbuka.",
                            parent=self
                        )
                        return

                    # Otomatis tambah slot jika kamera yang ditemukan melebihi slot yang ada
                    while len(self.cam_entries) < len(cams) and len(self.cam_entries) < 16:
                        self.add_new_slot_ui()

                    limit = min(len(self.cam_entries), len(cams))
                    for i in range(limit):
                        cam = cams[i]
                        ent_name, ent_url = self.cam_entries[i]
                        ent_name.delete(0, tk.END)
                        ent_name.insert(0, f"Kamera {i+1} ({cam['ip']})")
                        ent_url.delete(0, tk.END)
                        ent_url.insert(0, cam["primary_url"])

                    self.lbl_scan_indicator.config(
                        text=f"✔ Sukses! Ditemukan {len(cams)} kamera CCTV. {limit} kamera langsung dipasangkan ke Slot 1-{limit}!",
                        fg="#4ade80"
                    )
                    messagebox.showinfo(
                        "Kamera Berhasil Dipasang",
                        f"✔ Berhasil mendeteksi {len(cams)} kamera CCTV di jaringan!\n\n"
                        f"Slot 1 sampai {limit} telah otomatis diisi dengan RTSP URL terotentikasi.",
                        parent=self
                    )

                self.after(0, _on_done)
            except Exception as e:
                def _on_err(err=str(e)):
                    self.btn_auto_connect.config(state="normal", text="🔍 PINDAI JARINGAN & SAMBUNGKAN SEMUA KAMERA OTOMATIS")
                    self.lbl_scan_indicator.config(text=f"Error saat scan: {err}", fg="#f87171")
                    messagebox.showerror("Error Scan", f"Terjadi kesalahan saat memindai: {err}", parent=self)
                self.after(0, _on_err)

        threading.Thread(target=_scan_thread, daemon=True).start()

    def render_discovered_cams(self, cams):
        for w in self.f_discovered_list.winfo_children():
            w.destroy()

        if not cams:
            tk.Label(self.f_discovered_list, text="Tidak ada kamera yang terdeteksi.", bg="#0f172a", fg="#f87171", font=("Segoe UI", 8)).pack(anchor="w")
            return

        for i, cam in enumerate(cams):
            ip = cam["ip"]
            name = cam.get("name", f"Kamera {ip}")
            verified_tag = "✔ Tervalidasi" if cam.get("verified") else "RTSP Terbuka"
            
            row = tk.Frame(self.f_discovered_list, bg="#0f172a", pady=2)
            row.pack(fill="x")

            lbl_info = tk.Label(
                row, 
                text=f"{i+1}. {ip} • {name} [{verified_tag}]", 
                bg="#0f172a", fg="#f1f5f9", 
                font=("Segoe UI", 8, "bold"), 
                width=34, anchor="w"
            )
            lbl_info.pack(side="left")

            max_show = min(len(self.cam_entries), 8)
            for slot_idx in range(max_show):
                btn_slot = tk.Button(
                    row, 
                    text=f"➜ C{slot_idx+1}", 
                    bg="#1e293b", fg="#38bdf8", 
                    activebackground="#0284c7", activeforeground="#ffffff",
                    font=("Segoe UI", 7), relief="flat", padx=3,
                    command=lambda s=slot_idx, c=cam: self.assign_cam_to_slot(s, c)
                )
                btn_slot.pack(side="left", padx=1)

    def assign_cam_to_slot(self, slot_idx, cam):
        if slot_idx < len(self.cam_entries):
            ent_name, ent_url = self.cam_entries[slot_idx]
            ent_name.delete(0, tk.END)
            ent_name.insert(0, f"Kamera {slot_idx+1} ({cam['ip']})")
            ent_url.delete(0, tk.END)
            ent_url.insert(0, cam["primary_url"])
            self.lbl_scan_indicator.config(
                text=f"✔ Kamera {cam['ip']} dipasangkan ke Slot {slot_idx+1}!",
                fg="#4ade80"
            )

    # --- TAB 2: SERVER & TUJUAN SIARAN (YouTube / Private RTMP / Local Recording) ---
    def build_server_tab(self, parent):
        stream_cfg = self.cfg.get("streaming", {})
        yt_cfg = self.cfg.get("youtube_api", {})

        # CARD TARGET SELECTOR
        c_mode = tk.Frame(parent, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        c_mode.pack(fill="x", pady=(0, 10))

        tk.Label(c_mode, text="🎯 Tujuan Siaran & Penyimpanan (Broadcast Destination)", bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        f_mr = tk.Frame(c_mode, bg="#1e293b")
        f_mr.pack(fill="x", pady=(6, 4))
        tk.Label(f_mr, text="Target Server:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.cmb_stream_mode = ttk.Combobox(
            f_mr,
            values=[
                "youtube (YouTube Live - Free Unlimited Cloud untuk Warga)",
                "private_rtmp (Private Media Server / Custom RTMP - MediaMTX, SRS, VPS)",
                "local_recording (Perekaman Lokal ke HDD / NAS Saja - Tanpa Internet)"
            ],
            state="readonly", width=58
        )
        cur_mode = stream_cfg.get("mode", "youtube")
        if cur_mode == "private_rtmp":
            self.cmb_stream_mode.set("private_rtmp (Private Media Server / Custom RTMP - MediaMTX, SRS, VPS)")
        elif cur_mode == "local_recording":
            self.cmb_stream_mode.set("local_recording (Perekaman Lokal ke HDD / NAS Saja - Tanpa Internet)")
        else:
            self.cmb_stream_mode.set("youtube (YouTube Live - Free Unlimited Cloud untuk Warga)")
        self.cmb_stream_mode.pack(side="left", padx=6)
        self.cmb_stream_mode.bind("<<ComboboxSelected>>", lambda e: self.on_stream_mode_changed())

        # CONTAINER DINAMIS
        self.f_dynamic_server = tk.Frame(parent, bg="#0f172a")
        self.f_dynamic_server.pack(fill="both", expand=True)

        # 1. CARD PRIVATE RTMP (Untuk Klien Bonafide / Gengsi)
        self.c_private = tk.Frame(self.f_dynamic_server, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        tk.Label(self.c_private, text="🏢 Private Media Server / Custom RTMP (Untuk Klien Bonafide)", bg="#1e293b", fg="#34d399", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(
            self.c_private,
            text="Solusi eksklusif tanpa logo YouTube! Mengalirkan feed ke server pribadi (MediaMTX / SRS / NGINX / VPS).\n"
                 "Klien dapat menonton di domain sendiri (misal: https://cctv.pt-klien.co.id) via WebRTC latensi < 0.5 dtk.",
            bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 8), justify="left"
        ).pack(anchor="w", pady=(2, 8))

        f_pr1 = tk.Frame(self.c_private, bg="#1e293b")
        f_pr1.pack(fill="x", pady=4)
        tk.Label(f_pr1, text="URL Private RTMP:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9, "bold"), width=18, anchor="w").pack(side="left")
        self.ent_custom_rtmp = tk.Entry(f_pr1, font=("Segoe UI", 9), width=45, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_custom_rtmp.insert(0, stream_cfg.get("custom_rtmp_url", "rtmp://127.0.0.1:1935/live/posronda"))
        self.ent_custom_rtmp.pack(side="left", padx=4)

        f_pr2 = tk.Frame(self.c_private, bg="#1e293b")
        f_pr2.pack(fill="x", pady=4)
        tk.Label(f_pr2, text="Stream Key / Path:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=18, anchor="w").pack(side="left")
        self.ent_custom_key = tk.Entry(f_pr2, font=("Segoe UI", 9), width=45, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_custom_key.insert(0, stream_cfg.get("stream_key", ""))
        self.ent_custom_key.pack(side="left", padx=4)

        # 2. CARD PEREKAMAN LOKAL HDD / NAS (Offline Tanpa Internet)
        self.c_local = tk.Frame(self.f_dynamic_server, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        tk.Label(self.c_local, text="💾 Perekaman Lokal Mandiri (Local HDD / NAS Storage)", bg="#1e293b", fg="#fbbf24", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(
            self.c_local,
            text="Keamanan & Kerahasiaan Penuh: Video disimpan langsung ke Harddisk / NAS lokal tanpa koneksi internet.\n"
                 "Dilengkapi fitur Auto-Prune yang otomatis menghapus rekaman lama agar penyimpanan tidak pernah penuh.",
            bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 8), justify="left"
        ).pack(anchor="w", pady=(2, 8))

        loc_cfg = stream_cfg.get("local_record", {})

        f_lc1 = tk.Frame(self.c_local, bg="#1e293b")
        f_lc1.pack(fill="x", pady=4)
        tk.Label(f_lc1, text="Folder Rekaman:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9, "bold"), width=18, anchor="w").pack(side="left")
        self.ent_rec_dir = tk.Entry(f_lc1, font=("Segoe UI", 9), width=36, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_rec_dir.insert(0, loc_cfg.get("output_dir", "recordings"))
        self.ent_rec_dir.pack(side="left", padx=4)
        btn_br_rec = tk.Button(f_lc1, text="Pilih Folder...", bg="#334155", fg="#cbd5e1", relief="flat", font=("Segoe UI", 8), command=self.browse_rec_dir)
        btn_br_rec.pack(side="left")

        f_lc2 = tk.Frame(self.c_local, bg="#1e293b")
        f_lc2.pack(fill="x", pady=4)
        tk.Label(f_lc2, text="Durasi Potongan File:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        self.cmb_seg_dur = ttk.Combobox(f_lc2, values=["15 Menit (Standar)", "30 Menit", "60 Menit (1 Jam)"], state="readonly", width=24)
        cur_seg = loc_cfg.get("segment_minutes", 15)
        self.cmb_seg_dur.set(f"{cur_seg} Menit (Standar)" if cur_seg == 15 else f"{cur_seg} Menit")
        self.cmb_seg_dur.pack(side="left", padx=4)

        f_lc3 = tk.Frame(self.c_local, bg="#1e293b")
        f_lc3.pack(fill="x", pady=4)
        tk.Label(f_lc3, text="Masa Simpan (Auto-Delete):", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        self.cmb_retention = ttk.Combobox(f_lc3, values=["7 Hari", "14 Hari (Direkomendasikan)", "30 Hari (1 Bulan)", "60 Hari"], state="readonly", width=24)
        cur_ret = loc_cfg.get("retention_days", 14)
        self.cmb_retention.set(f"{cur_ret} Hari (Direkomendasikan)" if cur_ret == 14 else f"{cur_ret} Hari")
        self.cmb_retention.pack(side="left", padx=4)

        # 3. CARD YOUTUBE LIVE (Default Siskamling / Warga)
        self.c_youtube = tk.Frame(self.f_dynamic_server, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        tk.Label(self.c_youtube, text="🔑 YouTube Live Streaming (Free Cloud Storage)", bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(
            self.c_youtube,
            text="Gunakan Stream Key bawaan YouTube Studio Anda. Bebas biaya sewa server & penyimpanan gratis 24 jam.",
            bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(2, 6))

        f_sk = tk.Frame(self.c_youtube, bg="#1e293b")
        f_sk.pack(fill="x", pady=3)
        tk.Label(f_sk, text="Stream Key:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9, "bold"), width=16, anchor="w").pack(side="left")
        self.ent_stream_key = tk.Entry(f_sk, font=("Segoe UI", 9), width=36, show="*", bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_stream_key.insert(0, stream_cfg.get("stream_key", ""))
        self.ent_stream_key.pack(side="left", padx=(0, 4))
        self.btn_toggle_key = tk.Button(f_sk, text="👁️", bg="#334155", fg="#cbd5e1", relief="flat", font=("Segoe UI", 8), command=self.toggle_stream_key_visibility)
        self.btn_toggle_key.pack(side="left")

        f_rtmp = tk.Frame(self.c_youtube, bg="#1e293b")
        f_rtmp.pack(fill="x", pady=3)
        tk.Label(f_rtmp, text="RTMP Server:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=16, anchor="w").pack(side="left")
        self.ent_rtmp = tk.Entry(f_rtmp, font=("Segoe UI", 9), width=42, bg="#0f172a", fg="#cbd5e1", insertbackground="#38bdf8")
        self.ent_rtmp.insert(0, stream_cfg.get("rtmp_server", "rtmp://a.rtmp.youtube.com/live2"))
        self.ent_rtmp.pack(side="left")

        # Otomasi API Box di dalam YouTube
        f_api_box = tk.Frame(self.c_youtube, bg="#0f172a", padx=10, pady=8)
        f_api_box.pack(fill="x", pady=(8, 2))

        self.var_yt_enabled = tk.BooleanVar(value=yt_cfg.get("enabled", False))
        chk_api = tk.Checkbutton(
            f_api_box,
            text="Aktifkan Otomasi YouTube API v3 (Auto Buat Broadcast & Masuk Playlist)",
            variable=self.var_yt_enabled,
            bg="#0f172a", fg="#ffffff", selectcolor="#1e293b",
            activebackground="#0f172a", activeforeground="#ffffff",
            font=("Segoe UI", 8, "bold")
        )
        chk_api.pack(anchor="w", pady=(0, 4))

        f_sec = tk.Frame(f_api_box, bg="#0f172a")
        f_sec.pack(fill="x", pady=2)
        tk.Label(f_sec, text="Client Secret JSON:", bg="#0f172a", fg="#cbd5e1", font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        self.ent_secret = tk.Entry(f_sec, font=("Segoe UI", 8), width=32, bg="#1e293b", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_secret.insert(0, yt_cfg.get("client_secrets_file", "client_secrets.json"))
        self.ent_secret.pack(side="left", padx=4)
        btn_br = tk.Button(f_sec, text="Pilih...", bg="#334155", fg="#cbd5e1", relief="flat", font=("Segoe UI", 7), command=self.browse_secret)
        btn_br.pack(side="left")

        f_pl = tk.Frame(f_api_box, bg="#0f172a")
        f_pl.pack(fill="x", pady=2)
        tk.Label(f_pl, text="Playlist ID:", bg="#0f172a", fg="#cbd5e1", font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        self.ent_playlist = tk.Entry(f_pl, font=("Segoe UI", 8), width=38, bg="#1e293b", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_playlist.insert(0, yt_cfg.get("playlist_id", ""))
        self.ent_playlist.pack(side="left", padx=4)

        f_tit = tk.Frame(f_api_box, bg="#0f172a")
        f_tit.pack(fill="x", pady=2)
        tk.Label(f_tit, text="Judul Video:", bg="#0f172a", fg="#cbd5e1", font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        self.ent_title = tk.Entry(f_tit, font=("Segoe UI", 8), width=38, bg="#1e293b", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_title.insert(0, yt_cfg.get("title_prefix", "PosRonda Live Monitoring 24 Jam"))
        self.ent_title.pack(side="left", padx=4)

        f_lat = tk.Frame(f_api_box, bg="#0f172a")
        f_lat.pack(fill="x", pady=2)
        tk.Label(f_lat, text="Latency:", bg="#0f172a", fg="#cbd5e1", font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        self.cmb_latency = ttk.Combobox(f_lat, values=["low (Jeda 4-7 dtk - Seimbang)", "ultraLow (1.5-3 dtk)", "normal (15-30 dtk)"], state="readonly", width=34)
        cur_lat = yt_cfg.get("latency_preference", "low")
        self.cmb_latency.set("ultraLow (1.5-3 dtk)" if cur_lat == "ultraLow" else "normal (15-30 dtk)" if cur_lat == "normal" else "low (Jeda 4-7 dtk - Seimbang)")
        self.cmb_latency.pack(side="left", padx=4)

        f_act = tk.Frame(f_api_box, bg="#0f172a")
        f_act.pack(fill="x", pady=(6, 0))
        btn_t_api = tk.Button(f_act, text="▶ Tes YouTube API", bg="#dc2626", fg="white", relief="flat", font=("Segoe UI", 7, "bold"), padx=6, pady=2, command=self.test_youtube_api)
        btn_t_api.pack(side="left", padx=(0, 6))
        btn_c_live = tk.Button(f_act, text="⏹️ Tutup Siaran Zombie", bg="#b91c1c", fg="#fee2e2", relief="flat", font=("Segoe UI", 7), padx=6, pady=2, command=self.cleanup_active_broadcasts)
        btn_c_live.pack(side="left", padx=(0, 6))
        btn_c_up = tk.Button(f_act, text="🗑️ Hapus Upcoming Menumpuk", bg="#7f1d1d", fg="#fecaca", relief="flat", font=("Segoe UI", 7), padx=6, pady=2, command=self.cleanup_upcoming_broadcasts)
        btn_c_up.pack(side="left")

        # Render kartu yang aktif
        self.on_stream_mode_changed()

    def on_stream_mode_changed(self):
        mode_val = self.cmb_stream_mode.get()
        self.c_youtube.pack_forget()
        self.c_private.pack_forget()
        self.c_local.pack_forget()

        if "private_rtmp" in mode_val:
            self.c_private.pack(fill="x", pady=(0, 10))
        elif "local_recording" in mode_val:
            self.c_local.pack(fill="x", pady=(0, 10))
        else: # YouTube
            self.c_youtube.pack(fill="x", pady=(0, 10))

    def browse_rec_dir(self):
        d = filedialog.askdirectory(parent=self)
        if d:
            self.ent_rec_dir.delete(0, tk.END)
            self.ent_rec_dir.insert(0, d)

    def browse_secret(self):
        f = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], parent=self)
        if f:
            self.ent_secret.delete(0, tk.END)
            self.ent_secret.insert(0, f)

    def test_youtube_api(self):
        secret_file = self.ent_secret.get().strip()
        playlist_id = self.ent_playlist.get().strip()

        if not secret_file or not os.path.exists(secret_file):
            messagebox.showerror("File Tidak Ditemukan", f"File client secret '{secret_file}' tidak ditemukan!", parent=self)
            return

        def run_test():
            try:
                from youtube_manager import YouTubeManager
                temp_cfg = {
                    "youtube_api": {
                        "client_secrets_file": secret_file,
                        "token_file": "token.json",
                        "playlist_id": playlist_id,
                        "privacy_status": "unlisted"
                    }
                }
                yt = YouTubeManager(temp_cfg)
                ok, message = yt.test_connection(playlist_id=playlist_id)
                if ok:
                    self.after(0, lambda: messagebox.showinfo("Koneksi YouTube API Sukses", message, parent=self))
                else:
                    self.after(0, lambda: messagebox.showwarning("Peringatan YouTube API", message, parent=self))
            except Exception as e:
                err_text = str(e)
                self.after(0, lambda: messagebox.showerror("Gagal Tes", f"Error YouTube API:\n{err_text}", parent=self))

        threading.Thread(target=run_test, daemon=True).start()

    def cleanup_upcoming_broadcasts(self):
        secret_file = self.ent_secret.get().strip()
        if not secret_file or not os.path.exists(secret_file):
            messagebox.showerror("File Tidak Ditemukan", f"File '{secret_file}' tidak ditemukan!", parent=self)
            return

        if not messagebox.askyesno("Konfirmasi", "Hapus semua siaran 'Upcoming' yang menumpuk di channel?", parent=self):
            return

        def run_cleanup():
            try:
                from youtube_manager import YouTubeManager
                yt = YouTubeManager(self.cfg)
                ok, msg = yt.cleanup_all_upcoming()
                self.after(0, lambda: messagebox.showinfo("Pembersihan Selesai", msg, parent=self))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e), parent=self))

        threading.Thread(target=run_cleanup, daemon=True).start()

    def cleanup_active_broadcasts(self):
        secret_file = self.ent_secret.get().strip()
        if not os.path.exists(secret_file):
            messagebox.showwarning("File Tidak Ditemukan", f"File '{secret_file}' tidak ditemukan!", parent=self)
            return

        if not messagebox.askyesno("Konfirmasi", "Tutup seluruh siaran Live menggantung menjadi video arsip?", parent=self):
            return

        def run_cleanup_live():
            try:
                from youtube_manager import YouTubeManager
                yt = YouTubeManager(self.cfg)
                ok, msg = yt.cleanup_active_live_broadcasts(only_cctv_prefix=False)
                self.after(0, lambda: messagebox.showinfo("Pembersihan Siaran Live Selesai", msg, parent=self))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e), parent=self))

        threading.Thread(target=run_cleanup_live, daemon=True).start()

    def build_perf_tab(self, parent):
        perf_cfg = self.cfg.get("streaming", {})

        c_perf = tk.Frame(parent, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        c_perf.pack(fill="x", pady=(0, 12))

        tk.Label(c_perf, text="⚡ Mesin Encoding & Hardware Acceleration", bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        # Encoder
        f_enc = tk.Frame(c_perf, bg="#1e293b")
        f_enc.pack(fill="x", pady=6)
        tk.Label(f_enc, text="Encoder Video:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=20, anchor="w").pack(side="left")
        self.cmb_encoder = ttk.Combobox(
            f_enc, 
            values=[
                "h264_qsv (Intel QuickSync GPU - ThinkPad X230 Sangat Dingin)",
                "libx264 (Software CPU - Kompatibel Universal)"
            ], 
            state="readonly", width=42
        )
        cur_enc = perf_cfg.get("encoder", "h264_qsv")
        self.cmb_encoder.set("h264_qsv (Intel QuickSync GPU - ThinkPad X230 Sangat Dingin)" if cur_enc == "h264_qsv" else "libx264 (Software CPU - Kompatibel Universal)")
        self.cmb_encoder.pack(side="left", padx=5)

        # Resolusi Grid
        f_res = tk.Frame(c_perf, bg="#1e293b")
        f_res.pack(fill="x", pady=6)
        tk.Label(f_res, text="Resolusi Layar:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=20, anchor="w").pack(side="left")
        self.cmb_res = ttk.Combobox(
            f_res,
            values=[
                "1280x720 (720p HD - Seimbang & Ringan)",
                "1920x1080 (1080p Full HD - Tajam)",
                "960x540 (qHD - Paling Hemat Kuota)"
            ],
            state="readonly", width=42
        )
        cur_res = perf_cfg.get("grid_resolution", "1280x720")
        self.cmb_res.set("1920x1080 (1080p Full HD - Tajam)" if cur_res == "1920x1080" else "960x540 (qHD - Paling Hemat Kuota)" if cur_res == "960x540" else "1280x720 (720p HD - Seimbang & Ringan)")
        self.cmb_res.pack(side="left", padx=5)

        # FPS
        f_fps = tk.Frame(c_perf, bg="#1e293b")
        f_fps.pack(fill="x", pady=6)
        tk.Label(f_fps, text="Frame Rate (FPS):", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=20, anchor="w").pack(side="left")
        self.cmb_fps = ttk.Combobox(f_fps, values=["25 FPS (Standar Mulus)", "30 FPS", "20 FPS", "15 FPS (Hemat Daya)"], state="readonly", width=42)
        cur_fps = perf_cfg.get("fps", 25)
        self.cmb_fps.set(f"{cur_fps} FPS" if cur_fps in [15, 20, 30] else "25 FPS (Standar Mulus)")
        self.cmb_fps.pack(side="left", padx=5)

        # Bitrate
        f_bit = tk.Frame(c_perf, bg="#1e293b")
        f_bit.pack(fill="x", pady=6)
        tk.Label(f_bit, text="Bitrate Streaming (kbps):", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=20, anchor="w").pack(side="left")
        self.ent_bitrate = tk.Entry(f_bit, font=("Segoe UI", 9), width=44, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_bitrate.insert(0, str(perf_cfg.get("bitrate_kbps", 1200)))
        self.ent_bitrate.pack(side="left", padx=5)

        # Auto-Start Windows Card
        c_boot = tk.Frame(parent, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        c_boot.pack(fill="x")

        self.var_autostart = tk.BooleanVar(value=config_manager.is_autostart_enabled())
        chk_boot = tk.Checkbutton(
            c_boot,
            text="🚀 Jalankan PosRonda Otomatis saat Windows Menyala (Auto-Recovery Pasca Mati Lampu)",
            variable=self.var_autostart,
            bg="#1e293b", fg="#ffffff", selectcolor="#0f172a",
            activebackground="#1e293b", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold")
        )
        chk_boot.pack(anchor="w", pady=(0, 4))

        tk.Label(
            c_boot,
            text="Sangat disarankan untuk pos siskamling 24 jam! Jika listrik padam dan kembali menyala,\n"
                 "laptop akan otomatis memuat PosRonda dan streaming kembali aktif secara mandiri.",
            bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 8), justify="left"
        ).pack(anchor="w")

    def build_osd_tab(self, parent):
        osd_cfg = self.cfg.get("osd", {})

        c_osd = tk.Frame(parent, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        c_osd.pack(fill="x")

        tk.Label(c_osd, text="✍️ Kustomisasi Teks Jam & Nama Kamera (OSD)", bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

        f_pos = tk.Frame(c_osd, bg="#1e293b")
        f_pos.pack(fill="x", pady=6)
        tk.Label(f_pos, text="Posisi Teks di Layar:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=20, anchor="w").pack(side="left")
        self.cmb_osd_pos = ttk.Combobox(
            f_pos,
            values=["top_left (Pojok Kiri Atas)", "bottom_left (Pojok Kiri Bawah)", "top_right (Pojok Kanan Atas)", "bottom_right (Pojok Kanan Bawah)", "none (Sembunyikan)"],
            state="readonly", width=40
        )
        cur_pos = osd_cfg.get("position", "top_left")
        self.cmb_osd_pos.set(f"{cur_pos} (Pojok Kiri Atas)" if cur_pos == "top_left" else cur_pos)
        self.cmb_osd_pos.pack(side="left", padx=5)

        f_sz = tk.Frame(c_osd, bg="#1e293b")
        f_sz.pack(fill="x", pady=6)
        tk.Label(f_sz, text="Ukuran Huruf (Font Scale):", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=20, anchor="w").pack(side="left")
        self.cmb_osd_size = ttk.Combobox(f_sz, values=["0.42 (Standar Rekomendasi)", "0.38 (Kecil Rapi)", "0.50 (Sedang)", "0.60 (Besar)"], width=40)
        self.cmb_osd_size.set(str(osd_cfg.get("font_scale", 0.42)))
        self.cmb_osd_size.pack(side="left", padx=5)

        f_sty = tk.Frame(c_osd, bg="#1e293b")
        f_sty.pack(fill="x", pady=6)
        tk.Label(f_sty, text="Gaya Badge:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=20, anchor="w").pack(side="left")
        self.cmb_osd_style = ttk.Combobox(
            f_sty,
            values=["badge_outline (Badge Gelap + Outline)", "clean_outline (Tanpa Kotak Badge)", "retro_green (Hijau CCTV Retro)"],
            state="readonly", width=40
        )
        self.cmb_osd_style.set(osd_cfg.get("style", "badge_outline"))
        self.cmb_osd_style.pack(side="left", padx=5)

    def build_tg_tab(self, parent):
        tg_cfg = self.cfg.get("telegram", {})

        c_tg = tk.Frame(parent, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        c_tg.pack(fill="x")

        self.var_tg_enabled = tk.BooleanVar(value=tg_cfg.get("enabled", False))
        chk_tg = tk.Checkbutton(
            c_tg,
            text="Aktifkan Notifikasi Telegram (Kirim Status & Deteksi Kamera)",
            variable=self.var_tg_enabled,
            bg="#1e293b", fg="#ffffff", selectcolor="#0f172a",
            activebackground="#1e293b", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold")
        )
        chk_tg.pack(anchor="w", pady=(0, 10))

        f_tok = tk.Frame(c_tg, bg="#1e293b")
        f_tok.pack(fill="x", pady=4)
        tk.Label(f_tok, text="Bot Token:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=18, anchor="w").pack(side="left")
        self.ent_tg_token = tk.Entry(f_tok, font=("Segoe UI", 9), width=42, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_tg_token.insert(0, tg_cfg.get("bot_token", ""))
        self.ent_tg_token.pack(side="left", padx=5)

        f_ch = tk.Frame(c_tg, bg="#1e293b")
        f_ch.pack(fill="x", pady=4)
        tk.Label(f_ch, text="Chat ID:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9), width=18, anchor="w").pack(side="left")
        self.ent_tg_chat = tk.Entry(f_ch, font=("Segoe UI", 9), width=42, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_tg_chat.insert(0, tg_cfg.get("chat_id", ""))
        self.ent_tg_chat.pack(side="left", padx=5)

        btn_t_tg = tk.Button(c_tg, text="✈ Kirim Notifikasi Tes Telegram", bg="#0284c7", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=10, pady=5, command=self.test_telegram)
        btn_t_tg.pack(anchor="w", pady=(12, 0))

    def test_telegram(self):
        token = self.ent_tg_token.get().strip()
        chat_id = self.ent_tg_chat.get().strip()
        if not token or not chat_id:
            messagebox.showwarning("Data Kurang", "Harap isi Bot Token dan Chat ID Telegram terlebih dahulu!", parent=self)
            return

        def _do_tg():
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                r = requests.post(url, json={"chat_id": chat_id, "text": "🔔 Tes Berhasil! PosRonda Hub terhubung ke Telegram Anda."}, timeout=6)
                if r.status_code == 200:
                    self.after(0, lambda: messagebox.showinfo("Sukses", "Pesan tes berhasil diterima Telegram!", parent=self))
                else:
                    self.after(0, lambda: messagebox.showerror("Gagal", f"Telegram API Error: {r.text}", parent=self))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e), parent=self))

        threading.Thread(target=_do_tg, daemon=True).start()

    def build_license_tab(self, parent):
        lic_info = LicenseManager.get_license_info()

        c_status = tk.Frame(parent, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        c_status.pack(fill="x", pady=(0, 12))

        lbl_tier = tk.Label(
            c_status,
            text=f"💎 {lic_info.get('tier_name')}",
            bg="#1e293b", fg="#38bdf8" if lic_info.get("is_pro") else "#cbd5e1",
            font=("Segoe UI", 11, "bold")
        )
        lbl_tier.pack(anchor="w")

        lbl_status_desc = tk.Label(
            c_status,
            text=f"Status: {lic_info.get('status_text')}\n"
                 f"Pemegang: {lic_info.get('holder')} ({lic_info.get('org')})",
            bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 9), justify="left"
        )
        lbl_status_desc.pack(anchor="w", pady=(4, 0))

        c_winrar = tk.Frame(parent, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        c_winrar.pack(fill="x", pady=(0, 12))

        tk.Label(c_winrar, text="📖 Konsep Lisensi PosRonda (Semi Open-Source ala WinRAR)", bg="#1e293b", fg="#34d399", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(
            c_winrar,
            text="PosRonda menganut filosofi keterbukaan ala WinRAR:\n"
                 "• PosRonda Community Edition: Sepenuhnya GRATIS selamanya tanpa batasan durasi monitoring,\n"
                 "  tanpa batas waktu, dan tidak pernah kedaluwarsa untuk warga RT/RW, masjid, dan pos kamling.\n"
                 "• PosRonda PRO Commercial Edition: Ditujukan bagi teknisi / installer CCTV profesional yang menjual\n"
                 "  solusi monitoring siap pakai kepada klien komersial (ruko, perkantoran, perumahan elitis, pabrik).",
            bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8), justify="left"
        ).pack(anchor="w", pady=(4, 6))

        tk.Label(
            c_winrar,
            text="Fitur Eksklusif PosRonda PRO:\n"
                 "✔ Multi-Kamera hingga 16 Kamera (Grid 3x3 & Auto Patrol Tour).\n"
                 "✔ Private Media Server (MediaMTX / SRS) & Direct Local NAS Recording.\n"
                 "✔ White-Labeling Penuh: Ganti nama & logo PosRonda dengan merek usaha Anda sendiri.\n"
                 "✔ Watermark Kustom & Logo Perusahaan pada tayangan siaran.",
            bg="#1e293b", fg="#fbbf24", font=("Segoe UI", 8), justify="left"
        ).pack(anchor="w")

        c_act = tk.Frame(parent, bg="#1e293b", padx=14, pady=12, highlightthickness=1, highlightbackground="#334155")
        c_act.pack(fill="x")

        tk.Label(c_act, text="🔑 Aktivasi Kunci Lisensi PosRonda PRO", bg="#1e293b", fg="#f8fafc", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))

        f_h = tk.Frame(c_act, bg="#1e293b")
        f_h.pack(fill="x", pady=2)
        tk.Label(f_h, text="Nama Pemilik:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        self.ent_lic_holder = tk.Entry(f_h, font=("Segoe UI", 8), width=36, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_lic_holder.pack(side="left")

        f_o = tk.Frame(c_act, bg="#1e293b")
        f_o.pack(fill="x", pady=2)
        tk.Label(f_o, text="Organisasi/Toko:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        self.ent_lic_org = tk.Entry(f_o, font=("Segoe UI", 8), width=36, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_lic_org.pack(side="left")

        f_k = tk.Frame(c_act, bg="#1e293b")
        f_k.pack(fill="x", pady=2)
        tk.Label(f_k, text="Serial Key (.LIC):", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        self.ent_lic_key = tk.Entry(f_k, font=("Segoe UI", 8), width=36, bg="#0f172a", fg="#ffffff", insertbackground="#38bdf8")
        self.ent_lic_key.pack(side="left")

        f_b_lic = tk.Frame(c_act, bg="#1e293b")
        f_b_lic.pack(fill="x", pady=(8, 0))

        btn_apply_lic = tk.Button(
            f_b_lic, text="✔ Pasang Lisensi PRO", bg="#059669", fg="white", relief="flat", font=("Segoe UI", 8, "bold"),
            padx=10, pady=4, cursor="hand2", command=self.apply_pro_license
        )
        btn_apply_lic.pack(side="left", padx=(0, 8))

        btn_buy_lic = tk.Button(
            f_b_lic, text="🛒 Beli Lisensi Pro PosRonda", bg="#3b82f6", fg="white", relief="flat", font=("Segoe UI", 8),
            padx=10, pady=4, cursor="hand2", command=self.open_buy_license_info
        )
        btn_buy_lic.pack(side="left")

    def apply_pro_license(self):
        holder = self.ent_lic_holder.get().strip()
        org = self.ent_lic_org.get().strip() or "Komersial"
        key = self.ent_lic_key.get().strip()

        if not holder or not key:
            messagebox.showwarning("Data Kurang", "Harap masukkan Nama Pemilik dan Serial Key!", parent=self)
            return

        ok, msg = LicenseManager.install_license(holder, org, key)
        if ok:
            messagebox.showinfo("Aktivasi Sukses", f"Selamat! {msg}\n\nSilakan restart PosRonda untuk menikmati fitur PRO.", parent=self)
        else:
            messagebox.showerror("Gagal Pasang Lisensi", msg, parent=self)

    def open_buy_license_info(self):
        messagebox.showinfo(
            "Pembelian Lisensi PosRonda PRO",
            "🛡️ PosRonda PRO Edition dirancang untuk mendukung teknisi CCTV dan pengembangan berkelanjutan.\n\n"
            "Untuk pemesanan lisensi komersial & white-labeling kustom:\n"
            "• Email: support@posronda.org / dev@posronda.internal\n"
            "• Lisensi berlaku seumur hidup (Lifetime) per mesin/unit klien.\n\n"
            "Terima kasih telah mendukung keamanan lingkungan dan proyek ini!",
            parent=self
        )

    def save_all(self):
        new_cams = []
        for i, (ent_name, ent_url) in enumerate(self.cam_entries):
            url_val = ent_url.get().strip()
            name_val = ent_name.get().strip()
            new_cams.append({
                "id": i + 1,
                "name": name_val,
                "rtsp_url": url_val,
                "enabled": bool(url_val)
            })

        self.cfg["cameras"] = new_cams

        # Simpan Pengaturan Patrol
        if "patrol" not in self.cfg:
            self.cfg["patrol"] = {}
        self.cfg["patrol"]["enabled"] = self.var_patrol_enabled.get()
        try:
            self.cfg["patrol"]["interval_seconds"] = int(self.cmb_patrol_interval.get().split()[0])
        except Exception:
            self.cfg["patrol"]["interval_seconds"] = 15

        lay_choice = self.cmb_patrol_layout.get()
        self.cfg["patrol"]["layout"] = "3x3" if "3x3" in lay_choice else "2x2"

        # Simpan Kredensial Default Kamera
        if "default_camera_credentials" not in self.cfg:
            self.cfg["default_camera_credentials"] = {}
        self.cfg["default_camera_credentials"]["username"] = self.ent_cam_user.get().strip()
        self.cfg["default_camera_credentials"]["password"] = self.ent_cam_pwd.get().strip()
        try:
            self.cfg["default_camera_credentials"]["default_port"] = int(self.ent_cam_port.get().strip())
        except Exception:
            self.cfg["default_camera_credentials"]["default_port"] = 554

        # Simpan Target Server & Mode Siaran
        mode_raw = self.cmb_stream_mode.get()
        if "private_rtmp" in mode_raw:
            stream_mode = "private_rtmp"
        elif "local_recording" in mode_raw:
            stream_mode = "local_recording"
        else:
            stream_mode = "youtube"

        self.cfg["streaming"]["mode"] = stream_mode
        self.cfg["streaming"]["custom_rtmp_url"] = self.ent_custom_rtmp.get().strip()
        if hasattr(self, "ent_custom_key") and self.ent_custom_key.get().strip():
            self.cfg["streaming"]["stream_key"] = self.ent_custom_key.get().strip()
        else:
            self.cfg["streaming"]["stream_key"] = self.ent_stream_key.get().strip()
        self.cfg["streaming"]["rtmp_server"] = self.ent_rtmp.get().strip()

        # Simpan Local Record
        if "local_record" not in self.cfg["streaming"]:
            self.cfg["streaming"]["local_record"] = {}
        self.cfg["streaming"]["local_record"]["enabled"] = (stream_mode == "local_recording")
        self.cfg["streaming"]["local_record"]["output_dir"] = self.ent_rec_dir.get().strip()
        try:
            self.cfg["streaming"]["local_record"]["segment_minutes"] = int(self.cmb_seg_dur.get().split()[0])
        except Exception:
            self.cfg["streaming"]["local_record"]["segment_minutes"] = 15
        try:
            self.cfg["streaming"]["local_record"]["retention_days"] = int(self.cmb_retention.get().split()[0])
        except Exception:
            self.cfg["streaming"]["local_record"]["retention_days"] = 14

        # YouTube API config
        self.cfg["youtube_api"]["enabled"] = self.var_yt_enabled.get()
        self.cfg["youtube_api"]["client_secrets_file"] = self.ent_secret.get().strip()
        self.cfg["youtube_api"]["playlist_id"] = self.ent_playlist.get().strip()
        self.cfg["youtube_api"]["title_prefix"] = self.ent_title.get().strip()
        lat_choice = self.cmb_latency.get()
        self.cfg["youtube_api"]["latency_preference"] = "ultraLow" if "ultraLow" in lat_choice else "normal" if "normal" in lat_choice else "low"

        # Hardware & Perf
        res_choice = self.cmb_res.get()
        self.cfg["streaming"]["grid_resolution"] = "1920x1080" if "1920x1080" in res_choice else "960x540" if "960x540" in res_choice else "1280x720"

        enc_choice = self.cmb_encoder.get()
        self.cfg["streaming"]["encoder"] = "h264_qsv" if "h264_qsv" in enc_choice else "libx264"

        try:
            self.cfg["streaming"]["fps"] = int(self.cmb_fps.get().split()[0])
        except Exception:
            self.cfg["streaming"]["fps"] = 25

        try:
            self.cfg["streaming"]["bitrate_kbps"] = int(self.ent_bitrate.get().strip())
        except Exception:
            self.cfg["streaming"]["bitrate_kbps"] = 1200

        # OSD
        if "osd" not in self.cfg:
            self.cfg["osd"] = {}
        try:
            self.cfg["osd"]["font_scale"] = float(self.cmb_osd_size.get().split()[0])
        except Exception:
            self.cfg["osd"]["font_scale"] = 0.42

        pos_raw = self.cmb_osd_pos.get().split()[0]
        self.cfg["osd"]["position"] = pos_raw if pos_raw in ["top_left", "bottom_left", "top_right", "bottom_right", "none"] else "top_left"
        self.cfg["osd"]["style"] = self.cmb_osd_style.get().split()[0]

        # Telegram
        self.cfg["telegram"]["enabled"] = self.var_tg_enabled.get()
        self.cfg["telegram"]["bot_token"] = self.ent_tg_token.get().strip()
        self.cfg["telegram"]["chat_id"] = self.ent_tg_chat.get().strip()

        # Windows Auto-Start
        if hasattr(self, "var_autostart"):
            try:
                config_manager.set_autostart(self.var_autostart.get())
            except Exception as e:
                print(f"[Settings] Error set autostart: {e}")

        # Terapkan konfigurasi
        self.on_save(self.cfg)
        self.destroy()
