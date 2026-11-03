"""
YouTube Data API v3 Automation Module
Mengatur siklus live stream 11 jam, binding stream key, dan otomatis menambahkan ke Playlist.
"""

import os
import json
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

class YouTubeManager:
    def __init__(self, config):
        self.cfg = config.get("youtube_api", {})
        try:
            from posronda.core import config_manager
        except ImportError:
            import config_manager
        base_dir = config_manager.get_base_dir()
        secret_name = self.cfg.get("client_secrets_file", "client_secrets.json")
        self.client_secrets_file = secret_name if os.path.isabs(secret_name) else os.path.join(base_dir, secret_name)
        token_name = self.cfg.get("token_file", "token.json")
        self.token_file = token_name if os.path.isabs(token_name) else os.path.join(base_dir, token_name)
        self.playlist_id = self.cfg.get("playlist_id", "")
        self.title_prefix = self.cfg.get("title_prefix", "CCTV Monitoring 24 Jam")
        self.privacy_status = self.cfg.get("privacy_status", "unlisted")
        self.latency_preference = self.cfg.get("latency_preference", "low")
        self.single_stream_mode = self.cfg.get("single_stream_mode", True)
        self.service = None

    def authenticate(self):
        """Autentikasi OAuth 2.0 (hanya perlu login browser sekali, token disimpan di token.json)"""
        creds = None
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                print(f"Token invalid, perlu login ulang: {e}")
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None

            if not creds:
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(
                        f"File '{self.client_secrets_file}' tidak ditemukan! "
                        "Silakan unduh dari Google Cloud Console dan letakkan di folder aplikasi."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        self.service = build("youtube", "v3", credentials=creds)
        return True

    def test_connection(self, playlist_id=None):
        """Memeriksa apakah token/kredensial valid, mengambil nama channel & status playlist."""
        if not self.service:
            self.authenticate()

        # 1. Cek info Channel YouTube milik akun ini
        ch_resp = self.service.channels().list(part="snippet", mine=True).execute()
        items = ch_resp.get("items", [])
        if not items:
            return False, "Kredensial valid, namun tidak ditemukan Channel YouTube aktif di akun ini.", None

        channel_name = items[0]["snippet"]["title"]
        msg = f"[OK] Berhasil terhubung ke Channel: '{channel_name}'"

        # 2. Cek Playlist jika diisi
        target_pl = playlist_id or self.playlist_id
        if target_pl:
            try:
                pl_resp = self.service.playlists().list(part="snippet", id=target_pl).execute()
                pl_items = pl_resp.get("items", [])
                if pl_items:
                    pl_title = pl_items[0]["snippet"]["title"]
                    msg += f"\n[OK] Playlist Valid: '{pl_title}' (ID: {target_pl})"
                else:
                    msg += f"\n[PERINGATAN] Playlist ID '{target_pl}' tidak ditemukan atau bersifat private."
            except Exception as e:
                msg += f"\n[PERINGATAN] Gagal memverifikasi Playlist: {e}"
        else:
            msg += "\n[INFO] Playlist ID kosong (Video tidak akan otomatis dimasukkan ke playlist)."

        # 3. Coba deteksi stream key yang sudah ada di channel ini & cek izin live streaming
        stream_key = None
        try:
            s_resp = self.service.liveStreams().list(part="cdn,snippet", mine=True, maxResults=5).execute()
            s_items = s_resp.get("items", [])
            if s_items:
                stream_key = s_items[0]["cdn"]["ingestionInfo"]["streamName"]
                masked_key = stream_key[:4] + "****" if len(stream_key) > 4 else "****"
                msg += f"\n[OK] Stream Key YouTube terdeteksi: {masked_key}"
            else:
                msg += "\n[INFO] Belum ada stream key aktif di YouTube Studio."
        except Exception as se:
            err_str = str(se)
            if "liveStreamingNotEnabled" in err_str or "The user is not enabled for live streaming" in err_str:
                msg += (
                    "\n\n[PERINGATAN PENTING] Fitur Live Streaming BELUM AKTIF pada Channel ini!"
                    "\n   Google melaporkan izin live streaming belum terbuka untuk akun ini."
                    "\n   Langkah Aktivasi:"
                    "\n   1. Buka https://studio.youtube.com"
                    "\n   2. Klik 'Create' (Buat) -> 'Go Live' (Mulai Siaran)"
                    "\n   3. Lakukan verifikasi nomor HP yang diminta YouTube"
                    "\n   4. Tunggu masa aktivasi hingga 24 jam dari pihak YouTube."
                )

        return True, msg, stream_key

    def list_channel_playlists(self):
        """
        Mengambil daftar seluruh playlist yang dimiliki oleh channel YouTube pengguna.
        Mengembalikan tuple: (success: bool, playlists: list, error_log: str/None)
        """
        if not self.service:
            self.authenticate()

        playlists = []
        try:
            next_page = None
            while True:
                req_args = {
                    "part": "id,snippet,status,contentDetails",
                    "mine": True,
                    "maxResults": 50
                }
                if next_page:
                    req_args["pageToken"] = next_page

                resp = self.service.playlists().list(**req_args).execute()
                for item in resp.get("items", []):
                    playlists.append({
                        "id": item["id"],
                        "title": item.get("snippet", {}).get("title", "Untitled Playlist"),
                        "description": item.get("snippet", {}).get("description", ""),
                        "privacy": item.get("status", {}).get("privacyStatus", "unlisted"),
                        "item_count": item.get("contentDetails", {}).get("itemCount", 0)
                    })
                next_page = resp.get("nextPageToken")
                if not next_page:
                    break

            return True, playlists, None
        except Exception as e:
            import traceback
            return False, [], traceback.format_exc()

    def create_playlist(self, title, description="", privacy_status="unlisted"):
        """
        Membuat playlist baru langsung di channel YouTube pengguna.
        privacy_status: 'unlisted' | 'public' | 'private'
        Mengembalikan tuple: (success: bool, created_playlist_dict: dict/None, error_log: str/None)
        """
        if not self.service:
            self.authenticate()

        try:
            body = {
                "snippet": {
                    "title": title.strip(),
                    "description": description.strip() or "Arsip Rekaman CCTV Otomatis - PosRonda Surveillance Hub"
                },
                "status": {
                    "privacyStatus": privacy_status.lower()
                }
            }
            resp = self.service.playlists().insert(
                part="snippet,status",
                body=body
            ).execute()

            new_pl = {
                "id": resp["id"],
                "title": resp.get("snippet", {}).get("title", title),
                "privacy": resp.get("status", {}).get("privacyStatus", privacy_status),
                "item_count": 0
            }
            return True, new_pl, None
        except Exception as e:
            import traceback
            return False, None, traceback.format_exc()

    def find_existing_upcoming_broadcast(self):
        """Mencari apakah sudah ada siaran 'upcoming' aktif milik CCTV Hub untuk digunakan kembali (Anti-Numpuk)"""
        if not self.service:
            self.authenticate()

        try:
            resp = self.service.liveBroadcasts().list(
                part="id,snippet,status,contentDetails",
                broadcastStatus="upcoming",
                maxResults=50
            ).execute()

            items = resp.get("items", [])
            if not items:
                return None

            # Filter yang awalan judulnya cocok dengan CCTV Hub kita
            matched = [i for i in items if self.title_prefix.lower() in i["snippet"].get("title", "").lower()]
            if not matched:
                matched = items

            # Urutkan dari yang terbaru
            matched.sort(
                key=lambda x: x.get("snippet", {}).get("scheduledStartTime") or x.get("snippet", {}).get("publishedAt", ""),
                reverse=True
            )

            # Cari siaran yang memiliki stream key valid
            valid_item = None
            stream_name = None
            ingestion_address = None

            for candidate in matched:
                b_id = candidate["id"]
                bs_id = candidate.get("contentDetails", {}).get("boundStreamId")
                if not bs_id:
                    continue
                try:
                    s_resp = self.service.liveStreams().list(part="cdn", id=bs_id).execute()
                    s_items = s_resp.get("items", [])
                    if s_items:
                        valid_item = candidate
                        stream_name = s_items[0]["cdn"]["ingestionInfo"]["streamName"]
                        ingestion_address = s_items[0]["cdn"]["ingestionInfo"]["ingestionAddress"]
                        break
                except Exception:
                    continue

            if not valid_item:
                return None

            broadcast_id = valid_item["id"]

            return {
                "broadcast_id": broadcast_id,
                "stream_id": bs_id,
                "stream_key": stream_name,
                "rtmp_url": ingestion_address,
                "watch_url": f"https://youtu.be/{broadcast_id}",
                "title": valid_item["snippet"]["title"]
            }
        except Exception as e:
            print(f"[YouTube API] Error cek broadcast existing: {e}")
            return None

    def cleanup_all_upcoming(self, only_cctv_prefix=False):
        """Menghapus seluruh siaran 'upcoming' yang menumpuk di channel YouTube (Pembersih Massal)"""
        if not self.service:
            self.authenticate()

        deleted_count = 0
        try:
            next_page_token = None
            while True:
                list_args = {
                    "part": "id,snippet,status",
                    "broadcastStatus": "upcoming",
                    "maxResults": 50
                }
                if next_page_token:
                    list_args["pageToken"] = next_page_token

                resp = self.service.liveBroadcasts().list(**list_args).execute()

                items = resp.get("items", [])
                if not items:
                    break

                for item in items:
                    b_id = item["id"]
                    title = item.get("snippet", {}).get("title", "")
                    # Filter jika hanya ingin menghapus siaran milik CCTV Hub
                    if only_cctv_prefix and self.title_prefix.lower() not in title.lower():
                        continue

                    try:
                        self.service.liveBroadcasts().delete(id=b_id).execute()
                        deleted_count += 1
                        print(f"[YouTube API] Terhapus siaran upcoming: {title} ({b_id})")
                    except Exception as e:
                        print(f"[YouTube API] Gagal hapus {b_id}: {e}, mencoba unbind dulu...")
                        try:
                            self.service.liveBroadcasts().bind(id=b_id, part="id,contentDetails").execute()
                            self.service.liveBroadcasts().delete(id=b_id).execute()
                            deleted_count += 1
                            print(f"[YouTube API] Terhapus setelah unbind: {title} ({b_id})")
                        except Exception as e2:
                            print(f"[YouTube API] Tetap gagal hapus {b_id}: {e2}")

                next_page_token = resp.get("nextPageToken")
                if not next_page_token:
                    break

            return True, f"Berhasil menghapus {deleted_count} siaran 'Upcoming' yang menumpuk di YouTube Studio!", None
        except Exception as e:
            err_str = str(e)
            if "liveStreamingNotEnabled" in err_str or "The user is not enabled for live streaming" in err_str:
                return False, (
                    "Fitur Live Streaming belum aktif pada Channel YouTube Anda di YouTube Studio (Error 403 liveStreamingNotEnabled).\n\n"
                    "Langkah aktivasi:\n"
                    "1. Buka https://studio.youtube.com\n"
                    "2. Klik 'Create' (Buat) -> 'Go Live' (Mulai Siaran Langsung)\n"
                    "3. Lakukan verifikasi nomor HP sesuai instruksi YouTube\n"
                    "4. Tunggu masa aktivasi hingga 24 jam sampai YouTube mengaktifkan fitur live streaming untuk channel Anda."
                ), err_str
            elif "quotaExceeded" in err_str or "quota" in err_str.lower():
                return False, (
                    "Batas kuota harian (10.000 unit) YouTube Data API telah habis untuk hari ini (Error 403 quotaExceeded).\n\n"
                    "Tips: Gunakan Stream Key manual dari YouTube Studio untuk siaran langsung bebas kuota 24 jam."
                ), err_str

            return False, f"Terjadi kesalahan saat membersihkan siaran upcoming:\n{e}", err_str

    def cleanup_active_live_broadcasts(self, only_cctv_prefix=False, exclude_broadcast_id=None):
        """
        Menutup siaran live yang sedang aktif atau menggantung (zombie streams) di YouTube,
        misalnya sisa siaran semalam saat laptop mati lampu atau sisa run sebelumnya.
        Hanya memeriksa siaran yang aktif (broadcastStatus='active') agar cepat, akurat, dan hemat kuota API.
        """
        if not self.service:
            self.authenticate()

        closed_count = 0
        deleted_count = 0
        try:
            list_args = {
                "part": "id,snippet,status",
                "broadcastStatus": "active",
                "maxResults": 25
            }

            resp = self.service.liveBroadcasts().list(**list_args).execute()
            items = resp.get("items", [])

            for item in items:
                b_id = item["id"]
                if exclude_broadcast_id and b_id == exclude_broadcast_id:
                    continue

                title = item.get("snippet", {}).get("title", "")
                status = item.get("status", {}).get("lifeCycleStatus", "")

                # Abaikan siaran yang sudah resmi complete / selesai
                if status in ["complete", "revoked"]:
                    continue

                # Filter prefix jika diminta
                if only_cctv_prefix:
                    is_match = (
                        self.title_prefix.lower() in title.lower() or
                        "cctv" in title.lower() or
                        "live stream" in title.lower() or
                        "stream key untuk" in title.lower()
                    )
                    if not is_match:
                        continue

                print(f"[YouTube API] Menangani siaran lama menggantung: '{title}' ({b_id}, Status: {status})...")

                # Jika statusnya aktif / menggantung (live, liveStarting, testing, testStarting):
                if status in ["live", "liveStarting", "testing", "testStarting"]:
                    try:
                        self.service.liveBroadcasts().transition(
                            broadcastStatus="complete",
                            id=b_id,
                            part="status"
                        ).execute()
                        closed_count += 1
                        print(f"[YouTube API] Siaran live {b_id} berhasil DITUTUP menjadi arsip (complete).")
                    except Exception as te:
                        print(f"[YouTube API] Transisi complete {b_id} gagal ({te}), mencoba unbind & hapus...")
                        try:
                            self.service.liveBroadcasts().bind(id=b_id, part="id,contentDetails").execute()
                        except Exception:
                            pass
                        try:
                            self.service.liveBroadcasts().delete(id=b_id).execute()
                            closed_count += 1
                            print(f"[YouTube API] Siaran {b_id} berhasil dihapus.")
                        except Exception as de:
                            print(f"[YouTube API] Gagal hapus {b_id}: {de}")

            msg_parts = []
            if closed_count > 0:
                msg_parts.append(f"{closed_count} siaran live zombie ditutup menjadi arsip video")
            if not msg_parts:
                return True, "Tidak ditemukan siaran live menggantung. Semua siaran di channel sudah bersih!", None
            return True, f"Berhasil membersihkan: {' dan '.join(msg_parts)}.", None
        except Exception as e:
            err_str = str(e)
            if "liveStreamingNotEnabled" in err_str or "The user is not enabled for live streaming" in err_str:
                return False, (
                    "Fitur Live Streaming belum aktif pada Channel YouTube Anda di YouTube Studio (Error 403 liveStreamingNotEnabled).\n\n"
                    "Langkah aktivasi:\n"
                    "1. Buka https://studio.youtube.com\n"
                    "2. Klik 'Create' (Buat) -> 'Go Live' (Mulai Siaran Langsung)\n"
                    "3. Lakukan verifikasi nomor HP yang diminta YouTube\n"
                    "4. Tunggu masa aktivasi hingga 24 jam agar YouTube mengaktifkan izin streaming."
                ), err_str
            elif "quotaExceeded" in err_str or "quota" in err_str.lower():
                return False, (
                    "Batas kuota harian (10.000 unit) YouTube Data API telah habis untuk hari ini (Error 403 quotaExceeded).\n\n"
                    "Tips: Gunakan Stream Key manual dari YouTube Studio untuk siaran langsung bebas kuota 24 jam."
                ), err_str

            print(f"[YouTube API] Error saat membersihkan siaran: {e}")
            return False, f"Terjadi kesalahan saat membersihkan siaran:\n{e}", err_str

    def create_broadcast_and_stream(self, custom_title=None, force_new=True):
        """Membuat Live Broadcast baru di YouTube (Dioptimasi hemat kuota API)"""
        if not self.service:
            self.authenticate()

        now_local = datetime.datetime.now()
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        title = custom_title or f"{self.title_prefix} - {now_local.strftime('%d %b %Y (%H:%M WIB)')}"
        description = (
            f"Sistem CCTV Otomatis ThinkPad X230\n"
            f"Mulai siaran: {now_local.strftime('%Y-%m-%d %H:%M:%S WIB')}\n"
            f"Maksimal durasi: 11 Jam (Auto-Archive)\n\n"
            f"--- TIMELINE KEJADIAN ---\n"
            f"00:00:00 - Siaran Dimulai\n"
        )

        # 1. Buat Live Broadcast
        broadcast_body = {
            "snippet": {
                "title": title,
                "description": description,
                # Gunakan waktu UTC +5 menit agar aman dan tidak pernah ditolak Google karena dianggap waktu lampau
                "scheduledStartTime": (now_utc + datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "status": {
                "privacyStatus": self.privacy_status,
                "selfDeclaredMadeForKids": False
            },
            "contentDetails": {
                "monitorStream": {
                    "enableMonitorStream": False
                },
                "enableDvr": True,
                "enableAutoStart": True,
                "enableAutoStop": False,
                "latencyPreference": self.latency_preference # ultraLow, low, atau normal
            }
        }
        broadcast_resp = self.service.liveBroadcasts().insert(
            part="snippet,status,contentDetails",
            body=broadcast_body
        ).execute()

        broadcast_id = broadcast_resp["id"]

        # 2. Dapatkan atau Buat Live Stream Ingestion (Stream Key)
        # Optimasi: Gunakan kembali stream ingestion yang sudah ada (hemat 50 unit kuota API!)
        stream_id = None
        stream_name = None
        ingestion_address = None

        try:
            s_list = self.service.liveStreams().list(part="id,cdn", mine=True, maxResults=5).execute()
            for s_item in s_list.get("items", []):
                ing_info = s_item.get("cdn", {}).get("ingestionInfo", {})
                if ing_info.get("streamName") and ing_info.get("ingestionAddress"):
                    stream_id = s_item["id"]
                    stream_name = ing_info["streamName"]
                    ingestion_address = ing_info["ingestionAddress"]
                    print(f"[YouTube API] Menggunakan Stream Ingestion yang sudah ada: {stream_id}")
                    break
        except Exception as le:
            print(f"[YouTube API] Info cek stream existing: {le}")

        if not stream_id:
            stream_body = {
                "snippet": {
                    "title": f"Stream Key untuk {title}"
                },
                "cdn": {
                    "frameRate": "variable",
                    "ingestionType": "rtmp",
                    "resolution": "variable"
                }
            }
            stream_resp = self.service.liveStreams().insert(
                part="snippet,cdn",
                body=stream_body
            ).execute()

            stream_id = stream_resp["id"]
            stream_name = stream_resp["cdn"]["ingestionInfo"]["streamName"]
            ingestion_address = stream_resp["cdn"]["ingestionInfo"]["ingestionAddress"]

        # 3. Ikat (Bind) Broadcast ke Stream
        self.service.liveBroadcasts().bind(
            id=broadcast_id,
            streamId=stream_id,
            part="id,contentDetails"
        ).execute()

        # 4. Masukkan ke Playlist target jika disetel
        if self.playlist_id:
            try:
                self.add_to_playlist(broadcast_id, self.playlist_id)
            except Exception as e:
                print(f"Gagal menambahkan ke playlist: {e}")

        return {
            "broadcast_id": broadcast_id,
            "stream_id": stream_id,
            "stream_key": stream_name,
            "rtmp_url": ingestion_address,
            "watch_url": f"https://youtu.be/{broadcast_id}",
            "title": title
        }

    def add_to_playlist(self, video_id, playlist_id):
        """Menambahkan video siaran ke playlist YouTube tertentu"""
        if not self.service:
            self.authenticate()

        body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
        return self.service.playlistItems().insert(part="snippet", body=body).execute()

    def wait_for_stream_and_transition(self, broadcast_id, stream_id=None, on_live_callback=None, on_progress_callback=None, max_retries=30, delay=3):
        """Memantau ingestion stream hingga aktif di YouTube (Hemat kuota: transisi hanya dipanggil maksimal 1x jika auto-start belum aktif)"""
        if not self.service:
            self.authenticate()

        print(f"[YouTube API] Memantau status siaran (Broadcast: {broadcast_id})...")
        transition_attempted = False

        for attempt in range(max_retries):
            time.sleep(delay)
            try:
                # 1. Cek status broadcast saat ini (hanya 1 unit kuota)
                b_resp = self.service.liveBroadcasts().list(part="status", id=broadcast_id).execute()
                b_items = b_resp.get("items", [])
                if b_items:
                    b_status = b_items[0]["status"].get("lifeCycleStatus")
                    print(f"[YouTube API] Status Broadcast: '{b_status}' (Cek ke-{attempt+1}/{max_retries})")
                    if b_status in ["live", "liveStarting"]:
                        print(f"[YouTube API] Siaran {broadcast_id} RESMI LIVE ({b_status})!")
                        if on_live_callback:
                            try:
                                on_live_callback()
                            except Exception as cbe:
                                print(f"[YouTube API Callback Error] {cbe}")
                        return True
                    elif b_status == "testing":
                        if on_progress_callback:
                            try:
                                on_progress_callback("YouTube dalam status Testing -> Mengubah ke LIVE...")
                            except Exception:
                                pass
                        if not transition_attempted:
                            try:
                                self.service.liveBroadcasts().transition(
                                    broadcastStatus="live",
                                    id=broadcast_id,
                                    part="status"
                                ).execute()
                                transition_attempted = True
                                print("[YouTube API] Transisi dari testing ke LIVE berhasil!")
                                if on_live_callback:
                                    try:
                                        on_live_callback()
                                    except Exception:
                                        pass
                                return True
                            except Exception as te:
                                print(f"[YouTube API] Menunggu transisi testing -> live: {te}")

                # 2. Cek status ingestion stream dari FFmpeg (hanya 1 unit kuota)
                stream_active = False
                if stream_id:
                    s_resp = self.service.liveStreams().list(part="status", id=stream_id).execute()
                    s_items = s_resp.get("items", [])
                    if s_items:
                        s_status = s_items[0]["status"].get("streamStatus")
                        print(f"[YouTube API] Status sinyal FFmpeg di YouTube: '{s_status}'")
                        if s_status == "active":
                            stream_active = True
                            if on_progress_callback:
                                try:
                                    on_progress_callback("Sinyal video diterima YouTube! Menghidupkan siaran...")
                                except Exception:
                                    pass
                        else:
                            if on_progress_callback:
                                try:
                                    on_progress_callback(f"Menunggu verifikasi sinyal oleh YouTube ({s_status})...")
                                except Exception:
                                    pass
                else:
                    stream_active = True

                # 3. Karena enableAutoStart: True, YouTube otomatis LIVE saat data video masuk.
                # Hanya jika stream_active sudah lama (attempt >= 8) dan belum live, lakukan transisi manual SEKALI SAJA!
                if stream_active and attempt >= 8 and not transition_attempted:
                    transition_attempted = True
                    try:
                        self.service.liveBroadcasts().transition(
                            broadcastStatus="live",
                            id=broadcast_id,
                            part="status"
                        ).execute()
                        print(f"[YouTube API] Transisi manual ke LIVE berhasil dikirim!")
                        if on_live_callback:
                            try:
                                on_live_callback()
                            except Exception:
                                pass
                        return True
                    except Exception as te:
                        err_str = str(te).lower()
                        if "redundant" in err_str or "already" in err_str or "invalidtransition" in err_str:
                            print("[YouTube API] Siaran sudah dalam status LIVE!")
                            if on_live_callback:
                                try:
                                    on_live_callback()
                                except Exception:
                                    pass
                            return True
            except Exception as e:
                print(f"[YouTube API] Menunggu stream active: {e}")

        return False

    def transition_to_live(self, broadcast_id):
        """Memaksa broadcast bertransisi ke status 'live' jika YouTube belum otomatis mengubahnya"""
        return self.wait_for_stream_and_transition(broadcast_id)

    def end_broadcast(self, broadcast_id):
        """Mengakhiri siaran lama secara rapi agar diproses YouTube menjadi arsip video utuh"""
        if not self.service:
            self.authenticate()

        try:
            return self.service.liveBroadcasts().transition(
                broadcastStatus="complete",
                id=broadcast_id,
                part="status"
            ).execute()
        except Exception as e:
            print(f"Gagal menutup broadcast {broadcast_id}: {e}")
            return None

    def append_description_timestamp(self, broadcast_id, timestamp_str, label):
        """Menambahkan bookmark timestamp ke deskripsi video live secara real-time"""
        if not self.service:
            return False
        try:
            # Ambil snippet video saat ini
            video_resp = self.service.videos().list(part="snippet", id=broadcast_id).execute()
            if not video_resp.get("items"):
                return False

            item = video_resp["items"][0]
            snippet = item["snippet"]
            old_desc = snippet.get("description", "")
            
            new_line = f"{timestamp_str} - {label}\n"
            if new_line not in old_desc:
                snippet["description"] = old_desc + new_line
                self.service.videos().update(part="snippet", body={"id": broadcast_id, "snippet": snippet}).execute()
                return True
        except Exception as e:
            print(f"Gagal update deskripsi: {e}")
        return False
