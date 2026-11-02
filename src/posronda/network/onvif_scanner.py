"""
PosRonda ONVIF & Network RTSP Camera Scanner
Engine Deteksi Kamera Otomatis Ramah Orang Awam:
1. Protokol standar ONVIF WS-Discovery (Multicast UDP 239.255.255.250:3702)
2. Fast Subnet RTSP Scanner (Port 554, 8554, 8899, 10554, 80, 8080)
3. Smart Path Prober (Socket DESCRIBE probe dengan Basic Auth)
4. Auto-Builder RTSP URL dengan Username & Password kamera tanpa perlu ketik manual
"""

import socket
import uuid
import re
import time
import base64
import hashlib
from concurrent.futures import ThreadPoolExecutor

WS_DISCOVERY_IP = "239.255.255.250"
WS_DISCOVERY_PORT = 3702

PROBE_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope"
          xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
          xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
          xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
  <Header>
    <wsa:MessageID>urn:uuid:{msg_id}</wsa:MessageID>
    <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
    <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
  </Header>
  <Body>
    <d:Probe>
      <d:Types>dn:NetworkVideoTransmitter</d:Types>
    </d:Probe>
  </Body>
</Envelope>"""

COMMON_RTSP_PATHS = [
    "/Streaming/Channels/101",                   # Hikvision, Hilook, Ezviz (Main stream)
    "/cam/realmonitor?channel=1&subtype=0",      # Dahua, Imou (Main stream)
    "/stream1",                                  # TP-Link Tapo (Main stream)
    "/live/ch0",                                 # V380, V360, Tuya, generic
    "/ch0_0.264",                                # Xiongmai / XM / Yoosee
    "/onvif1",                                   # ONVIF profile 1
    "/unicast/c1/s0/live",                       # Uniview / UNV (Main stream)
    "/h264Preview_01_main",                      # Reolink (Main stream)
    "/ch0",                                      # Generic
    "/Streaming/Channels/102",                   # Hikvision, Ezviz (Sub stream)
    "/cam/realmonitor?channel=1&subtype=1",      # Dahua, Imou (Sub stream)
    "/stream2",                                  # TP-Link Tapo (Sub stream)
    "/11",                                       # Besder / generic
    "/ch0_1.264",                                # Xiongmai / XM (Sub stream)
    "/video1",                                   # Older IP cameras
    "/media/video1",                             # Sony / Axis
    "/onvif2",                                   # ONVIF profile 2
]

def get_local_ip_and_subnet():
    """Mendeteksi IP laptop lokal dan prefix subnet (contoh: '192.168.1.')"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "192.168.1.100"
    finally:
        s.close()

    parts = local_ip.split(".")
    if len(parts) == 4:
        subnet = f"{parts[0]}.{parts[1]}.{parts[2]}."
    else:
        subnet = "192.168.1."
    return local_ip, subnet

def discover_onvif_cameras(timeout=1.8):
    """Memindai kamera ONVIF dengan WS-Discovery UDP Multicast Probe"""
    cameras = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(timeout)
    
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    except Exception:
        pass

    msg_id = str(uuid.uuid4())
    probe_msg = PROBE_TEMPLATE.format(msg_id=msg_id).encode("utf-8")

    try:
        sock.sendto(probe_msg, (WS_DISCOVERY_IP, WS_DISCOVERY_PORT))
    except Exception as e:
        print(f"[ONVIF Scanner] Gagal kirim probe WS-Discovery: {e}")
        sock.close()
        return cameras

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            data, addr = sock.recvfrom(65535)
            sender_ip = addr[0]
            xml_text = data.decode("utf-8", errors="ignore")
            
            xaddrs = re.findall(r"http://([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)(?::([0-9]+))?", xml_text)
            onvif_port = 80
            cam_ip = sender_ip
            if xaddrs:
                cam_ip = xaddrs[0][0]
                if xaddrs[0][1]:
                    try:
                        onvif_port = int(xaddrs[0][1])
                    except Exception:
                        pass

            name = f"ONVIF Camera ({cam_ip})"
            scopes = re.findall(r"onvif://www\.onvif\.org/(?:name|hardware)/([^\s<]+)", xml_text)
            if scopes:
                name = f"ONVIF: {scopes[0]} ({cam_ip})"

            cameras[cam_ip] = {
                "ip": cam_ip,
                "name": name,
                "onvif_port": onvif_port,
                "protocol": "ONVIF",
                "rtsp_port": 554
            }
        except socket.timeout:
            break
        except Exception:
            continue

    sock.close()
    return cameras

