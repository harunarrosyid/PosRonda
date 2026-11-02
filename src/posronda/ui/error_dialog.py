"""
PosRonda Error & Diagnostic Dialog with Clipboard Copy
Menampilkan pesan error terstruktur dengan tombol 'Salin Log Error' untuk memudahkan pelaporan bug.
"""

import tkinter as tk
from tkinter import ttk
import webbrowser

class ErrorDialog(tk.Toplevel):
    def __init__(self, parent, title, message, error_details=None, action_url=None, action_url_label=None):
        super().__init__(parent)
        self.title(title or "Peringatan / Error - PosRonda")
        self.configure(bg="#0b0f19")
        self.transient(parent)
        self.grab_set()

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(680, sw - 40)
        h = min(480, sh - 100)
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(500, 340)

        self.full_log_text = error_details or message
        self.action_url = action_url
        self.action_url_label = action_url_label

        self._build_ui(title, message, error_details)

    def _build_ui(self, title, message, error_details):
        # 1. Header Card
        f_header = tk.Frame(self, bg="#1e1b4b", padx=16, pady=10)
        f_header.pack(fill="x")

        lbl_icon = tk.Label(f_header, text="[ERROR]", bg="#1e1b4b", fg="#f87171", font=("Segoe UI", 10, "bold"))
        lbl_icon.pack(side="left", padx=(0, 10))

        f_htext = tk.Frame(f_header, bg="#1e1b4b")
        f_htext.pack(side="left", fill="x", expand=True)

        tk.Label(
            f_htext,
            text=title or "Terjadi Kesalahan",
            bg="#1e1b4b",
            fg="#fca5a5",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            f_htext,
            text="Gunakan tombol 'Salin Log Error' di bawah untuk menyalin seluruh detail laporan.",
            bg="#1e1b4b",
            fg="#94a3b8",
            font=("Segoe UI", 8)
        ).pack(anchor="w")

        # 2. Body Area
        f_body = tk.Frame(self, bg="#0b0f19", padx=14, pady=10)
        f_body.pack(fill="both", expand=True)

        # Summary box
        f_msg = tk.Frame(f_body, bg="#1e293b", padx=12, pady=10, highlightthickness=1, highlightbackground="#334155")
        f_msg.pack(fill="x", pady=(0, 10))

        lbl_msg = tk.Label(
            f_msg,
            text=message,
            bg="#1e293b",
            fg="#f8fafc",
            font=("Segoe UI", 9),
            justify="left",
            wraplength=w - 70 if 'w' in locals() else 580
        )
        lbl_msg.pack(anchor="w")

        # Detail Log Header & Textbox
        tk.Label(
            f_body,
            text="Detail Teknis / Log Error Lengkap:",
            bg="#0b0f19",
            fg="#94a3b8",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(0, 4))

        f_txt = tk.Frame(f_body, bg="#020617")
        f_txt.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(f_txt, orient="vertical")
        self.txt_log = tk.Text(
            f_txt,
            bg="#020617",
            fg="#f1f5f9",
            insertbackground="#ffffff",
            font=("Consolas", 8),
            wrap="word",
            padx=8,
            pady=8,
            yscrollcommand=scrollbar.set,
            relief="flat",
            highlightthickness=1,
            highlightbackground="#334155"
        )
        scrollbar.config(command=self.txt_log.yview)

        self.txt_log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        display_text = error_details if error_details else message
        self.txt_log.insert("1.0", display_text)
        self.txt_log.config(state="disabled")

        # 3. Bottom Bar Buttons
        f_bottom = tk.Frame(self, bg="#0f172a", padx=14, pady=10, highlightthickness=1, highlightbackground="#1e293b")
        f_bottom.pack(side="bottom", fill="x")

        self.btn_copy = tk.Button(
            f_bottom,
            text="Salin Log Error",
            bg="#3b82f6",
            fg="#ffffff",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.copy_to_clipboard
        )
        self.btn_copy.pack(side="left", padx=(0, 8))

        if self.action_url:
            btn_url = tk.Button(
                f_bottom,
                text=self.action_url_label or "Buka Tautan Bantuan",
                bg="#0284c7",
                fg="#ffffff",
                activebackground="#0369a1",
                activeforeground="#ffffff",
                relief="flat",
                font=("Segoe UI", 9),
                padx=10,
                pady=4,
                cursor="hand2",
                command=lambda: webbrowser.open_new(self.action_url)
            )
            btn_url.pack(side="left", padx=(0, 8))

        btn_close = tk.Button(
            f_bottom,
            text="Tutup",
            bg="#334155",
            fg="#cbd5e1",
            activebackground="#475569",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9),
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.destroy
        )
        btn_close.pack(side="right")

    def copy_to_clipboard(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.full_log_text)
            self.update_idletasks()
            self.btn_copy.config(
                text="Log Berhasil Disalin!",
                bg="#16a34a",
                activebackground="#15803d"
            )
            self.after(2500, lambda: self.btn_copy.config(
                text="Salin Log Error",
                bg="#3b82f6",
                activebackground="#2563eb"
            ))
        except Exception:
            pass

def show_error_dialog(parent, title, message, error_details=None, action_url=None, action_url_label=None):
    """Fungsi pembantu sekali panggil untuk menampilkan Error Dialog dengan fitur copy log"""
    return ErrorDialog(parent, title, message, error_details, action_url, action_url_label)
