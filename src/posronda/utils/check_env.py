"""
Pre-Flight Environment Checker for PosRonda v4.0
Mendeteksi apakah Python dan FFmpeg sudah terpasang dengan benar.
Jika belum, menyediakan link download langsung yang siap klik.
"""

import sys
import os
import shutil
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

REQUIRED_PYTHON_MAJOR = 3
REQUIRED_PYTHON_MINOR = 10

PYTHON_DOWNLOAD_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
PYTHON_DOWNLOAD_NAME = "Python 3.11.9 (64-bit Windows Installer)"

FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
FFMPEG_DOWNLOAD_NAME = "FFmpeg Release Essentials (Windows 64-bit with Intel QuickSync)"

def check_python_version():
    major = sys.version_info.major
    minor = sys.version_info.minor
    if major == REQUIRED_PYTHON_MAJOR and minor >= REQUIRED_PYTHON_MINOR:
        return True, f"Python {major}.{minor}.{sys.version_info.micro} (Didukung)"
    return False, f"Python {major}.{minor}.{sys.version_info.micro} (Disarankan minimal 3.10)"

def check_ffmpeg():
    # 1. Cek di PATH sistem
    if shutil.which("ffmpeg") or shutil.which("ffmpeg.exe"):
        return True, "FFmpeg terdeteksi di System PATH"
    
    # 2. Cek di folder lokal aplikasi
    this_dir = os.path.dirname(os.path.abspath(__file__))
    root_candidate = os.path.abspath(os.path.join(this_dir, "..", "..", ".."))
    local_paths = [
        os.path.join(os.getcwd(), "ffmpeg.exe"),
        os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(root_candidate, "ffmpeg.exe"),
        os.path.join(root_candidate, "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe"),
        os.path.join(this_dir, "ffmpeg.exe"),
    ]
    for p in local_paths:
        if os.path.exists(p):
            return True, f"FFmpeg ditemukan di folder lokal: {p}"
            
    return False, "FFmpeg TIDAK ditemukan di komputer"

def open_url(url):
    webbrowser.open_new(url)

def show_env_gui(py_ok, py_msg, ffmpeg_ok, ffmpeg_msg):
    root = tk.Tk()
    root.title("Pemeriksa Sistem - PosRonda v4.0")
    root.geometry("620x460")
    root.resizable(False, False)
    root.configure(bg="#0b0f19")

    style = ttk.Style()
    style.theme_use("clam")

    title_lbl = tk.Label(
        root, 
        text="🛡️ Pemeriksaan Sistem PosRonda Hub", 
        font=("Segoe UI", 16, "bold"), 
        bg="#0b0f19", 
        fg="#818cf8"
    )
    title_lbl.pack(pady=15)

    frame = tk.Frame(root, bg="#2b2d42", padx=20, pady=15, bd=1, relief="ridge")
    frame.pack(fill="both", expand=True, padx=25, pady=10)

    # Status Python
    py_color = "#4ade80" if py_ok else "#f87171"
    py_icon = "✔" if py_ok else "✖"
    lbl_py = tk.Label(frame, text=f"{py_icon} Status Python:", font=("Segoe UI", 11, "bold"), bg="#2b2d42", fg="#ffffff")
    lbl_py.grid(row=0, column=0, sticky="w", pady=5)
    lbl_py_val = tk.Label(frame, text=py_msg, font=("Segoe UI", 10), bg="#2b2d42", fg=py_color)
    lbl_py_val.grid(row=0, column=1, sticky="w", padx=10, pady=5)

    if not py_ok:
        btn_py = tk.Button(
            frame, 
            text=f"⬇ Download {PYTHON_DOWNLOAD_NAME}", 
            bg="#3b82f6", 
            fg="white", 
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=8, pady=4,
            command=lambda: open_url(PYTHON_DOWNLOAD_URL)
        )
        btn_py.grid(row=1, column=1, sticky="w", padx=10, pady=5)

    # Status FFmpeg
    ff_color = "#4ade80" if ffmpeg_ok else "#f87171"
    ff_icon = "✔" if ffmpeg_ok else "✖"
    lbl_ff = tk.Label(frame, text=f"{ff_icon} Status FFmpeg:", font=("Segoe UI", 11, "bold"), bg="#2b2d42", fg="#ffffff")
    lbl_ff.grid(row=2, column=0, sticky="w", pady=(15, 5))
    lbl_ff_val = tk.Label(frame, text=ffmpeg_msg, font=("Segoe UI", 10), bg="#2b2d42", fg=ff_color)
    lbl_ff_val.grid(row=2, column=1, sticky="w", padx=10, pady=(15, 5))

    if not ffmpeg_ok:
        desc_ff = tk.Label(
            frame, 
            text="FFmpeg diperlukan untuk menangkap RTSP & push stream ke YouTube via Intel QuickSync.\nCukup unduh zip di bawah, ekstrak, lalu taruh 'ffmpeg.exe' di folder aplikasi ini.",
            font=("Segoe UI", 8), 
            bg="#2b2d42", 
            fg="#94a3b8",
            justify="left"
        )
        desc_ff.grid(row=3, column=1, sticky="w", padx=10, pady=3)

        btn_ff = tk.Button(
            frame, 
            text=f"⬇ Download {FFMPEG_DOWNLOAD_NAME}", 
            bg="#f59e0b", 
            fg="black", 
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=8, pady=4,
            command=lambda: open_url(FFMPEG_DOWNLOAD_URL)
        )
        btn_ff.grid(row=4, column=1, sticky="w", padx=10, pady=5)

    # Panduan singkat
    footer_text = (
        "Tips: Saat menginstall Python, pastikan mencentang [X] 'Add python.exe to PATH'\n"
        "Setelah mengunduh FFmpeg, taruh file 'ffmpeg.exe' di satu folder dengan aplikasi ini."
    )
    lbl_footer = tk.Label(root, text=footer_text, font=("Segoe UI", 8), bg="#1e1e24", fg="#94a3b8")
    lbl_footer.pack(pady=10)

    btn_action = tk.Button(
        root, 
        text="Tutup & Mulai Aplikasi" if (py_ok and ffmpeg_ok) else "Tutup", 
        bg="#22c55e" if (py_ok and ffmpeg_ok) else "#64748b",
        fg="white", 
        font=("Segoe UI", 10, "bold"),
        padx=15, pady=6,
        relief="flat",
        command=root.destroy
    )
    btn_action.pack(pady=10)

    root.mainloop()

def run_check(show_gui_if_missing=True):
    py_ok, py_msg = check_python_version()
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg()

    if not py_ok or not ffmpeg_ok:
        if show_gui_if_missing:
            show_env_gui(py_ok, py_msg, ffmpeg_ok, ffmpeg_msg)
        return False
    return True

if __name__ == "__main__":
    is_ready = run_check(show_gui_if_missing=True)
    if is_ready:
        print("✔ Sistem siap! Python dan FFmpeg terdeteksi.")
        sys.exit(0)
    else:
        print("✖ Komponen belum lengkap. Silakan unduh melalui jendela dialog.")
        sys.exit(1)
