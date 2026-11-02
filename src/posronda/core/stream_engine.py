"""
Streaming Engine & Camera Watchdog
Mengelola 4 feed RTSP, Watchdog anti-freeze, compositing 2x2 grid, dan pipe ke FFmpeg (Intel QuickSync).
"""

import os
import sys
import shutil

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
import subprocess
import cv2
import numpy as np

def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "config.json")):
        return cwd
    this_dir = os.path.dirname(os.path.abspath(__file__))
    root_candidate = os.path.abspath(os.path.join(this_dir, "..", "..", ".."))
    if os.path.exists(os.path.join(root_candidate, "config.json")):
        return root_candidate
    return cwd

def draw_patrol_badge(img, text):
    """Menggambar badge halaman patrol di bagian atas tengah kanvas"""
    h, w = img.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.42
    thickness = 1
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
    pad_x, pad_y = 10, 4
    x1 = (w - tw) // 2 - pad_x
    y1 = 8
    x2 = x1 + tw + (pad_x * 2)
    y2 = y1 + th + (pad_y * 2)
    # Latar belakang gelap transparan & outline cyan
    cv2.rectangle(img, (x1, y1), (x2, y2), (15, 23, 42), -1)
    cv2.rectangle(img, (x1, y1), (x2, y2), (56, 189, 248), 1)
    cv2.putText(img, text, (x1 + pad_x, y2 - pad_y), font, scale, (248, 250, 252), thickness, cv2.LINE_AA)

def clean_old_recordings(output_dir, retention_days=14):
    """Menghapus file rekaman .mp4 lokal yang lebih lama dari retention_days"""
    if not output_dir or not os.path.exists(output_dir):
        return
    try:
        cutoff = time.time() - (retention_days * 86400)
        for fname in os.listdir(output_dir):
            if fname.lower().endswith(".mp4"):
                fpath = os.path.join(output_dir, fname)
                if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
                    try:
                        os.remove(fpath)
                        print(f"[PosRonda Storage] Menghapus rekaman lama: {fname}")
                    except Exception:
                        pass
    except Exception as e:
        print(f"[PosRonda Storage] Gagal membersihkan rekaman: {e}")

def draw_cctv_osd(img, text, font_scale=0.42, position="top_left", style="badge_outline"):
    """
    Standar OSD CCTV Profesional:
    Otomatis menyesuaikan dengan background apa pun dan ukuran proporsional:
    1. Badge latar belakang abu gelap (anti-silau saat background putih/terang)
    2. Garis tepi hitam tebal (stroke)
    3. Teks putih kristal terang (kontras tajam saat malam/gelap)
    """
    if position == "none":
        return

    font = cv2.FONT_HERSHEY_SIMPLEX
    h, w, _ = img.shape
    (tw, th), baseline = cv2.getTextSize(text, font, font_scale, 1)
    pad = 3

    if position == "bottom_left":
        x, y = 12, h - 10
    elif position == "top_right":
        x, y = max(w - tw - 12, 5), 18
    elif position == "bottom_right":
        x, y = max(w - tw - 12, 5), h - 10
    else: # top_left (default)
        x, y = 12, 18

    if style == "badge_outline":
        cv2.rectangle(img, (x - pad, y - th - pad), (x + tw + pad, y + pad), (15, 15, 20), -1)
        cv2.rectangle(img, (x - pad, y - th - pad), (x + tw + pad, y + pad), (60, 60, 70), 1)
        cv2.putText(img, text, (x, y), font, font_scale, (0, 0, 0), 2, cv2.LINE_8)
        cv2.putText(img, text, (x, y), font, font_scale, (255, 255, 255), 1, cv2.LINE_8)
    elif style == "retro_green":
        cv2.putText(img, text, (x, y), font, font_scale, (0, 0, 0), 2, cv2.LINE_8)
        cv2.putText(img, text, (x, y), font, font_scale, (0, 255, 0), 1, cv2.LINE_8)
    else: # clean_outline
        cv2.putText(img, text, (x, y), font, font_scale, (0, 0, 0), 2, cv2.LINE_8)
        cv2.putText(img, text, (x, y), font, font_scale, (255, 255, 255), 1, cv2.LINE_8)