def _check_port(ip, port, timeout=0.30):
    """Tes cepat apakah port TCP terbuka (timeout ~300ms)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        res = s.connect_ex((ip, port))
        s.close()
        return res == 0
    except Exception:
        return False

def scan_rtsp_network(subnet=None, ports=[554, 8554], max_workers=70):
    """Memindai seluruh subnet lokal (/24) untuk port RTSP yang terbuka"""
    if not subnet:
        _, subnet = get_local_ip_and_subnet()

    discovered = {}
    ip_list = [f"{subnet}{i}" for i in range(1, 255)]

    def scan_single(ip):
        for p in ports:
            if _check_port(ip, p):
                return ip, p
        return None, None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(scan_single, ip_list)
        for ip, port in results:
            if ip:
                discovered[ip] = {
                    "ip": ip,
                    "name": f"Kamera RTSP ({ip})",
                    "rtsp_port": port,
                    "protocol": "RTSP"
                }

    return discovered

def probe_rtsp_path(ip, port, path, username="", password="", timeout=0.8):
    """
    Kirim RTSP DESCRIBE request murni via TCP socket dengan dukungan penuh
    otentikasi RFC 2617 Digest dan Basic.
    200 OK -> Path valid & stream siap diambil langsung.
    401 -> Menuntut otentikasi (Digest challenge).
    404 -> Path tidak tersedia pada kamera ini.
    """
    clean_path = path if path.startswith("/") or not path else f"/{path}"
    uri = f"rtsp://{ip}:{port}{clean_path}"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))

        # 1. Permintaan DESCRIBE awal
        req = (
            f"DESCRIBE {uri} RTSP/1.0\r\n"
            f"CSeq: 1\r\n"
            f"User-Agent: PosRonda-CCTV-Scanner\r\n"
            f"Accept: application/sdp\r\n\r\n"
        )
        s.sendall(req.encode("ascii"))
        resp = s.recv(2048).decode("latin-1", errors="ignore")

        if "RTSP/1.0 200" in resp:
            s.close()
            return True, "200 OK"

        if "RTSP/1.0 401" in resp:
            # 2. Kamera meminta otentikasi
            if not username:
                s.close()
                return False, "401 Butuh Password"

            realm_m = re.search(r'realm="([^"]+)"', resp, re.IGNORECASE)
            nonce_m = re.search(r'nonce="([^"]+)"', resp, re.IGNORECASE)

            if realm_m and nonce_m:
                realm = realm_m.group(1)
                nonce = nonce_m.group(1)
                qop_m = re.search(r'qop="([^"]+)"', resp, re.IGNORECASE)
                qop = qop_m.group(1) if qop_m else None

                ha1 = hashlib.md5(f"{username}:{realm}:{password}".encode("utf-8")).hexdigest()
                ha2 = hashlib.md5(f"DESCRIBE:{uri}".encode("utf-8")).hexdigest()

                if qop and "auth" in qop.lower():
                    nc = "00000001"
                    cnonce = "0a4f113b"
                    resp_hash = hashlib.md5(f"{ha1}:{nonce}:{nc}:{cnonce}:auth:{ha2}".encode("utf-8")).hexdigest()
                    auth_hdr = (
                        f'Digest username="{username}", realm="{realm}", nonce="{nonce}", '
                        f'uri="{uri}", response="{resp_hash}", qop=auth, nc={nc}, cnonce="{cnonce}"'
                    )
                else:
                    resp_hash = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode("utf-8")).hexdigest()
                    auth_hdr = f'Digest username="{username}", realm="{realm}", nonce="{nonce}", uri="{uri}", response="{resp_hash}"'

                req2 = (
                    f"DESCRIBE {uri} RTSP/1.0\r\n"
                    f"CSeq: 2\r\n"
                    f"User-Agent: PosRonda-CCTV-Scanner\r\n"
                    f"Accept: application/sdp\r\n"
                    f"Authorization: {auth_hdr}\r\n\r\n"
                )

                try:
                    s.sendall(req2.encode("ascii"))
                    resp2 = s.recv(2048).decode("latin-1", errors="ignore")
                except Exception:
                    s.close()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(timeout)
                    s.connect((ip, port))
                    s.sendall(req2.encode("ascii"))
                    resp2 = s.recv(2048).decode("latin-1", errors="ignore")

                s.close()
                if "RTSP/1.0 200" in resp2:
                    return True, "200 OK"
                if "RTSP/1.0 404" in resp2:
                    return False, "404 Not Found"
                if "RTSP/1.0 401" in resp2:
                    return False, "401 Kredensial Salah"
                return False, resp2.split("\r\n")[0] if resp2 else "Empty"

            else:
                token = base64.b64encode(f"{username}:{password}".encode()).decode()
                req_basic = (
                    f"DESCRIBE {uri} RTSP/1.0\r\n"
                    f"CSeq: 2\r\n"
                    f"User-Agent: PosRonda-CCTV-Scanner\r\n"
                    f"Accept: application/sdp\r\n"
                    f"Authorization: Basic {token}\r\n\r\n"
                )
                s.close()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                s.connect((ip, port))
                s.sendall(req_basic.encode("ascii"))
                resp_basic = s.recv(2048).decode("latin-1", errors="ignore")
                s.close()
                if "RTSP/1.0 200" in resp_basic:
                    return True, "200 OK"
                if "RTSP/1.0 404" in resp_basic:
                    return False, "404 Not Found"
                if "RTSP/1.0 401" in resp_basic:
                    return False, "401 Kredensial Salah"
                return False, resp_basic.split("\r\n")[0] if resp_basic else "Empty"

        s.close()
        if "RTSP/1.0 404" in resp:
            return False, "404 Not Found"
        return False, resp.split("\r\n")[0] if resp else "Empty"

    except Exception:
        return False, "Error / Offline"

def build_rtsp_url(ip, port=554, username="", password="", path="/Streaming/Channels/101"):
    """Membangun string RTSP lengkap dengan format yang benar"""
    auth = ""
    u = username.strip() if username else ""
    p = password.strip() if password else ""
    if u and p:
        auth = f"{u}:{p}@"
    elif u:
        auth = f"{u}@"
    
    clean_path = path if path.startswith("/") or not path else f"/{path}"
    return f"rtsp://{auth}{ip}:{port}{clean_path}"

def find_best_rtsp_url(ip, port=554, username="", password="", probe=True, cam_hint="", return_auth_info=False):
    """
    Mencari jalur RTSP terbaik untuk IP kamera tertentu.
    Jika probe=True, mencoba probe seluruh jalur umum secara paralel dengan Digest Auth.
    """
    hint_lower = str(cam_hint).lower()
    ordered_paths = list(COMMON_RTSP_PATHS)

    if any(h in hint_lower for h in ["hikvision", "hilook", "ezviz"]):
        preferred = ["/Streaming/Channels/101", "/Streaming/Channels/102"]
        ordered_paths = preferred + [p for p in ordered_paths if p not in preferred]
    elif any(d in hint_lower for d in ["dahua", "imou", "general"]):
        preferred = ["/cam/realmonitor?channel=1&subtype=0", "/cam/realmonitor?channel=1&subtype=1"]
        ordered_paths = preferred + [p for p in ordered_paths if p not in preferred]
    elif any(t in hint_lower for t in ["tapo", "tp-link"]):
        preferred = ["/stream1", "/stream2"]
        ordered_paths = preferred + [p for p in ordered_paths if p not in preferred]
    elif "reolink" in hint_lower:
        preferred = ["/h264Preview_01_main", "/h264Preview_01_sub"]
        ordered_paths = preferred + [p for p in ordered_paths if p not in preferred]
    elif any(x in hint_lower for x in ["xm", "xiongmai", "yoosee"]):
        preferred = ["/ch0_0.264", "/onvif1", "/ch0"]
        ordered_paths = preferred + [p for p in ordered_paths if p not in preferred]
    elif "uniview" in hint_lower or "unv" in hint_lower:
        preferred = ["/unicast/c1/s0/live", "/unicast/c1/s1/live"]
        ordered_paths = preferred + [p for p in ordered_paths if p not in preferred]

    if not probe:
        primary = build_rtsp_url(ip, port, username, password, ordered_paths[0])
        candidates = [build_rtsp_url(ip, port, username, password, p) for p in ordered_paths]
        if return_auth_info:
            return primary, candidates, False, False
        return primary, candidates, False

    verified = False
    needs_auth = False
    best_path = ordered_paths[0]

    def _test_p(p):
        ok, msg = probe_rtsp_path(ip, port, p, username, password, timeout=0.8)
        return p, ok, msg

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(_test_p, ordered_paths))

    status_map = {p: (ok, msg) for p, ok, msg in results}
    for p in ordered_paths:
        ok, msg = status_map.get(p, (False, ""))
        if ok:
            best_path = p
            verified = True
            break
        if "401" in msg:
            needs_auth = True

    primary = build_rtsp_url(ip, port, username, password, best_path)
    candidates = [build_rtsp_url(ip, port, username, password, p) for p in ordered_paths]
    if return_auth_info:
        return primary, candidates, verified, needs_auth
    return primary, candidates, verified

def scan_all_cameras(username="admin", password="", default_port=554, probe=True):
    """
    Pindai seluruh kamera di jaringan dan buat URL RTSP yang siap digunakan
    oleh pengguna awam dengan username & password yang dimasukkan.
    """
    print("[PosRonda Scanner] Memulai pemindaian ONVIF & Jaringan...")
    
    # 1. Pindai ONVIF WS-Discovery
    onvif_cams = discover_onvif_cameras(timeout=1.6)
    
    # 2. Pindai port RTSP di seluruh subnet
    rtsp_cams = scan_rtsp_network(ports=[default_port, 8554] if default_port != 8554 else [554, 8554], max_workers=70)
    
    # 3. Gabungkan hasil
    combined = {}
    for ip, data in rtsp_cams.items():
        combined[ip] = data
        
    for ip, data in onvif_cams.items():
        if ip in combined:
            combined[ip]["name"] = data["name"]
            combined[ip]["onvif_port"] = data.get("onvif_port", 80)
            combined[ip]["protocol"] = "ONVIF+RTSP"
        else:
            combined[ip] = data

    final_list = []
    sorted_ips = sorted(combined.keys(), key=lambda x: [int(p) for p in x.split('.') if p.isdigit()])

    for ip in sorted_ips:
        cam = combined[ip]
        port = cam.get("rtsp_port", default_port)
        cam_hint = cam.get("name", "")
        primary_url, candidates, verified, needs_auth = find_best_rtsp_url(
            ip, port, username, password, probe=probe, cam_hint=cam_hint, return_auth_info=True
        )
        
        final_list.append({
            "ip": ip,
            "name": cam.get("name", f"Kamera ({ip})"),
            "protocol": cam.get("protocol", "RTSP"),
            "rtsp_port": port,
            "primary_url": primary_url,
            "candidate_urls": candidates,
            "verified": verified,
            "needs_auth": needs_auth
        })

    print(f"[PosRonda Scanner] Selesai! Ditemukan {len(final_list)} kamera aktif.")
    return final_list

def extract_ip(url_or_text):
    """Mengekstrak alamat IPv4 dari URL atau teks apa pun"""
    if not url_or_text:
        return None
    m = re.search(r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})", str(url_or_text))
    return m.group(1) if m else None

def extract_credentials_and_path(url):
    """Mengekstrak user, pass, port, dan path dari RTSP URL"""
    if not url:
        return "admin", "", 554, "/live/ch0"
    m = re.search(r"rtsp://(?:([^:]+)(?::([^@]+))?@)?([^:/]+)(?::([0-9]+))?(/.*)?", url)
    if not m:
        return "admin", "", 554, "/live/ch0"
    user = m.group(1) or "admin"
    pwd = m.group(2) or ""
    port = int(m.group(4)) if m.group(4) else 554
    path = m.group(5) or "/live/ch0"
    return user, pwd, port, path

def replace_ip_in_url(old_url, new_ip):
    """
    Mengganti HANYA bagian IP address pada RTSP URL,
    menjaga username, password, port, dan path asli tetap utuh 100%.
    """
    if not old_url or not re.search(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", old_url):
        return f"rtsp://admin@{new_ip}:554/live/ch0"
    return re.sub(r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})", new_ip, old_url, count=1)

def replace_credentials_in_url(url, new_user, new_pass):
    """Mengganti username & password pada URL RTSP yang sudah ada"""
    _, _, port, path = extract_credentials_and_path(url)
    ip = extract_ip(url)
    if not ip:
        return url
    return build_rtsp_url(ip, port, new_user, new_pass, path)

def auto_assign_to_slots(scanned_cams, username="admin", password="", current_slots=None, max_slots=8):
    """
    Memetakan kamera hasil pemindaian ke slot CCTV secara cerdas (mendukung hingga 8-16 kamera).
    Bagi orang awam, langsung memasangkan URL RTSP yang siap pakai.
    """
    slots = []
    total_slots = max(4, min(max_slots, len(scanned_cams)))
    if current_slots and len(current_slots) > total_slots:
        total_slots = len(current_slots)

    limit = min(total_slots, len(scanned_cams))
    
    for i in range(total_slots):
        slot_id = i + 1
        if i < limit:
            cam = scanned_cams[i]
            ip = cam["ip"]
            port = cam.get("rtsp_port", 554)
            name = f"Kamera {slot_id} ({ip})"
            url = cam.get("primary_url") or build_rtsp_url(ip, port, username, password, "/live/ch0")
            slots.append({
                "id": slot_id,
                "name": name,
                "rtsp_url": url,
                "enabled": True
            })
        else:
            old = current_slots[i] if current_slots and i < len(current_slots) else None
            if old:
                slots.append(old)
            else:
                slots.append({
                    "id": slot_id,
                    "name": f"Kamera {slot_id}",
                    "rtsp_url": "",
                    "enabled": False
                })
    return slots
