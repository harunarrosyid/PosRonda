"""
generate_license.py - Generator Kunci Lisensi PosRonda PRO untuk Admin
Digunakan saat memproses pesanan lisensi dari pembeli via email atau web.
"""
import sys
import hashlib

LICENSE_SECRET_SALT = "POSRONDA_SECURE_SALT_v4_2026_CORE"

def generate(holder, org="Komersial"):
    raw = f"{holder.strip()}:{org.strip()}:{LICENSE_SECRET_SALT}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()

def main():
    if len(sys.argv) < 2:
        print("Penggunaan:")
        print("  python scripts/generate_license.py \"<Nama Pemilik>\" [\"<Nama Toko/Organisasi>\"]")
        print("\nContoh:")
        print("  python scripts/generate_license.py \"Budi Santoso\" \"Berkah CCTV Security\"")
        sys.exit(1)

    holder = sys.argv[1].strip()
    org = sys.argv[2].strip() if len(sys.argv) > 2 else "Komersial"
    key = generate(holder, org)

    print("\n" + "=" * 55)
    print("       POSRONDA PRO LICENSE KEY GENERATOR")
    print("=" * 55)
    print(f"Nama Pemilik : {holder}")
    print(f"Organisasi   : {org}")
    print(f"Serial Key   : {key}")
    print("=" * 55)
    print("\nTemplate Balasan Email / WhatsApp ke Pembeli:")
    print("-" * 55)
    print(f"Halo {holder},\n")
    print("Terima kasih atas pemesanan lisensi PosRonda PRO.")
    print("Berikut data lisensi resmi Anda:\n")
    print(f"• Nama Pemilik    : {holder}")
    print(f"• Organisasi/Toko : {org}")
    print(f"• Serial Key      : {key}\n")
    print("Cara Aktivasi:")
    print("1. Buka PosRonda di laptop Anda.")
    print("2. Tekan tombol F2 (Pengaturan), lalu buka tab 'Lisensi'.")
    print("3. Masukkan Nama Pemilik, Organisasi, dan Serial Key di atas.")
    print("4. Klik 'Pasang Lisensi PRO', lalu restart aplikasi.")
    print("-" * 55 + "\n")

if __name__ == "__main__":
    main()
