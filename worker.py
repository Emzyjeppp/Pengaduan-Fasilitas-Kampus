import redis
import json
import time
import os

# Konfigurasi Koneksi Redis (Harus sama dengan Producer)
broker = redis.Redis(host='localhost', port=6379, db=0)
QUEUE_NAME = 'antrean_laporan'
DATABASE_FILE = 'database_laporan.json'

def simpan_ke_file(data):
    """Fungsi untuk menyimpan data ke file JSON (Simulasi Database)"""
    # Cek jika file sudah ada, load isinya
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    # Tambahkan data baru
    existing_data.append(data)

    # Tulis ulang file
    with open(DATABASE_FILE, 'w') as f:
        json.dump(existing_data, f, indent=4)
    print(f"[STORAGE] Laporan {data['id']} tersimpan di {DATABASE_FILE}")

def main():
    print(" [*] Worker Pengaduan Kampus berjalan...")
    print(" [*] Menunggu pesan di antrean Redis...")

    while True:
        # 1. Mengambil pesan dari antrean (Blocking Pop)
        # 'brpop' akan menunggu sampai ada pesan masuk (lebih efisien dari loop biasa)
        # Ini mencerminkan proses 'Consumer App' menerima pesan [cite: 45]
        _, pesan_bytes = broker.brpop(QUEUE_NAME)
        
        # 2. Deserialisasi (Bytes -> JSON Object)
        pesan_data = json.loads(pesan_bytes)
        
        print(f" [x] Menerima Laporan ID: {pesan_data['id']}")
        print(f"     Dari: {pesan_data['pelapor']['nama']}")

        # 3. Simulasi Proses Berat (misal: Notifikasi ke Teknisi)
        # Delay ini membuktikan konsep ASINKRON. 
        # API sudah merespons User, tapi Worker baru mengerjakannya di sini.
        print(" [.] Memproses laporan...", end='', flush=True)
        time.sleep(5) # Pura-pura sibuk selama 5 detik
        print(" Selesai!")

        # 4. Update status dan Simpan
        pesan_data['status'] = 'DIPROSES_TEKNISI'
        pesan_data['waktu_diproses'] = time.ctime()
        
        simpan_ke_file(pesan_data)
        print(" [x] Siap menerima pesan berikutnya...\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nWorker dimatikan.")