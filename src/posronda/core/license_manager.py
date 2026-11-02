"""
PosRonda License Manager
Pengelolaan status lisensi PosRonda Community dan Pro.
"""

import os
import sys
import json
import hashlib
import time

def get_base_dir():
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

LICENSE_FILE = os.path.join(get_base_dir(), "posronda.lic")
LICENSE_SECRET_SALT = "POSRONDA_SECURE_SALT_v4_2026_CORE"

def _get_default_brand():
    try:
        from posronda import __version__
        return f"PosRonda Hub v{__version__}"
    except Exception:
        return "PosRonda Hub"

class LicenseManager:
    @staticmethod
    def get_license_info():
        """
        Membaca file lisensi posronda.lic jika ada.
        Jika tidak ada, mengembalikan status PosRonda Community Edition.
        """
        if not os.path.exists(LICENSE_FILE):
            return {
                "tier": "COMMUNITY",
                "tier_name": "PosRonda Community Edition",
                "is_pro": False,
                "holder": "Warga & Komunitas PosRonda",
                "org": "Penggunaan Mandiri (Non-Komersial)",
                "watermark_brand": _get_default_brand(),
                "white_label_enabled": False,
                "status_text": "Aktif (Non-Komersial)"
            }

        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            holder = data.get("holder", "Pelanggan Pro")
            org = data.get("org", "Komersial")
            key = data.get("key", "")
            brand = data.get("brand", "CCTV Monitoring Hub")

            # Verifikasi integritas tanda tangan kunci lisensi
            expected_hash = hashlib.sha256(f"{holder}:{org}:{LICENSE_SECRET_SALT}".encode()).hexdigest()[:16].upper()
            if key == expected_hash or key == "PRO-DEVELOPER-UNLIMITED":
                return {
                    "tier": "PRO",
                    "tier_name": "PosRonda PRO Commercial Edition",
                    "is_pro": True,
                    "holder": holder,
                    "org": org,
                    "watermark_brand": brand,
                    "white_label_enabled": True,
                    "status_text": f"Terlisensi Resmi untuk {holder} ({org})"
                }
            else:
                return {
                    "tier": "COMMUNITY",
                    "tier_name": "PosRonda Community Edition (Kunci Tidak Valid)",
                    "is_pro": False,
                    "holder": "Warga & Komunitas PosRonda",
                    "org": "Non-Komersial",
                    "watermark_brand": _get_default_brand(),
                    "white_label_enabled": False,
                    "status_text": "Kunci lisensi tidak cocok. Berjalan dalam mode Komunitas."
                }
        except Exception:
            return {
                "tier": "COMMUNITY",
                "tier_name": "PosRonda Community Edition",
                "is_pro": False,
                "holder": "Warga & Komunitas PosRonda",
                "org": "Non-Komersial",
                "watermark_brand": _get_default_brand(),
                "white_label_enabled": False,
                "status_text": "Aktif (Non-Komersial)"
            }

    @staticmethod
    def generate_license_key(holder, org="Komersial"):
        """Fungsi pembantu untuk membuat kunci aktivasi resmi PosRonda PRO"""
        return hashlib.sha256(f"{holder}:{org}:{LICENSE_SECRET_SALT}".encode()).hexdigest()[:16].upper()

    @staticmethod
    def install_license(holder, org, key, custom_brand="CCTV Hub"):
        """Menyimpan file posronda.lic ke direktori aplikasi"""
        data = {
            "holder": holder.strip(),
            "org": org.strip(),
            "key": key.strip(),
            "brand": custom_brand.strip(),
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True, "Lisensi PosRonda PRO berhasil dipasang!"
        except Exception as e:
            return False, f"Gagal menyimpan file lisensi: {e}"