class RTSPCameraWorker(threading.Thread):
    def __init__(self, cam_id, name, rtsp_url, target_width=640, target_height=360, font_scale=0.42, osd_position="top_left", osd_style="badge_outline", auto_resolve_ip=False):
        super().__init__(daemon=True)
        self.cam_id = cam_id
        self.name = name
        self.rtsp_url = rtsp_url
        self.target_w = target_width
        self.target_h = target_height
        self.font_scale = font_scale
        self.osd_pos = osd_position
        self.osd_style = osd_style
        self.auto_resolve_ip = False
        
        self.current_frame = None
        self.status = "Menghubungkan..."
        self.last_frame_time = 0
        self.running = True
        self.lock = threading.Lock()
        self.failed_connects = 0
        self.refresh_requested = False
        self._last_osd_sec = -1
        self._cached_osd_text = None

    def refresh(self):
        """Memaksa kamera melakukan reconnect / refresh seketika (Dipicu oleh Double Tap / Klik)"""
        self.status = "Merefresh Kamera..."
        self.current_frame = self._generate_placeholder("Merefresh Kamera...")
        self.refresh_requested = True
        self.failed_connects = 0

    def run(self):
        while self.running:
            if not self.rtsp_url or not self.rtsp_url.startswith("rtsp://"):
                self.status = "URL Belum Disetel"
                self.current_frame = self._generate_placeholder("URL Kosong")
                time.sleep(2)
                continue

            self.status = "Menyambungkan..."
            self.current_frame = self._generate_placeholder("Menghubungkan...")

            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                self.failed_connects += 1
                self.status = f"Gagal Konek ({self.failed_connects}x)"
                self.current_frame = self._generate_placeholder("Gagal Terhubung (Retry...)")
                time.sleep(2)
                continue

            self.failed_connects = 0
            self.status = "ONLINE"
            self.last_frame_time = time.time()

            while self.running and cap.isOpened():
                if self.refresh_requested:
                    self.refresh_requested = False
                    print(f"[{self.name}] Refresh diminta pengguna. Menghubungkan ulang seketika...")
                    break

                ret, frame = cap.read()
                now = time.time()

                if not ret or frame is None:
                    if now - self.last_frame_time > 3.0:
                        self.status = "Kamera Putus (Reconnecting...)"
                        self.current_frame = self._generate_placeholder("Koneksi Hilang...")
                        break
                    time.sleep(0.01)
                    continue

                self.last_frame_time = now

                # Hindari memodifikasi internal buffer OpenCV langsung (wajib copy agar P-frames tidak korup/bengong)
                fh, fw = frame.shape[:2]
                if fw == self.target_w and fh == self.target_h:
                    resized = frame.copy()
                else:
                    resized = cv2.resize(frame, (self.target_w, self.target_h), interpolation=cv2.INTER_NEAREST)

                # Optimasi: Cache format teks OSD per detik (menghemat CPU)
                cur_sec = int(now)
                if cur_sec != self._last_osd_sec or self._cached_osd_text is None:
                    self._last_osd_sec = cur_sec
                    self._cached_osd_text = f"{self.name} - {time.strftime('%H:%M:%S', time.localtime(now))}"

                # Gambar label OSD adaptif yang proporsional dan selalu terbaca
                draw_cctv_osd(resized, self._cached_osd_text, font_scale=self.font_scale, position=self.osd_pos, style=self.osd_style)

                # Assignment atomik bebas lock
                self.current_frame = resized
                self.status = "ONLINE"

            cap.release()
            if self.refresh_requested:
                self.refresh_requested = False
                continue
            time.sleep(1.0)

    def get_frame_direct(self, target_buf=None):
        """
        Atomic reference read tanpa mutex lock (zero lock contention).
        Jika target_buf diberikan (slice numpy), C-memcpy langsung ke buffer tujuan!
        """
        src = self.current_frame
        if src is None:
            src = self._generate_placeholder(self.status)

        if target_buf is not None:
            try:
                if target_buf.shape == src.shape:
                    np.copyto(target_buf, src)
                else:
                    cv2.resize(src, (target_buf.shape[1], target_buf.shape[0]), dst=target_buf, interpolation=cv2.INTER_NEAREST)
            except Exception:
                pass
            return target_buf
        return src

    def get_frame(self):
        src = self.current_frame
        if src is None:
            return self._generate_placeholder(self.status)
        return src

    def _generate_placeholder(self, text):
        if hasattr(self, "_cached_placeholder_text") and self._cached_placeholder_text == text:
            if hasattr(self, "_cached_placeholder_img") and self._cached_placeholder_img is not None:
                return self._cached_placeholder_img

        img = np.zeros((self.target_h, self.target_w, 3), dtype=np.uint8)
        # Background abu gelap
        img[:] = (30, 30, 35)
        # Kotak pembatas
        cv2.rectangle(img, (5, 5), (self.target_w - 5, self.target_h - 5), (60, 60, 70), 2)
        # Teks status
        cv2.putText(
            img, 
            f"[{self.name}]", 
            (50, self.target_h // 2 - 20), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.0, 
            (255, 255, 255), 
            2, 
            cv2.LINE_AA
        )
        cv2.putText(
            img, 
            text, 
            (50, self.target_h // 2 + 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (0, 165, 255), 
            2, 
            cv2.LINE_AA
        )
        self._cached_placeholder_text = text
        self._cached_placeholder_img = img
        return img

    def update_rtsp_url(self, new_url):
        """Memperbarui URL RTSP kamera secara dinamis (misal jika IP berubah oleh router DHCP)"""
        with self.lock:
            self.rtsp_url = new_url
            self.status = "Menghubungkan IP Baru..."
            self.failed_connects = 0

    def stop(self):
        self.running = False


class FFmpegStreamPusher:
    """
    Mengambil composite grid dari memory dan melakukan push stream ke YouTube / Private RTMP
    atau menyimpan rekaman mandiri ke Local HDD / NAS dengan thread mandiri (Zero-Lag).
    """
    def __init__(
        self, 
        rtmp_url="rtmp://a.rtmp.youtube.com/live2", 
        stream_key="", 
        fps=25, 
        bitrate="1200k", 
        encoder="h264_qsv", 
        resolution="1280x720", 
        preset="veryfast", 
        external_driver=True,
        mode="youtube",
        custom_rtmp_url="",
        local_output_dir="recordings",
        segment_seconds=900,
        retention_days=14
    ):
        self.mode = mode or "youtube"
        self.rtmp_url = rtmp_url or "rtmp://a.rtmp.youtube.com/live2"
        self.stream_key = stream_key or ""
        self.custom_rtmp_url = custom_rtmp_url or ""
        self.local_output_dir = local_output_dir or "recordings"
        self.segment_seconds = segment_seconds or 900
        self.retention_days = retention_days or 14
        self.fps = fps
        self.bitrate = bitrate
        self.encoder = encoder
        self.resolution = resolution
        self.preset = preset
        self.process = None
        self.running = False
        self.is_paused = False
        self.latest_frame = None
        self.lock = threading.Lock()
        self.feed_thread = None
        self.log_file = None
        self.external_driver = external_driver
        self._cleaner_thread = None

    def pause(self):
        """Menjeda streaming ke YouTube/Server dengan menampilkan layar standby"""
        with self.lock:
            self.is_paused = True

    def resume(self):
        """Melanjutkan pengiriman streaming kamera ke YouTube/Server"""
        with self.lock:
            self.is_paused = False

    def _generate_pause_frame(self):
        try:
            w, h = map(int, self.resolution.split("x"))
        except Exception:
            w, h = 1280, 720
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (18, 18, 24)
        cv2.rectangle(frame, (10, 10), (w - 10, h - 10), (45, 45, 60), 2)
        cv2.line(frame, (30, 60), (w - 30, 60), (0, 140, 255), 2)
        cv2.line(frame, (30, h - 60), (w - 30, h - 60), (0, 140, 255), 2)
        now_str = time.strftime('%H:%M:%S WIB')
        cv2.putText(frame, "||", (w // 2 - 15, h // 2 - 35), cv2.FONT_HERSHEY_DUPLEX, 2.0, (0, 165, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, "STREAMING SEDANG DIJEDA", (w // 2 - 210, h // 2 + 15), cv2.FONT_HERSHEY_DUPLEX, 0.95, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Waktu Jeda: {now_str} | Monitoring Kamera Lokal Tetap Berjalan", (w // 2 - 270, h // 2 + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (160, 165, 180), 1, cv2.LINE_AA)
        return frame

    def _generate_standby_frame(self):
        try:
            w, h = map(int, self.resolution.split("x"))
        except Exception:
            w, h = 1280, 720
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (20, 22, 28)
        cv2.rectangle(frame, (10, 10), (w - 10, h - 10), (45, 45, 60), 2)
        cv2.putText(frame, "POSRONDA HUB - MONITORING 24 JAM", (w // 2 - 230, h // 2 - 15), cv2.FONT_HERSHEY_DUPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Menghubungkan Feed Kamera...", (w // 2 - 150, h // 2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 1, cv2.LINE_AA)
        return frame

    def update_frame(self, frame_bgr):
        with self.lock:
            self.latest_frame = frame_bgr

    def push_frame(self, frame_bgr):
        """Menulis frame langsung ke stdin FFmpeg (Single-Timer Zero Jitter Push)"""
        if not self.running or not self.process:
            return False

        if self.process.poll() is not None:
            self.running = False
            return False

        self.external_driver = True
        out_frame = None
        with self.lock:
            self.latest_frame = frame_bgr
            if self.is_paused:
                out_frame = self._generate_pause_frame()
            elif frame_bgr is not None:
                out_frame = frame_bgr
            elif self.latest_frame is not None:
                out_frame = self.latest_frame
            else:
                out_frame = self._generate_standby_frame()

        if out_frame is not None:
            try:
                self.process.stdin.write(memoryview(out_frame))
                return True
            except (BrokenPipeError, OSError):
                self.running = False
                return False
        return False

    def _build_cmd(self, enc, pre, ffmpeg_bin, target, max_rate, buf_size):
        """Menyusun argumen FFmpeg yang 100% valid untuk YouTube, Private RTMP, maupun Local Recording"""
        cmd = [
            ffmpeg_bin,
            "-y",
            "-fflags", "+nobuffer+genpts",
            "-flags", "+low_delay",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", self.resolution,
            "-pix_fmt", "bgr24",
            "-r", str(self.fps),
            "-i", "-", # Input 0: Video dari Python
            "-f", "lavfi",
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", # Input 1: Audio dummy
            "-c:v", enc,
        ]

        if enc == "h264_qsv":
            qsv_preset = "veryfast"
            if pre in ["faster", "fast", "medium", "slow", "slower", "veryslow"]:
                qsv_preset = pre
            cmd.extend(["-preset", qsv_preset])
            cmd.extend(["-pix_fmt", "nv12"])
        else: # libx264
            x264_preset = pre if pre in ["ultrafast", "superfast", "veryfast"] else "ultrafast"
            cmd.extend(["-preset", x264_preset])
            cmd.extend(["-tune", "zerolatency"])
            cmd.extend(["-threads", "2"])
            cmd.extend(["-pix_fmt", "yuv420p"])

        if self.mode == "local_recording":
            base_dir = _get_base_dir()
            rec_dir = os.path.join(base_dir, self.local_output_dir) if not os.path.isabs(self.local_output_dir) else self.local_output_dir
            os.makedirs(rec_dir, exist_ok=True)
            file_pattern = os.path.join(rec_dir, "PosRonda_%Y-%m-%d_%H-%M-%S.mp4")
            cmd.extend([
                "-b:v", self.bitrate,
                "-maxrate", max_rate,
                "-bufsize", buf_size,
                "-g", str(self.fps * 2),
                "-c:a", "aac",
                "-b:a", "64k",
                "-f", "segment",
                "-segment_time", str(self.segment_seconds),
                "-segment_format", "mp4",
                "-reset_timestamps", "1",
                "-strftime", "1",
                file_pattern
            ])
        else:
            cmd.extend([
                "-b:v", self.bitrate,
                "-maxrate", max_rate,
                "-bufsize", buf_size,
                "-g", str(self.fps * 2),
                "-c:a", "aac",
                "-b:a", "64k",
                "-f", "flv",
                "-flvflags", "no_duration_filesize",
                target
            ])
        return cmd

    def start(self):
        base_dir = _get_base_dir()

        if self.mode == "local_recording":
            target = os.path.join(base_dir, self.local_output_dir) if not os.path.isabs(self.local_output_dir) else self.local_output_dir
            os.makedirs(target, exist_ok=True)
        elif self.mode == "private_rtmp":
            if self.custom_rtmp_url:
                target = self.custom_rtmp_url.strip()
                if self.stream_key and not target.endswith(self.stream_key):
                    target = f"{target.rstrip('/')}/{self.stream_key}"
            else:
                target = f"{self.rtmp_url.rstrip('/')}/{self.stream_key}"
        else: # "youtube"
            target = f"{self.rtmp_url.rstrip('/')}/{self.stream_key}"

        # Prioritas pemilihan binary FFmpeg:
        # 0. Internal bundle jika dibundle PyInstaller (sys._MEIPASS)
        # 1. Folder lokal PosRonda (ffmpeg.exe atau ffmpeg/bin/ffmpeg.exe)
        # 2. System PATH di komputer / laptop user (shutil.which)
        # 3. Default fallback "ffmpeg"
        ffmpeg_bin = None
        if hasattr(sys, "_MEIPASS"):
            meipass_ff = os.path.join(sys._MEIPASS, "ffmpeg.exe")
            if os.path.exists(meipass_ff):
                ffmpeg_bin = meipass_ff

        if not ffmpeg_bin:
            local_candidates = [
                os.path.join(base_dir, "ffmpeg.exe"),
                os.path.join(base_dir, "ffmpeg", "bin", "ffmpeg.exe"),
                os.path.join(base_dir, "bin", "ffmpeg.exe"),
            ]
            for cand in local_candidates:
                if os.path.exists(cand):
                    ffmpeg_bin = cand
                    break

        if not ffmpeg_bin:
            ffmpeg_bin = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe") or "ffmpeg"

        log_file_path = os.path.join(base_dir, "ffmpeg_log.txt")

        try:
            numeric_br = int(self.bitrate.replace("k", ""))
        except Exception:
            numeric_br = 1800
        max_rate = f"{numeric_br + 300}k"
        buf_size = f"{(numeric_br + 300) * 2}k"

        attempts = [
            ("h264_qsv", "veryfast"),
            ("libx264", "ultrafast")
        ]
        if self.encoder and self.encoder not in ["h264_qsv", "libx264"]:
            attempts.insert(0, (self.encoder, self.preset))

        self.running = False
        for enc, pre in attempts:
            cmd = self._build_cmd(enc, pre, ffmpeg_bin, target, max_rate, buf_size)
            try:
                if self.log_file and not self.log_file.closed:
                    try:
                        self.log_file.close()
                    except Exception:
                        pass
                self.log_file = open(log_file_path, "w", encoding="utf-8")

                print(f"[FFmpeg] Memulai engine [{self.mode}] dengan encoder: {enc} ({pre})...")
                self.process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stderr=self.log_file,
                    stdout=subprocess.DEVNULL,
                    bufsize=0
                )
                self.running = True

                if not getattr(self, "external_driver", True):
                    self.feed_thread = threading.Thread(target=self._feed_loop, daemon=True)
                    self.feed_thread.start()

                time.sleep(1.0)
                poll = self.process.poll()
                if poll is None:
                    self.encoder = enc
                    self.preset = pre
                    print(f"[FFmpeg] ✔ Encoder {enc} AKTIF & stabil mengalir ({self.mode}) @ {self.fps} FPS")

                    if self.mode == "local_recording":
                        def _cleaner_loop():
                            while self.running:
                                clean_old_recordings(target, self.retention_days)
                                for _ in range(1800):
                                    if not self.running:
                                        break
                                    time.sleep(1)
                        self._cleaner_thread = threading.Thread(target=_cleaner_loop, daemon=True)
                        self._cleaner_thread.start()

                    return True
                else:
                    print(f"[FFmpeg WARNING] Encoder {enc} berhenti (Exit Code: {poll}). Mencoba opsi cadangan...")
                    self.running = False
                    if self.feed_thread and self.feed_thread.is_alive():
                        self.feed_thread.join(timeout=0.5)
                    try:
                        if self.process.stdin:
                            self.process.stdin.close()
                    except Exception:
                        pass
                    try:
                        self.process.terminate()
                    except Exception:
                        pass
                    self.process = None
            except Exception as e:
                print(f"[FFmpeg] Gagal meluncurkan {enc}: {e}")
                self.running = False

        print("[FFmpeg FATAL] Semua encoder gagal dijalankan! Periksa ffmpeg_log.txt.")
        return False

    def _feed_loop(self):
        if getattr(self, "external_driver", False):
            return

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.winmm.timeBeginPeriod(1)
            except Exception:
                pass

        interval = 1.0 / self.fps
        next_time = time.perf_counter() + interval

        while self.running and self.process and self.process.poll() is None:
            if getattr(self, "external_driver", False):
                break

            frame = None
            with self.lock:
                if self.is_paused:
                    frame = self._generate_pause_frame()
                elif self.latest_frame is not None:
                    frame = self.latest_frame
                else:
                    frame = self._generate_standby_frame()

            if frame is not None:
                try:
                    self.process.stdin.write(frame.tobytes())
                    self.process.stdin.flush()
                except (BrokenPipeError, OSError):
                    break

            now = time.perf_counter()
            sleep_duration = next_time - now
            if sleep_duration > 0:
                time.sleep(sleep_duration)

            next_time += interval
            if next_time < time.perf_counter():
                next_time = time.perf_counter() + interval

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.winmm.timeEndPeriod(1)
            except Exception:
                pass

    def write_frame(self, frame_bgr):
        self.update_frame(frame_bgr)
        return True

    def stop(self):
        self.running = False
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                pass
            self.process = None
        if self.log_file and not self.log_file.closed:
            try:
                self.log_file.close()
            except Exception:
                pass
            self.log_file = None


class GridCompositor(threading.Thread):
    """
    Mesin Penggabung Grid Mandiri & Berkecepatan Tinggi (Dedicated Compositor Engine)
    - Mendukung Patrol / Tour Mode: Otomatis memutar halaman kamera (4, 8, 12, 16 kamera).
    - Mendukung Grid 2x2 (4 kamera) dan Grid 3x3 (9 kamera).
    - Memisahkan seluruh beban komposit, scaling, dan konversi warna dari thread Tkinter.
    - Double Buffering GUI 100% bebas tearing.
    """
    def __init__(self, cameras, pusher=None, fps=25, resolution="1280x720", patrol_cfg=None):
        super().__init__(daemon=True)
        self.cams = cameras
        self.pusher = pusher
        self.fps = fps
        self.resolution = resolution
        self.patrol_cfg = patrol_cfg or {}
        self.running = True
        self.lock = threading.Lock()

        self.patrol_enabled = self.patrol_cfg.get("enabled", False)
        self.patrol_interval = max(5, self.patrol_cfg.get("interval_seconds", 15))
        self.layout = self.patrol_cfg.get("layout", "2x2")
        self.current_page = 0
        self.last_page_time = time.time()

        self._calc_dims()

        if self.pusher:
            self.pusher.external_driver = True

    def _calc_dims(self):
        try:
            self.gw, self.gh = map(int, self.resolution.split("x"))
        except Exception:
            self.gw, self.gh = 1280, 720

        if self.layout == "3x3":
            self.cams_per_page = 9
            self.tile_w = self.gw // 3
            self.tile_h = self.gh // 3
        else:
            self.cams_per_page = 4
            self.tile_w = self.gw // 2
            self.tile_h = self.gh // 2

        self.total_pages = max(1, (len(self.cams) + self.cams_per_page - 1) // self.cams_per_page) if self.cams else 1
        if self.current_page >= self.total_pages:
            self.current_page = 0

        self.grid_bgr = np.zeros((self.gh, self.gw, 3), dtype=np.uint8)
        self.gui_front_buffer = np.zeros((self.gh, self.gw, 3), dtype=np.uint8)
        self.gui_back_buffer = np.zeros((self.gh, self.gw, 3), dtype=np.uint8)
        self.has_new_gui_frame = False

    def update_settings(self, cameras=None, pusher=None, fps=None, resolution=None, patrol_cfg=None):
        with self.lock:
            if cameras is not None:
                self.cams = cameras
            if pusher is not None:
                self.pusher = pusher
                self.pusher.external_driver = True
            if fps is not None:
                self.fps = fps
            if patrol_cfg is not None:
                self.patrol_cfg = patrol_cfg
                self.patrol_enabled = patrol_cfg.get("enabled", self.patrol_enabled)
                self.patrol_interval = max(5, patrol_cfg.get("interval_seconds", self.patrol_interval))
                self.layout = patrol_cfg.get("layout", self.layout)
            if resolution is not None:
                self.resolution = resolution
            self._calc_dims()

    def next_page(self):
        with self.lock:
            if self.total_pages > 1:
                self.current_page = (self.current_page + 1) % self.total_pages
                self.last_page_time = time.time()
                return self.current_page, self.total_pages
            return 0, 1

    def prev_page(self):
        with self.lock:
            if self.total_pages > 1:
                self.current_page = (self.current_page - 1 + self.total_pages) % self.total_pages
                self.last_page_time = time.time()
                return self.current_page, self.total_pages
            return 0, 1

    def set_page(self, page_idx):
        with self.lock:
            if 0 <= page_idx < self.total_pages:
                self.current_page = page_idx
                self.last_page_time = time.time()
                return self.current_page, self.total_pages
            return self.current_page, self.total_pages

    def get_page_info(self):
        with self.lock:
            return self.current_page, self.total_pages, self.patrol_enabled

    def get_latest_gui_frame(self):
        with self.lock:
            if not self.has_new_gui_frame:
                return None
            self.has_new_gui_frame = False
            return self.gui_front_buffer

    def run(self):
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.winmm.timeBeginPeriod(1)
            except Exception:
                pass

        target_fps = self.fps
        interval = 1.0 / max(target_fps, 5)
        next_tick = time.perf_counter() + interval

        while self.running:
            with self.lock:
                target_fps = self.fps
                gw, gh = self.gw, self.gh
                tile_w, tile_h = self.tile_w, self.tile_h
                current_pusher = self.pusher
                total_pages = self.total_pages
                patrol_enabled = self.patrol_enabled
                patrol_interval = self.patrol_interval
                cams_per_page = self.cams_per_page
                layout = self.layout

                now_time = time.time()
                if patrol_enabled and total_pages > 1:
                    if now_time - self.last_page_time >= patrol_interval:
                        self.current_page = (self.current_page + 1) % total_pages
                        self.last_page_time = now_time

                current_page = self.current_page
                start_idx = current_page * cams_per_page
                page_cams = self.cams[start_idx : start_idx + cams_per_page]

            interval = 1.0 / max(target_fps, 5)

            # 1. Salin tile kamera ke slice composite_grid
            try:
                if layout == "3x3":
                    for idx, cam in enumerate(page_cams):
                        r = idx // 3
                        c = idx % 3
                        y1 = r * tile_h
                        y2 = (r + 1) * tile_h if r < 2 else gh
                        x1 = c * tile_w
                        x2 = (c + 1) * tile_w if c < 2 else gw
                        cam.get_frame_direct(self.grid_bgr[y1:y2, x1:x2])
                else:
                    if len(page_cams) > 0:
                        page_cams[0].get_frame_direct(self.grid_bgr[0:tile_h, 0:tile_w])
                    if len(page_cams) > 1:
                        page_cams[1].get_frame_direct(self.grid_bgr[0:tile_h, tile_w:gw])
                    if len(page_cams) > 2:
                        page_cams[2].get_frame_direct(self.grid_bgr[tile_h:gh, 0:tile_w])
                    if len(page_cams) > 3:
                        page_cams[3].get_frame_direct(self.grid_bgr[tile_h:gh, tile_w:gw])

                if total_pages > 1:
                    draw_patrol_badge(
                        self.grid_bgr, 
                        f"PATROL {current_page + 1}/{total_pages} [CAM {start_idx + 1:02d}-{min(start_idx + cams_per_page, len(self.cams)):02d}]"
                    )
            except Exception:
                pass

            # 2. Kirim ke Pusher
            if current_pusher and current_pusher.running:
                current_pusher.push_frame(self.grid_bgr)

            # 3. Double buffer untuk Tkinter RGB
            try:
                cv2.cvtColor(self.grid_bgr, cv2.COLOR_BGR2RGB, dst=self.gui_back_buffer)
                with self.lock:
                    self.gui_front_buffer, self.gui_back_buffer = self.gui_back_buffer, self.gui_front_buffer
                    self.has_new_gui_frame = True
            except Exception:
                pass

            now = time.perf_counter()
            sleep_time = next_tick - now
            if sleep_time > 0:
                time.sleep(sleep_time)

            next_tick += interval
            if next_tick < time.perf_counter():
                next_tick = time.perf_counter() + interval

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.winmm.timeEndPeriod(1)
            except Exception:
                pass

    def stop(self):
        self.running = False

