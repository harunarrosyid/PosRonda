"""
Telegram Notification & Alert Module
Mengirimkan notifikasi instan berupa foto snapshot dan direct link ke menit video di YouTube.
"""

import time
import requests
import os

class TelegramNotifier:
    def __init__(self, config):
        self.cfg = config.get("telegram", {})
        self.enabled = self.cfg.get("enabled", False)
        self.bot_token = self.cfg.get("bot_token", "")
        self.chat_id = self.cfg.get("chat_id", "")
        self.last_alert_time = {} # Cooldown per kamera agar tidak spam

    def send_detection_alert(self, cam_name, image_path, broadcast_id, elapsed_seconds):
        """
        Mengirim foto dan link langsung ke detik kejadian di YouTube live.
        """
        if not self.enabled or not self.bot_token or not self.chat_id:
            return False

        now = time.time()
        # Cooldown 20 detik per kamera
        if cam_name in self.last_alert_time and (now - self.last_alert_time[cam_name]) < 20:
            return False

        self.last_alert_time[cam_name] = now

        # Hitung format jam:menit:detik
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Buat link YouTube dengan parameter offset detik
        youtube_link = f"https://youtu.be/{broadcast_id}?t={elapsed_seconds}s" if broadcast_id else "Siaran Langsung"

        caption = (
            f"🚨 <b>PERINGATAN DETEKSI CCTV</b>\n\n"
            f"📍 <b>Lokasi:</b> {cam_name}\n"
            f"⏱️ <b>Waktu Siaran:</b> Menit {time_str}\n"
            f"🔗 <b>Tonton Detik Ini:</b> <a href='{youtube_link}'>Klik untuk Putar di YouTube</a>\n"
        )

        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as photo:
                    data = {
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "HTML"
                    }
                    files = {"photo": photo}
                    resp = requests.post(url, data=data, files=files, timeout=10)
                    return resp.status_code == 200
            else:
                msg_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    "chat_id": self.chat_id,
                    "text": caption,
                    "parse_mode": "HTML"
                }
                resp = requests.post(msg_url, data=data, timeout=10)
                return resp.status_code == 200
        except Exception as e:
            print(f"Error mengirim Telegram: {e}")
            return False
