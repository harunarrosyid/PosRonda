"""
PosRonda Internationalization (i18n) Engine
Dukungan Dwibahasa (Bahasa Indonesia & English) untuk PosRonda Hub.
"""

_CURRENT_LANG = "id"

TRANSLATIONS = {
    "id": {
        "app_tagline": "Pusat Pemantau CCTV Multi-Kamera & Mesin Live Streaming Otomatis",
        "mode_studio": "Mode Studio (F9)",
        "mode_eco": "Mode Hemat (F9)",
        "eco_active_hint": "Mode Hemat Aktif (GUI 1 FPS) • Output Streamer Tetap Berjalan Penuh",
        "studio_active_hint": "Mode Studio Aktif (Tampilan Layar Monitor Framerate Penuh)",
        "status_monitoring": "MONITORING",
        "status_live": "SIARAN LANGSUNG (LIVE)",
        "status_paused": "JEDA",
        "status_standby": "STANDBY",
        "btn_settings": "Pengaturan (F2)",
        "btn_about": "Info",
        "btn_refresh_all": "Refresh Kamera",
        "btn_save": "Simpan & Terapkan Pengaturan",
        "btn_cancel": "Batal",
        "btn_backup": "Backup Pengaturan",
        "btn_import": "Impor Pengaturan",
        "tab_cams": "Kamera & Patrol",
        "tab_server": "Server & Tujuan Siaran",
        "tab_perf": "Kinerja Hardware",
        "tab_license": "Sistem & Lisensi",
        "tab_general": "Umum & Bahasa",
        "lang_selector": "Pilihan Bahasa Antarmuka (Language):",
        "yt_playlist": "Playlist Arsip YouTube:",
        "btn_load_playlists": "Muat Playlist",
        "btn_create_playlist": "Buat Playlist Baru",
        "yt_api_test": "Tes YouTube API",
        "yt_close_zombie": "Tutup Siaran Zombie",
        "yt_del_upcoming": "Hapus Upcoming Menumpuk",
        "lbl_no_playlist": "(Tanpa Playlist / Jangan Arsipkan)",
        "lbl_manual_playlist": "(Ketik ID Manual...)",
        "playlist_created_success": "Playlist baru berhasil dibuat dan dipilih!",
    },
    "en": {
        "app_tagline": "Autonomous Multi-Camera CCTV Surveillance Hub & Live Streaming Engine",
        "mode_studio": "Studio Mode (F9)",
        "mode_eco": "Eco Mode (F9)",
        "eco_active_hint": "Eco Mode Active (1 FPS GUI) • Output Streamer Running Full Framerate",
        "studio_active_hint": "Studio Mode Active (Full Framerate Visual Inspection)",
        "status_monitoring": "MONITORING",
        "status_live": "LIVE STREAMING",
        "status_paused": "PAUSED",
        "status_standby": "STANDBY",
        "btn_settings": "Settings (F2)",
        "btn_about": "About",
        "btn_refresh_all": "Refresh Feeds",
        "btn_save": "Save & Apply Settings",
        "btn_cancel": "Cancel",
        "btn_backup": "Export Settings",
        "btn_import": "Import Settings",
        "tab_cams": "Cameras & Layout",
        "tab_server": "Server & Destination",
        "tab_perf": "Performance & Hardware",
        "tab_license": "System & License",
        "tab_general": "General & Language",
        "lang_selector": "User Interface Language:",
        "yt_playlist": "YouTube Archive Playlist:",
        "btn_load_playlists": "Load Playlists",
        "btn_create_playlist": "Create New Playlist",
        "yt_api_test": "Test YouTube API",
        "yt_close_zombie": "Close Zombie Streams",
        "yt_del_upcoming": "Clear Upcoming Queue",
        "lbl_no_playlist": "(No Playlist / Do Not Archive)",
        "lbl_manual_playlist": "(Enter ID Manually...)",
        "playlist_created_success": "New playlist created and selected successfully!",
    }
}

def get_current_language():
    global _CURRENT_LANG
    return _CURRENT_LANG

def set_language(lang_code):
    global _CURRENT_LANG
    if lang_code in TRANSLATIONS:
        _CURRENT_LANG = lang_code
    else:
        _CURRENT_LANG = "id"

def t(key, default=None):
    """Mendapatkan teks terjemahan berdasarkan bahasa yang aktif saat ini"""
    lang = get_current_language()
    dict_lang = TRANSLATIONS.get(lang, TRANSLATIONS["id"])
    return dict_lang.get(key, default or key)
