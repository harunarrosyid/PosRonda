"""
PosRonda v4.0 - Autonomous CCTV Multi-Camera Hub & Live Streaming Engine
Monitoring Multi-Kamera (2x2 Patrol / 3x3 Grid) + Auto Streaming (YouTube Live, Private RTMP, HDD/NAS).
Dioptimalkan untuk ThinkPad X230 (Intel QuickSync QSV).
Semi Open-Source License Model (ala WinRAR).
"""

import sys
import os

# Standar Industri RTSP Capture: TCP, No-Buffer, Low-Delay, 1MB Socket Buffer, 5s Timeout (Anti-Freeze & Anti-Choke)
# SANGAT PENTING: Harus disetel SEBELUM 'import cv2' dimuat ke memori!
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;tcp|"
    "fflags;nobuffer|"
    "flags;low_delay|"
    "framedrop;1|"
    "max_delay;500000|"
    "reorder_queue_size;0|"
    "stimeout;5000000|"
    "timeout;5000000|"
    "buffer_size;1048576"
)

import time
import threading
import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

try:
    from posronda.core import config_manager
    from posronda.core.license_manager import LicenseManager
    from posronda.core.stream_engine import RTSPCameraWorker, FFmpegStreamPusher, GridCompositor
    from posronda.ui.settings_dialog import SettingsDialog
    from posronda.network.notifier import TelegramNotifier
    from posronda.utils import check_env
except ImportError:
    import check_env
    import config_manager
    from license_manager import LicenseManager
    from stream_engine import RTSPCameraWorker, FFmpegStreamPusher, GridCompositor
    from settings_dialog import SettingsDialog
    from notifier import TelegramNotifier

class CCTVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PosRonda v4.0 - Autonomous CCTV Multi-Camera Hub & Streaming Engine")
        self.root.geometry("1280x720")
        self.root.configure(bg="#07090e")

        # Muat konfigurasi
        self.cfg = config_manager.load_config()

        # Status kontrol streaming
        self.streaming_enabled = True
        self.is_streaming = False
        self.is_paused = False
        self.restart_requested = False
        self.stream_start_time = time.time()
        self.pusher_start_time = 0
        self.youtube_mgr = None
        self.current_broadcast = None
        self.pusher = None
        self.is_fullscreen = False

        # Inisialisasi Worker Kamera
        self.cams = []
        self._init_cameras()

        # Inisialisasi Mesin Compositor Berkecepatan Tinggi (Dedicated Compositor Engine)
        init_fps = self.cfg.get("streaming", {}).get("fps", 25)
        init_res = self.cfg.get("streaming", {}).get("grid_resolution", "1280x720")
        self.compositor = GridCompositor(
            cameras=self.cams,
            pusher=self.pusher,
            fps=init_fps,
            resolution=init_res,
            patrol_cfg=self.cfg.get("patrol", {})
        )
        self.compositor.start()

        # Bilah Kontrol & Status Bawah (Surveillance Command Center Bar)
        self.bottom_bar = tk.Frame(self.root, bg="#0f172a", padx=10, pady=6, highlightthickness=1, highlightbackground="#1e293b")
        self.bottom_bar.pack(side="bottom", fill="x")

        # Kiri: Brand Pill, Live Indicator Pill, Spec Badge & Teks Status
        self.lbl_brand_badge = tk.Label(
            self.bottom_bar, 
            text="🛡️ PosRonda v4.0", 
            bg="#1e1b4b", 
            fg="#818cf8", 
            font=("Segoe UI", 9, "bold"),
            padx=8, pady=2
        )
        self.lbl_brand_badge.pack(side="left", padx=(0, 6))

        self.lbl_status_icon = tk.Label(
            self.bottom_bar, 
            text="● MONITORING", 
            bg="#064e3b", 
            fg="#34d399", 
            font=("Segoe UI", 8, "bold"),
            padx=8, pady=2
        )
        self.lbl_status_icon.pack(side="left", padx=(0, 6))

        # Pill Spec Hardware/Resolusi & Target Server
        enc_lbl = "QSV GPU" if self.cfg.get("streaming", {}).get("encoder") == "h264_qsv" else "CPU"
        stream_mode = self.cfg.get("streaming", {}).get("mode", "youtube")
        mode_lbl = "YT Live" if stream_mode == "youtube" else ("Private RTMP" if stream_mode == "private_rtmp" else "HDD/NAS")
        self.lbl_spec_badge = tk.Label(
            self.bottom_bar,
            text=f"{init_res} • {init_fps}fps • {enc_lbl} • {mode_lbl}",
            bg="#1e293b",
            fg="#94a3b8",
            font=("Segoe UI", 8),
            padx=6, pady=2
        )
        self.lbl_spec_badge.pack(side="left", padx=(0, 8))

        self.lbl_status_text = tk.Label(
            self.bottom_bar, 
            text="Sistem monitoring aktif. (F2: Pengaturan | Spasi: Ganti Halaman Kamera | F11: Fullscreen)", 
            bg="#0f172a", 
            fg="#cbd5e1", 
            font=("Segoe UI", 8), 
            anchor="w"
        )
        self.lbl_status_text.pack(side="left", fill="x", expand=True)

        # Kanan: Tombol Kendali Cepat (Fullscreen, About/WinRAR, Settings, Navigasi Halaman, Akhiri, Restart, Jeda)
        self.btn_fs = tk.Button(
            self.bottom_bar, 
            text="⛶ Fullscreen (F11)", 
            bg="#1e293b", 
            fg="#94a3b8", 
            activebackground="#334155", 
            activeforeground="#ffffff",
            relief="flat", 
            font=("Segoe UI", 8), 
            padx=7, pady=2, 
            cursor="hand2",
            command=self.toggle_fullscreen
        )
        self.btn_fs.pack(side="right", padx=2)

        self.btn_about = tk.Button(
            self.bottom_bar, 
            text="💎 Lisensi (F1)", 
            bg="#1e293b", 
            fg="#38bdf8", 
            activebackground="#0284c7", 
            activeforeground="#ffffff",
            relief="flat", 
            font=("Segoe UI", 8), 
            padx=7, pady=2, 
            cursor="hand2",
            command=self.open_about_dialog
        )
        self.btn_about.pack(side="right", padx=2)

        self.btn_settings = tk.Button(
            self.bottom_bar, 
            text="⚙️ Pengaturan (F2)", 
            bg="#334155", 
            fg="#e2e8f0", 
            activebackground="#475569", 
            activeforeground="#ffffff",
            relief="flat", 
            font=("Segoe UI", 8), 
            padx=7, pady=2, 
            cursor="hand2",
            command=self.open_settings
        )
        self.btn_settings.pack(side="right", padx=2)

        # Tombol Navigasi Halaman Kamera (Patrol / Tour Mode Quick Selector)
        self.btn_page = tk.Button(
            self.bottom_bar,
            text="📄 Hal 1/1 (Spasi)",
            bg="#1e1b4b",
            fg="#a5b4fc",
            activebackground="#312e81",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            padx=7, pady=2,
            cursor="hand2",
            command=self.switch_camera_page
        )
        self.btn_page.pack(side="right", padx=2)

        self.btn_end = tk.Button(
            self.bottom_bar, 
            text="⏹️ Akhiri (F7)", 
            bg="#b91c1c", 
            fg="white", 
            activebackground="#dc2626", 
            activeforeground="#ffffff",
            relief="flat", 
            font=("Segoe UI", 8, "bold"), 
            padx=8, pady=2, 
            cursor="hand2",
            command=self.end_streaming
        )
        self.btn_end.pack(side="right", padx=2)

        self.btn_restart = tk.Button(
            self.bottom_bar, 
            text="🔄 Restart (F5)", 
            bg="#1d4ed8", 
            fg="white", 
            activebackground="#2563eb", 
            activeforeground="#ffffff",
            relief="flat", 
            font=("Segoe UI", 8, "bold"), 
            padx=8, pady=2, 
            cursor="hand2",
            command=self.restart_streaming
        )
        self.btn_restart.pack(side="right", padx=2)

        self.btn_pause = tk.Button(
            self.bottom_bar, 
            text="⏸️ Jeda (F6)", 
            bg="#b45309", 
            fg="white", 
            activebackground="#d97706", 
            activeforeground="#ffffff",
            relief="flat", 
            font=("Segoe UI", 8, "bold"), 
            padx=8, pady=2, 
            cursor="hand2",
            command=self.toggle_pause
        )
        self.btn_pause.pack(side="right", padx=2)

        # Canvas untuk Tampilan Layar Penuh (Di-pack setelah bottom_bar agar tidak menimpa bar)
        self.canvas = tk.Canvas(self.root, bg="#000000", highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill="both", expand=True)
        self.canvas_img_id = None
        self.tk_photo = None
        self._last_offset = None
        self._last_dims = None

        # Bind Interaksi Tap / Klik pada Layar Kamera (Tap 2x Refresh Seketika)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_tap)
        self.canvas.bind("<Button-1>", self.on_canvas_single_tap)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)

        # Bind Keyboard Shortcuts
        self.root.bind("<F1>", lambda e: self.open_about_dialog())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())
        self.root.bind("<F2>", lambda e: self.open_settings())
        self.root.bind("<F5>", lambda e: self.restart_streaming())
        self.root.bind("<F6>", lambda e: self.toggle_pause())
        self.root.bind("<F7>", lambda e: self.end_streaming())

        # Shortcut Patrol / Ganti Halaman Kamera
        self.root.bind("<space>", lambda e: self.switch_camera_page())
        self.root.bind("<Tab>", lambda e: self.switch_camera_page())
        self.root.bind("<Prior>", lambda e: self.prev_camera_page())
        self.root.bind("<Next>", lambda e: self.switch_camera_page())
        self.root.bind("1", lambda e: self.select_camera_page(0))
        self.root.bind("2", lambda e: self.select_camera_page(1))
        self.root.bind("3", lambda e: self.select_camera_page(2))
        self.root.bind("4", lambda e: self.select_camera_page(3))

        # Event Trigger untuk Reset / Mulai Ulang Stream Seketika
        self.stream_trigger = threading.Event()

        # Thread Lifecycle Streaming Engine (YouTube / Private RTMP / Local Recording)
        self.lifecycle_thread = threading.Thread(target=self._youtube_lifecycle_loop, daemon=True)
        self.lifecycle_thread.start()

        # Mulai Render Loop GUI (OBS Zero-Overhead In-Place Paste @ ~33 FPS, hemat CPU/GIL 95%)
        self.render_interval_ms = 30
        self.root.after(100, self.update_frame_loop)

        # Mulai Timer Status & Durasi Live Independen (1 Detik)
        self.root.after(1000, self._status_timer_tick)
        self._update_page_ui()

        # Cek jika RTSP masih default, tawarkan buka pengaturan
        if any("192.168.1.101" in c.get("rtsp_url", "") for c in self.cfg.get("cameras", [])):
            self.root.after(1000, self.open_settings)

    def _init_cameras(self):
        """Inisialisasi RTSPCameraWorker sesuai daftar kamera dan layout grid yang dipilih"""
        for c in self.cams:
            c.stop()
        self.cams = []

        res_str = self.cfg.get("streaming", {}).get("grid_resolution", "1280x720")
        try:
            gw, gh = map(int, res_str.split("x"))
        except Exception:
            gw, gh = 1280, 720

        patrol_cfg = self.cfg.get("patrol", {})
        layout = patrol_cfg.get("layout", "2x2")
        cols, rows = (3, 3) if layout == "3x3" else (2, 2)
        tile_w = gw // cols
        tile_h = gh // rows

        osd_cfg = self.cfg.get("osd", {})
        try:
            f_scale = float(osd_cfg.get("font_scale", 0.42))
        except Exception:
            f_scale = 0.42
        osd_pos = osd_cfg.get("position", "top_left")
        osd_style = osd_cfg.get("style", "badge_outline")

        cam_cfgs = self.cfg.get("cameras", [])
        if not cam_cfgs:
            cam_cfgs = [{"name": f"Kamera {i+1}", "rtsp_url": ""} for i in range(4)]

        for i, c_data in enumerate(cam_cfgs):
            worker = RTSPCameraWorker(
                cam_id=i+1,
                name=c_data.get("name", f"Kamera {i+1}"),
                rtsp_url=c_data.get("rtsp_url", ""),
                target_width=tile_w,
                target_height=tile_h,
                font_scale=f_scale,
                osd_position=osd_pos,
                osd_style=osd_style,
                auto_resolve_ip=False
            )
            worker.start()
            self.cams.append(worker)

        if hasattr(self, "compositor"):
            self.compositor.update_settings(
                cameras=self.cams,
                patrol_cfg=patrol_cfg,
                resolution=res_str
            )
        if hasattr(self, "_update_page_ui"):
            self._update_page_ui()

    def switch_camera_page(self):
        """Pindah ke halaman kamera berikutnya (Spasi / Tab / PageDown)"""
        if hasattr(self, "compositor") and self.compositor:
            cur, total = self.compositor.next_page()
            self._update_page_ui(cur, total)

    def prev_camera_page(self):
        """Pindah ke halaman kamera sebelumnya (PageUp)"""
        if hasattr(self, "compositor") and self.compositor:
            cur, total = self.compositor.prev_page()
            self._update_page_ui(cur, total)

    def select_camera_page(self, page_idx):
        """Pindah langsung ke nomor halaman tertentu (Tombol 1, 2, 3, 4)"""
        if hasattr(self, "compositor") and self.compositor:
            cur, total = self.compositor.set_page(page_idx)
            self._update_page_ui(cur, total)

    def _update_page_ui(self, cur=None, total=None):
        """Memperbarui teks indikator navigasi halaman kamera di toolbar bawah"""
        if not hasattr(self, "btn_page"):
            return
        if hasattr(self, "compositor") and self.compositor:
            if cur is None or total is None:
                cur, total, patrol_on = self.compositor.get_page_info()
            else:
                _, _, patrol_on = self.compositor.get_page_info()

            if total > 1:
                patrol_tag = " [Auto]" if patrol_on else ""
                self.btn_page.config(
                    text=f"📄 Hal {cur+1}/{total}{patrol_tag} (Spasi)",
                    state="normal"
                )
            else:
                self.btn_page.config(text="📄 Hal 1/1", state="disabled")

    def _youtube_lifecycle_loop(self):
        """
        Mengelola siklus transmisi video multi-tujuan:
        1. Mode YouTube Live (Standar 11 jam & Auto Playlist)
        2. Mode Private RTMP Server (MediaMTX / SRS / NGINX RTMP)
        3. Mode Perekaman Lokal HDD/NAS (Segmentasi MP4 & Auto-Pruning)
        """
        force_fresh = False
        while True:
            # Jika streaming dihentikan manual oleh user (OFFLINE), tunggu sampai user menekan Mulai
            if not self.streaming_enabled:
                self.stream_trigger.clear()
                self.stream_trigger.wait(timeout=2)
                continue

            stream_cfg = self.cfg.get("streaming", {})
            stream_mode = stream_cfg.get("mode", "youtube")
            encoder = stream_cfg.get("encoder", "libx264")
            preset = stream_cfg.get("x264_preset", "ultrafast")
            resolution = stream_cfg.get("grid_resolution", "1280x720")
            fps = stream_cfg.get("fps", 25)
            bitrate = f"{stream_cfg.get('bitrate_kbps', 1800)}k"

            # ----------------------------------------------------
            # MODE 1: PEREKAMAN LOKAL HDD / NAS MANDIRI (Mode Offline)
            # ----------------------------------------------------
            if stream_mode == "local_recording":
                rec_cfg = stream_cfg.get("local_record", {})
                rec_dir = rec_cfg.get("output_dir", "recordings")
                seg_mins = rec_cfg.get("segment_minutes", 15)
                ret_days = rec_cfg.get("retention_days", 14)

                if self.pusher:
                    self.pusher.stop()

                self.pusher = FFmpegStreamPusher(
                    fps=fps,
                    bitrate=bitrate,
                    encoder=encoder,
                    resolution=resolution,
                    preset=preset,
                    mode="local_recording",
                    local_output_dir=rec_dir,
                    segment_minutes=seg_mins,
                    retention_days=ret_days,
                    external_driver=True
                )
                if hasattr(self, "compositor"):
                    self.compositor.update_settings(pusher=self.pusher, fps=fps, resolution=resolution)

                started = self.pusher.start()
                if not started or not self.pusher.running:
                    self.is_streaming = False
                    self.lbl_status_icon.config(text="⚠️ ENCODER ERROR", bg="#450a0a", fg="#ef4444")
                    self.lbl_status_text.config(text="FFmpeg perekaman lokal gagal berjalan! Periksa ffmpeg_log.txt.")
                    self.stream_trigger.clear()
                    self.stream_trigger.wait(timeout=5)
                    continue

                actual_encoder = self.pusher.encoder
                self.pusher_start_time = time.time()
                self.stream_start_time = time.time()
                start_clock = time.strftime('%H:%M:%S', time.localtime(self.stream_start_time))
                self.is_streaming = True
                self.update_status(f"💾 Perekaman Lokal Aktif ({actual_encoder}) -> {rec_dir}/ ({seg_mins}m per part | Auto-Delete {ret_days} hari | Mulai {start_clock} WIB)", is_live=True)
                wait_seconds = 86400

            # ----------------------------------------------------
            # MODE 2: PRIVATE MEDIA SERVER / CUSTOM RTMP (Mode Mandiri)
            # ----------------------------------------------------
            elif stream_mode == "private_rtmp":
                custom_url = stream_cfg.get("custom_rtmp_url", "").strip()
                if not custom_url:
                    self.lbl_status_icon.config(text="⚠️ RTMP KOSONG", bg="#450a0a", fg="#ef4444")
                    self.lbl_status_text.config(text="Target RTMP Server kosong! Buka [F2] lalu tentukan URL RTMP tujuan.")
                    self.stream_trigger.clear()
                    self.stream_trigger.wait(timeout=5)
                    continue

                stream_key = stream_cfg.get("stream_key", "").strip()

                if self.pusher:
                    self.pusher.stop()

                self.pusher = FFmpegStreamPusher(
                    rtmp_url=custom_url,
                    stream_key=stream_key,
                    fps=fps,
                    bitrate=bitrate,
                    encoder=encoder,
                    resolution=resolution,
                    preset=preset,
                    mode="private_rtmp",
                    custom_rtmp_url=custom_url,
                    external_driver=True
                )
                if hasattr(self, "compositor"):
                    self.compositor.update_settings(pusher=self.pusher, fps=fps, resolution=resolution)

                started = self.pusher.start()
                if not started or not self.pusher.running:
                    self.is_streaming = False
                    self.lbl_status_icon.config(text="⚠️ ENCODER ERROR", bg="#450a0a", fg="#ef4444")
                    self.lbl_status_text.config(text="FFmpeg streaming private gagal! Periksa ffmpeg_log.txt.")
                    self.stream_trigger.clear()
                    self.stream_trigger.wait(timeout=5)
                    continue

                actual_encoder = self.pusher.encoder
                self.pusher_start_time = time.time()
                self.stream_start_time = time.time()
                start_clock = time.strftime('%H:%M:%S', time.localtime(self.stream_start_time))
                self.is_streaming = True
                self.update_status(f"🏢 Private Server Live ({actual_encoder}) -> {custom_url} (Mulai {start_clock} WIB)", is_live=True)
                wait_seconds = 86400

            # ----------------------------------------------------
            # MODE 3: YOUTUBE LIVE (Mode A - Standar 11 Jam)
            # ----------------------------------------------------
            else:
                yt_cfg = self.cfg.get("youtube_api", {})
                stream_key = stream_cfg.get("stream_key", "")
                rtmp_url = stream_cfg.get("rtmp_server", "rtmp://a.rtmp.youtube.com/live2")
                api_error = None

                # Jika YouTube API Aktif: buat / hubungkan broadcast
                if yt_cfg.get("enabled", False) and self.streaming_enabled:
                    try:
                        try:
                            from posronda.network.youtube_manager import YouTubeManager
                        except ImportError:
                            from youtube_manager import YouTubeManager
                        if not self.youtube_mgr:
                            self.youtube_mgr = YouTubeManager(self.cfg)
                            self.youtube_mgr.authenticate()

                        self.update_status("Menghubungkan ke YouTube Live...", is_live=False)

                        broadcast_info = None
                        if not force_fresh:
                            try:
                                broadcast_info = self.youtube_mgr.find_existing_upcoming_broadcast()
                                if broadcast_info:
                                    print(f"[YouTube API] Menggunakan siaran upcoming yang sudah siap: {broadcast_info['title']}")
                            except Exception as fe:
                                print(f"[YouTube API] Info cek upcoming: {fe}")

                        if not broadcast_info:
                            broadcast_info = self.youtube_mgr.create_broadcast_and_stream(force_new=force_fresh)

                        force_fresh = False
                        self.current_broadcast = broadcast_info
                        stream_key = broadcast_info["stream_key"]
                        rtmp_url = broadcast_info["rtmp_url"]

                        if stream_key and stream_key != stream_cfg.get("stream_key", ""):
                            self.cfg["streaming"]["stream_key"] = stream_key
                            config_manager.save_config(self.cfg)

                        self.update_status(f"Siaran siap: {broadcast_info['title']} (Menyiapkan encoder...)", is_live=False)
                    except Exception as e:
                        api_error = str(e)
                        print(f"[YouTube API Error] {e}")
                        if not stream_key:
                            stream_key = stream_cfg.get("stream_key", "")
                        if stream_key:
                            self.update_status(f"YouTube API Error ({e}). Menggunakan Stream Key cadangan...", is_live=False)

                if stream_key and self.streaming_enabled:
                    if self.pusher:
                        self.pusher.stop()

                    self.pusher = FFmpegStreamPusher(
                        rtmp_url=rtmp_url,
                        stream_key=stream_key,
                        fps=fps,
                        bitrate=bitrate,
                        encoder=encoder,
                        resolution=resolution,
                        preset=preset,
                        mode="youtube",
                        external_driver=True
                    )
                    if hasattr(self, "compositor"):
                        self.compositor.update_settings(pusher=self.pusher, fps=fps, resolution=resolution)

                    started = self.pusher.start()

                    if not started or not self.pusher.running:
                        self.is_streaming = False
                        self.lbl_status_icon.config(text="⚠️ ENCODER ERROR", bg="#450a0a", fg="#ef4444")
                        self.lbl_status_text.config(text="FFmpeg gagal berjalan! Periksa ffmpeg_log.txt.")
                        self.stream_trigger.clear()
                        self.stream_trigger.wait(timeout=5)
                        continue

                    actual_encoder = self.pusher.encoder
                    self.pusher_start_time = time.time()
                    self.stream_start_time = time.time()
                    start_clock = time.strftime('%H:%M:%S', time.localtime(self.stream_start_time))

                    if not yt_cfg.get("enabled", False) or not self.current_broadcast:
                        self.is_streaming = True
                        self.update_status(f"Streaming Manual ({actual_encoder} @ {fps}fps) -> YouTube (Mulai {start_clock} WIB)", is_live=True)
                    else:
                        self.is_streaming = False
                        self.lbl_status_icon.config(text=f"🟡 CONNECTING (Mulai {start_clock})", bg="#451a03", fg="#f59e0b")
                        self.lbl_status_text.config(text=f"Mengalirkan video ({actual_encoder}) ke YouTube, memverifikasi siaran...")

                    if self.youtube_mgr and self.current_broadcast:
                        b_id = self.current_broadcast.get("broadcast_id")
                        s_id = self.current_broadcast.get("stream_id")
                        def run_watcher():
                            def on_live():
                                def _apply_live():
                                    self.is_streaming = True
                                    start_str = time.strftime('%H:%M:%S', time.localtime(self.stream_start_time or time.time()))
                                    if self.current_broadcast:
                                        self.update_status(f"RESMI LIVE: {self.current_broadcast.get('title', '')} (Mulai {start_str} WIB)", is_live=True)
                                self.root.after(0, _apply_live)

                            def on_progress(msg):
                                def _apply_prog():
                                    self.lbl_status_text.config(text=msg)
                                self.root.after(0, _apply_prog)

                            if self.youtube_mgr:
                                self.youtube_mgr.wait_for_stream_and_transition(
                                    b_id, s_id, 
                                    on_live_callback=on_live,
                                    on_progress_callback=on_progress
                                )
                        threading.Thread(target=run_watcher, daemon=True).start()

                    max_hours = stream_cfg.get("max_duration_hours", 11)
                    lead_mins = stream_cfg.get("rollover_lead_minutes", 5)
                    wait_seconds = max((max_hours * 3600) - (lead_mins * 60), 60)
                else:
                    if self.streaming_enabled:
                        if api_error:
                            if "403" in api_error or "exceed" in api_error.lower() or "quota" in api_error.lower():
                                self.lbl_status_icon.config(text="⚠️ KUOTA API HABIS (403)", bg="#451a03", fg="#f59e0b")
                                self.lbl_status_text.config(text="Kuota harian YouTube API habis (Error 403). Buka [F2] lalu tempel Stream Key dari YouTube Studio agar langsung LIVE tanpa kuota!")
                            else:
                                self.lbl_status_icon.config(text="⚠️ YOUTUBE API ERROR", bg="#450a0a", fg="#ef4444")
                                self.lbl_status_text.config(text=f"Gagal buat siaran: {api_error}. Buka [F2] untuk Stream Key manual.")
                        else:
                            self.lbl_status_icon.config(text="⚠️ STREAM KEY KOSONG", bg="#450a0a", fg="#ef4444")
                            self.lbl_status_text.config(text="Stream Key kosong! Tekan [F2] untuk mengisi Stream Key YouTube Anda.")
                    wait_seconds = 5

            # Tunggu dengan event interruptible (bisa dibangunkan seketika jika ada restart/stop/save)
            self.stream_trigger.clear()
            interrupted = self.stream_trigger.wait(timeout=wait_seconds)

            if not self.streaming_enabled:
                if self.pusher:
                    self.pusher.stop()
                    self.pusher = None
                    if hasattr(self, "compositor"):
                        self.compositor.update_settings(pusher=None)
                continue

            if self.restart_requested:
                self.restart_requested = False
                if stream_mode == "youtube" and self.youtube_mgr and self.current_broadcast:
                    self.update_status("Menutup siaran lama untuk memulai siaran baru...", is_live=False)
                    old_id = self.current_broadcast.get("broadcast_id")
                    self.youtube_mgr.end_broadcast(old_id)
                force_fresh = True
                continue

            # Jika waktu 11 jam habis secara normal (khusus mode YouTube):
            if not interrupted and stream_mode == "youtube" and self.youtube_mgr and self.current_broadcast:
                self.update_status("Batas 11 jam tercapai. Menutup siaran lama & menyiapkan siaran baru...", is_live=False)
                old_id = self.current_broadcast.get("broadcast_id")
                self.youtube_mgr.end_broadcast(old_id)
                force_fresh = True

    def toggle_pause(self):
        """Menjeda atau melanjutkan push streaming / perekaman (F6)"""
        if not self.streaming_enabled or not self.is_streaming:
            messagebox.showinfo("Informasi", "Streaming / Perekaman sedang tidak aktif.")
            return

        stream_mode = self.cfg.get("streaming", {}).get("mode", "youtube")
        self.is_paused = not self.is_paused
        if self.pusher:
            if self.is_paused:
                self.pusher.pause()
            else:
                self.pusher.resume()

        if self.is_paused:
            if stream_mode == "local_recording":
                self.update_status("⏸️ Perekaman lokal DIJEDA (Kamera lokal tetap dipantau)")
            elif stream_mode == "private_rtmp":
                self.update_status("⏸️ Streaming ke Private Server DIJEDA (Layar standby aktif)")
            else:
                self.update_status("⏸️ Streaming DIJEDA ke YouTube (Layar standby aktif | Kamera lokal normal)")
        else:
            if stream_mode == "local_recording":
                self.update_status("▶️ Perekaman lokal DILANJUTKAN")
            elif stream_mode == "private_rtmp":
                self.update_status("▶️ Streaming DILANJUTKAN ke Private Server")
            else:
                self.update_status("▶️ Streaming DILANJUTKAN ke YouTube")

    def end_streaming(self):
        """Mengakhiri siaran streaming / rekaman atau memulai dari kondisi offline (F7)"""
        stream_mode = self.cfg.get("streaming", {}).get("mode", "youtube")
        mode_label = "Perekaman Lokal" if stream_mode == "local_recording" else ("Private RTMP Server" if stream_mode == "private_rtmp" else "YouTube Live")

        if not self.streaming_enabled:
            self.start_streaming()
            return

        if not messagebox.askyesno(
            f"Konfirmasi Akhiri {mode_label}",
            f"Apakah Anda yakin ingin MENGAKHIRI {mode_label} sekarang?\n\n"
            f"• Sesi {mode_label} akan ditutup rapi dan disimpan.\n"
            f"• Monitoring seluruh kamera di laptop ini akan TETAP BERJALAN normal."
        ):
            return

        self.streaming_enabled = False
        self.is_streaming = False
        self.is_paused = False

        if self.pusher:
            self.pusher.stop()
            self.pusher = None
            if hasattr(self, "compositor"):
                self.compositor.update_settings(pusher=None)

        if stream_mode == "youtube" and self.youtube_mgr and self.current_broadcast:
            b_id = self.current_broadcast.get("broadcast_id")
            def do_end():
                try:
                    self.youtube_mgr.end_broadcast(b_id)
                except Exception as e:
                    print(f"Error ending broadcast: {e}")
            threading.Thread(target=do_end, daemon=True).start()
            self.current_broadcast = None

        self.stream_trigger.set()
        self.update_status(f"{mode_label} telah diakhiri. Monitoring kamera lokal aktif.", is_live=False)

    def start_streaming(self):
        """Memulai kembali streaming / rekaman dari kondisi offline"""
        stream_mode = self.cfg.get("streaming", {}).get("mode", "youtube")
        mode_label = "Perekaman Lokal" if stream_mode == "local_recording" else ("Private Server" if stream_mode == "private_rtmp" else "YouTube")
        self.streaming_enabled = True
        self.is_paused = False
        self.restart_requested = False
        self.stream_start_time = time.time()
        self.stream_trigger.set()
        self.update_status(f"Menghubungkan & memulai {mode_label}...", is_live=False)

    def restart_streaming(self):
        """Memulai ulang siaran streaming / rekaman (F5)"""
        stream_mode = self.cfg.get("streaming", {}).get("mode", "youtube")
        mode_label = "Perekaman Lokal" if stream_mode == "local_recording" else ("Streaming Private" if stream_mode == "private_rtmp" else "YouTube Live")

        if not self.streaming_enabled:
            self.start_streaming()
            return

        if not messagebox.askyesno(
            "Konfirmasi Mulai Ulang",
            f"Mulai ulang {mode_label} sekarang?\n\n"
            f"Sesi saat ini akan ditutup rapi dan digantikan dengan sesi baru."
        ):
            return

        self.update_status(f"Memulai ulang {mode_label}...", is_live=False)
        self.is_paused = False
        self.restart_requested = True
        if self.pusher:
            self.pusher.stop()
            self.pusher = None
            if hasattr(self, "compositor"):
                self.compositor.update_settings(pusher=None)
        self.stream_trigger.set()

    def _get_camera_at_pos(self, x, y):
        """Mendeteksi objek kamera berdasarkan posisi koordinat klik di Canvas & halaman aktif"""
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        gw, gh = 1280, 720
        layout = self.cfg.get("patrol", {}).get("layout", "2x2")
        cols, rows = (3, 3) if layout == "3x3" else (2, 2)
        if hasattr(self, "compositor") and self.compositor:
            gw, gh = self.compositor.gw, self.compositor.gh
            cols = 3 if self.compositor.layout == "3x3" else 2
            rows = cols

        offset_x = max((cw - gw) // 2, 0)
        offset_y = max((ch - gh) // 2, 0)

        rel_x = x - offset_x
        rel_y = y - offset_y

        col_w = max(1, gw // cols)
        row_h = max(1, gh // rows)

        if rel_x < 0:
            col = min(max(0, x // max(cw // cols, 1)), cols - 1)
        elif rel_x >= gw:
            col = cols - 1
        else:
            col = min(rel_x // col_w, cols - 1)

        if rel_y < 0:
            row = min(max(0, y // max(ch // rows, 1)), rows - 1)
        elif rel_y >= gh:
            row = rows - 1
        else:
            row = min(rel_y // row_h, rows - 1)

        slot_in_page = int(row * cols + col)
        cur_page = getattr(self.compositor, "current_page", 0) if hasattr(self, "compositor") else 0
        cams_per_page = cols * rows
        cam_idx = cur_page * cams_per_page + slot_in_page

        if 0 <= cam_idx < len(self.cams):
            return cam_idx, self.cams[cam_idx]
        return None, None

    def on_canvas_double_tap(self, event):
        """Fitur Tap-Tap (Double Click) pada kuadran kamera untuk merefresh/reconnect seketika"""
        cam_idx, cam = self._get_camera_at_pos(event.x, event.y)
        if cam:
            print(f"[UI] Double-tap terdeteksi pada {cam.name}. Memulai reconnect...")
            cam.refresh()
            self.lbl_status_text.config(text=f"🔄 Merefresh & menghubungkan ulang {cam.name}...")

    def on_canvas_single_tap(self, event):
        """Jika kamera sedang OFFLINE / Gagal Konek / Putus, sekali klik langsung memicu refresh"""
        cam_idx, cam = self._get_camera_at_pos(event.x, event.y)
        if cam and cam.status != "ONLINE":
            print(f"[UI] Tap terdeteksi pada {cam.name} ({cam.status}). Memulai reconnect...")
            cam.refresh()
            self.lbl_status_text.config(text=f"🔄 Menghubungkan ulang {cam.name}...")

    def on_canvas_right_click(self, event):
        """Menu klik-kanan cepat untuk kendali kamera individual"""
        cam_idx, cam = self._get_camera_at_pos(event.x, event.y)
        menu = tk.Menu(self.root, tearoff=0, bg="#1e293b", fg="#e2e8f0", activebackground="#3b82f6", activeforeground="#ffffff")
        if cam:
            menu.add_command(label=f"🔄 Refresh {cam.name} (Tap 2x)", command=lambda: self._refresh_single_camera(cam))
            menu.add_separator()
        menu.add_command(label=f"🔄 Refresh Seluruh Kamera ({len(self.cams)})", command=self.refresh_all_cameras)
        menu.add_command(label="📄 Ganti Halaman Kamera (Spasi)", command=self.switch_camera_page)
        menu.add_separator()
        menu.add_command(label="⚙️ Buka Pengaturan CCTV (F2)", command=self.open_settings)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _refresh_single_camera(self, cam):
        cam.refresh()
        self.lbl_status_text.config(text=f"🔄 Merefresh & menghubungkan ulang {cam.name}...")

    def refresh_all_cameras(self):
        for c in self.cams:
            c.refresh()
        self.lbl_status_text.config(text=f"🔄 Merefresh seluruh {len(self.cams)} feed kamera...")

    def update_frame_loop(self):
        try:
            # OBS Zero-Overhead Rendering: In-place PhotoImage.paste (Sub-millisecond Win32 DIB Update)
            gui_rgb = self.compositor.get_latest_gui_frame()
            if gui_rgb is not None:
                gh, gw, _ = gui_rgb.shape
                # Gunakan Image.frombuffer agar ZERO-COPY tanpa alokasi heap dari numpy ke PIL!
                pil_img = Image.frombuffer("RGB", (gw, gh), gui_rgb, "raw", "RGB", 0, 1)

                cw = self.canvas.winfo_width()
                ch = self.canvas.winfo_height()
                offset_x = max((cw - gw) // 2, 0)
                offset_y = max((ch - gh) // 2, 0)

                if self.tk_photo is None or getattr(self, "_last_dims", None) != (gw, gh):
                    self.tk_photo = ImageTk.PhotoImage(image=pil_img)
                    self._last_dims = (gw, gh)
                    if self.canvas_img_id is None:
                        self.canvas_img_id = self.canvas.create_image(offset_x, offset_y, anchor="nw", image=self.tk_photo)
                    else:
                        self.canvas.coords(self.canvas_img_id, offset_x, offset_y)
                        self.canvas.itemconfig(self.canvas_img_id, image=self.tk_photo)
                    self._last_offset = (offset_x, offset_y)
                else:
                    self.tk_photo.paste(pil_img)
                    if getattr(self, "_last_offset", None) != (offset_x, offset_y):
                        self.canvas.coords(self.canvas_img_id, offset_x, offset_y)
                        self._last_offset = (offset_x, offset_y)

        except Exception:
            pass

        self.root.after(self.render_interval_ms, self.update_frame_loop)

    def _status_timer_tick(self):
        """Timer independen 1 detik untuk memantau status streaming & menghitung durasi LIVE secara real-time"""
        try:
            self._update_page_ui()
            stream_mode = self.cfg.get("streaming", {}).get("mode", "youtube")

            if not self.streaming_enabled:
                self.lbl_status_icon.config(text="⚪ OFFLINE", bg="#1e293b", fg="#94a3b8")
                start_btn_text = "💾 Mulai Rekam (F7)" if stream_mode == "local_recording" else "▶️ Mulai Stream (F7)"
                self.btn_end.config(text=start_btn_text, bg="#15803d", activebackground="#16a34a")
                self.btn_pause.config(state="disabled", text="⏸️ Jeda (F6)", bg="#334155")
            elif self.is_paused:
                self.lbl_status_icon.config(text="⏸️ DIJEDA", bg="#451a03", fg="#fbbf24")
                self.btn_end.config(text="⏹️ Akhiri (F7)", bg="#b91c1c", activebackground="#dc2626")
                self.btn_pause.config(state="normal", text="▶️ Lanjutkan (F6)", bg="#15803d", activebackground="#16a34a")
            elif self.pusher and self.pusher.running:
                # Cek jika proses FFmpeg crash / tertutup
                if self.pusher.process and self.pusher.process.poll() is not None:
                    exit_code = self.pusher.process.poll()
                    self.is_streaming = False
                    self.lbl_status_icon.config(text="⚠️ ENCODER ERROR", bg="#450a0a", fg="#ef4444")
                    self.lbl_status_text.config(text=f"FFmpeg tertutup (Kode: {exit_code})! Periksa ffmpeg_log.txt.")
                else:
                    # Auto-promote ke LIVE jika FFmpeg sudah aktif mengalir stabil > 3 detik
                    if not self.is_streaming and self.pusher_start_time > 0 and (time.time() - self.pusher_start_time) >= 3.0:
                        self.is_streaming = True
                        start_clock = time.strftime('%H:%M:%S', time.localtime(self.stream_start_time or time.time()))
                        if stream_mode == "local_recording":
                            rec_dir = self.cfg.get("streaming", {}).get("local_record", {}).get("output_dir", "recordings")
                            self.lbl_status_text.config(text=f"💾 PEREKAMAN AKTIF: Menyimpan video lokal ke {rec_dir}/ (Mulai {start_clock} WIB)")
                        elif stream_mode == "private_rtmp":
                            target_url = self.cfg.get("streaming", {}).get("custom_rtmp_url", "Private Server")
                            self.lbl_status_text.config(text=f"🏢 PRIVATE LIVE: Mengalir ke {target_url} (Mulai {start_clock} WIB)")
                        else:
                            title = self.current_broadcast.get('title', 'PosRonda Live') if self.current_broadcast else "Streaming PosRonda"
                            self.lbl_status_text.config(text=f"RESMI LIVE: {title} (Tayang sejak {start_clock} WIB)")

                    if self.is_streaming:
                        elapsed_sec = int(time.time() - (self.stream_start_time or time.time()))
                        hh = elapsed_sec // 3600
                        mm = (elapsed_sec % 3600) // 60
                        ss = elapsed_sec % 60

                        if stream_mode == "local_recording":
                            self.lbl_status_icon.config(
                                text=f"💾 REKAM ({hh:02d}:{mm:02d}:{ss:02d})", 
                                bg="#064e3b",
                                fg="#34d399"
                            )
                        elif stream_mode == "private_rtmp":
                            self.lbl_status_icon.config(
                                text=f"🏢 PRIVATE ({hh:02d}:{mm:02d}:{ss:02d})", 
                                bg="#312e81",
                                fg="#a5b4fc"
                            )
                        else:
                            self.lbl_status_icon.config(
                                text=f"● LIVE ({hh:02d}:{mm:02d}:{ss:02d})", 
                                bg="#450a0a",
                                fg="#ef4444"
                            )
                        self.btn_end.config(text="⏹️ Akhiri (F7)", bg="#b91c1c", activebackground="#dc2626")
                        self.btn_pause.config(state="normal", text="⏸️ Jeda (F6)", bg="#b45309", activebackground="#d97706")
                    else:
                        self.lbl_status_icon.config(text=f"🟡 CONNECTING", bg="#451a03", fg="#f59e0b")
                        self.btn_end.config(text="⏹️ Akhiri (F7)", bg="#b91c1c", activebackground="#dc2626")
                        self.btn_pause.config(state="disabled", text="⏸️ Jeda (F6)", bg="#334155")
        except Exception:
            pass

        self.root.after(1000, self._status_timer_tick)

    def update_status(self, text, is_live=None):
        if is_live is not None:
            self.is_streaming = is_live

        stream_mode = self.cfg.get("streaming", {}).get("mode", "youtube")

        if not self.streaming_enabled:
            self.lbl_status_icon.config(text="⚪ OFFLINE", bg="#1e293b", fg="#94a3b8")
            start_btn_text = "💾 Mulai Rekam (F7)" if stream_mode == "local_recording" else "▶️ Mulai Stream (F7)"
            self.btn_end.config(text=start_btn_text, bg="#15803d", activebackground="#16a34a")
            self.btn_pause.config(state="disabled", text="⏸️ Jeda (F6)", bg="#334155")
        elif not self.is_streaming:
            self.lbl_status_icon.config(text=f"🟡 CONNECTING", bg="#451a03", fg="#f59e0b")
            self.btn_end.config(text="⏹️ Akhiri (F7)", bg="#b91c1c", activebackground="#dc2626")
            self.btn_pause.config(state="disabled", text="⏸️ Jeda (F6)", bg="#334155")
        elif self.is_paused:
            self.lbl_status_icon.config(text="⏸️ DIJEDA", bg="#451a03", fg="#fbbf24")
            self.btn_end.config(text="⏹️ Akhiri (F7)", bg="#b91c1c", activebackground="#dc2626")
            self.btn_pause.config(state="normal", text="▶️ Lanjutkan (F6)", bg="#15803d", activebackground="#16a34a")
        else:
            elapsed_sec = int(time.time() - (self.stream_start_time or time.time()))
            hh = elapsed_sec // 3600
            mm = (elapsed_sec % 3600) // 60
            ss = elapsed_sec % 60
            if stream_mode == "local_recording":
                self.lbl_status_icon.config(
                    text=f"💾 REKAM ({hh:02d}:{mm:02d}:{ss:02d})", 
                    bg="#064e3b",
                    fg="#34d399"
                )
            elif stream_mode == "private_rtmp":
                self.lbl_status_icon.config(
                    text=f"🏢 PRIVATE ({hh:02d}:{mm:02d}:{ss:02d})", 
                    bg="#312e81",
                    fg="#a5b4fc"
                )
            else:
                self.lbl_status_icon.config(
                    text=f"● LIVE ({hh:02d}:{mm:02d}:{ss:02d})", 
                    bg="#450a0a",
                    fg="#ef4444"
                )
            self.btn_end.config(text="⏹️ Akhiri (F7)", bg="#b91c1c", activebackground="#dc2626")
            self.btn_pause.config(state="normal", text="⏸️ Jeda (F6)", bg="#b45309", activebackground="#d97706")

        self.lbl_status_text.config(text=text)

    def open_about_dialog(self):
        lic = LicenseManager.get_license_info()
        dlg = tk.Toplevel(self.root)
        dlg.title("Tentang PosRonda - Semi Open-Source (Model WinRAR)")
        dlg.geometry("540x440")
        dlg.resizable(False, False)
        dlg.configure(bg="#0b0f19")
        dlg.transient(self.root)
        dlg.grab_set()

        f_card = tk.Frame(dlg, bg="#1e293b", padx=20, pady=18, highlightthickness=1, highlightbackground="#334155")
        f_card.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(f_card, text="🛡️ PosRonda Hub v4.0", bg="#1e293b", fg="#818cf8", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(f_card, text="Autonomous CCTV Multi-Camera Hub & Live Streaming Engine", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 10))

        # Status Lisensi Box
        f_st = tk.Frame(f_card, bg="#0f172a", padx=12, pady=8)
        f_st.pack(fill="x", pady=4)
        tk.Label(f_st, text=f"💎 Edisi: {lic.get('tier_name')}", bg="#0f172a", fg="#38bdf8", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(f_st, text=f"Status: {lic.get('status_text')}", bg="#0f172a", fg="#cbd5e1", font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(f_st, text=f"Pemegang: {lic.get('holder')} ({lic.get('org')})", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 8)).pack(anchor="w")

        # Filosofi ala WinRAR
        tk.Label(
            f_card,
            text="Filosofi Lisensi Semi Open-Source (Model WinRAR):\n"
                 "• PosRonda Community Edition dapat digunakan secara GRATIS selamanya tanpa batasan fitur monitoring "
                 "dan tanpa pernah kedaluwarsa oleh warga, RT/RW, masjid, dan pos siskamling.\n\n"
                 "• Untuk teknisi CCTV & installer komersial, silakan gunakan PosRonda PRO untuk mendapatkan fitur White-Labeling, "
                 "Watermark logo perusahaan Anda sendiri, dan Kunci PIN installer.",
            bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 8), justify="left", wraplength=470
        ).pack(anchor="w", pady=(10, 14))

        # Tombol Aksi
        f_btns = tk.Frame(f_card, bg="#1e293b")
        f_btns.pack(fill="x")

        tk.Button(
            f_btns, text="Tutup", bg="#334155", fg="#ffffff", relief="flat", font=("Segoe UI", 8),
            padx=12, pady=4, cursor="hand2", command=dlg.destroy
        ).pack(side="right", padx=(4, 0))

        tk.Button(
            f_btns, text="⚙️ Pengaturan & Lisensi", bg="#0284c7", fg="#ffffff", relief="flat", font=("Segoe UI", 8, "bold"),
            padx=12, pady=4, cursor="hand2", command=lambda: [dlg.destroy(), self.open_settings()]
        ).pack(side="right")

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self):
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)

    def open_settings(self):
        def on_saved(new_cfg):
            self.cfg = new_cfg
            config_manager.save_config(new_cfg)
            new_fps = new_cfg.get("streaming", {}).get("fps", 25)
            new_res = new_cfg.get("streaming", {}).get("grid_resolution", "1280x720")
            enc_lbl = "QSV GPU" if new_cfg.get("streaming", {}).get("encoder") == "h264_qsv" else "CPU"
            
            stream_mode = new_cfg.get("streaming", {}).get("mode", "youtube")
            mode_lbl = "YT Live" if stream_mode == "youtube" else ("Private RTMP" if stream_mode == "private_rtmp" else "HDD/NAS")

            if hasattr(self, "lbl_spec_badge"):
                self.lbl_spec_badge.config(text=f"{new_res} • {new_fps}fps • {enc_lbl} • {mode_lbl}")
            self.render_interval_ms = max(int(1000 / new_fps), 25)
            self.tk_photo = None
            self._last_dims = None
            self._last_offset = None
            self._init_cameras()
            if hasattr(self, "compositor"):
                self.compositor.update_settings(
                    cameras=self.cams,
                    fps=new_fps,
                    resolution=new_res,
                    patrol_cfg=new_cfg.get("patrol", {})
                )
            self._update_page_ui()
            # Bangunkan thread streaming agar langsung memulai transmisi dengan pengaturan baru
            self.stream_trigger.set()
            messagebox.showinfo("Berhasil", "Pengaturan PosRonda disimpan. Kamera & Live Streaming di-refresh!")

        SettingsDialog(self.root, self.cfg, on_saved)

    def on_closing(self):
        # Bersihkan semua proses saat aplikasi ditutup
        if hasattr(self, "compositor"):
            self.compositor.stop()
        for c in self.cams:
            c.stop()
        if self.pusher:
            self.pusher.stop()
        if self.youtube_mgr and self.current_broadcast:
            try:
                self.youtube_mgr.end_broadcast(self.current_broadcast.get("broadcast_id"))
            except Exception:
                pass
        self.root.destroy()
        sys.exit(0)

def main():
    # 1. Pre-flight check (Deteksi Python & FFmpeg)
    ready = check_env.run_check(show_gui_if_missing=True)
    if not ready:
        sys.exit(1)

    root = tk.Tk()
    app = CCTVApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
