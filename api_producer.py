import json
import uuid
import os
import redis
from datetime import datetime
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# --- KONFIGURASI ---
# Koneksi ke Redis (Message Broker)
# Pastikan Redis server sudah berjalan di port default 6379
# Ini memenuhi syarat penggunaan Message Broker [cite: 5, 26]
try:
    broker = redis.Redis(host='localhost', port=6379, db=0)
    broker.ping() # Cek koneksi awal
    print(" [*] Terhubung ke Redis Message Broker")
except redis.ConnectionError:
    print(" [!] Gagal terhubung ke Redis. Pastikan server Redis menyala!")

# Konfigurasi Nama Queue dan File Database (Harus sama dengan worker.py)
CONST_QUEUE_NAME = 'antrean_laporan'
CONST_DB_FILE = 'database_laporan.json'

# --- HELPER FUNCTION ---
def baca_database():
    """Membaca data dari file JSON (Simulasi Database Shared)"""
    # Fungsi ini mensimulasikan pengecekan data yang sudah diproses oleh Worker [cite: 60]
    if not os.path.exists(CONST_DB_FILE):
        return []
    try:
        with open(CONST_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

# --- ROUTE UTAMA (TAMPILAN WEB) ---
@app.route('/', methods=['GET'])
def home():
    # Render file HTML yang ada di folder 'templates'
    return render_template('index.html')

# --- ENDPOINTS API ---

# 1. Endpoint POST: Menerima Laporan (Producer)
# Alur Sinkron: Client -> API -> Broker [cite: 28, 41]
@app.route('/api/lapor', methods=['POST'])
def buat_laporan():
    data = request.json
    
    # Validasi Input Sederhana
    if not data or 'pelapor' not in data:
        return jsonify({"error": "Data tidak lengkap"}), 400

    # Menyiapkan Data Laporan
    laporan_id = str(uuid.uuid4())[:8]  # ID unik pendek
    payload = {
        "id": laporan_id,
        "waktu_lapor": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pelapor": data['pelapor'],
        "lokasi": data.get('lokasi', '-'),
        "kerusakan": data.get('kerusakan', 'Umum'),
        "deskripsi": data.get('deskripsi', '-'),
        "status": "PENDING"  # Status awal sebelum diproses worker
    }

    # Serialisasi ke JSON String agar bisa dikirim lewat jaringan
    pesan_json = json.dumps(payload)

    # KIRIM KE MESSAGE BROKER (Redis)
    # Ini adalah inti dari komunikasi Asinkron [cite: 47]
    try:
        broker.lpush(CONST_QUEUE_NAME, pesan_json)
    except redis.ConnectionError:
        return jsonify({"error": "Gagal terhubung ke Message Broker"}), 500

    # Respon Cepat ke Client (202 Accepted)
    # Memberi tahu user bahwa laporan diterima tanpa menunggu teknisi [cite: 36, 37]
    return jsonify({
        "message": "Laporan berhasil diterima dan masuk antrean.",
        "id_laporan": laporan_id,
        "status": "PENDING"
    }), 202


# 2. Endpoint GET: Cek Status Laporan Tertentu
# Digunakan oleh Frontend untuk polling status [cite: 59]
@app.route('/api/laporan/<laporan_id>', methods=['GET'])
def get_laporan(laporan_id):
    # Cek di database (file JSON) apakah worker sudah selesai memproses?
    semua_laporan = baca_database()
    
    # Mencari laporan berdasarkan ID
    laporan = next((item for item in semua_laporan if item["id"] == laporan_id), None)
    
    if laporan:
        # Jika ketemu, berarti Worker sudah selesai
        return jsonify(laporan), 200
    else:
        # Jika tidak ada di DB, berarti masih antre di Redis atau ID salah
        return jsonify({
            "message": "Laporan sedang dalam antrean atau tidak ditemukan.",
            "status": "PENDING"
        }), 404


# 3. Endpoint GET: Monitoring Antrean (Untuk Demo)
@app.route('/api/antrean', methods=['GET'])
def cek_antrean():
    try:
        # Menghitung jumlah pesan yang "parkir" di Redis Queue
        jumlah = broker.llen(CONST_QUEUE_NAME)
        return jsonify({
            "status_broker": "Online",
            "jumlah_antrean": jumlah
        }), 200
    except Exception:
        return jsonify({"status_broker": "Offline", "jumlah_antrean": 0}), 500

if __name__ == '__main__':
    print("-------------------------------------------------")
    print(" SISTEM PENGADUAN KAMPUS (API PRODUCER) BERJALAN ")
    print(" Akses Web di: http://localhost:5000")
    print("-------------------------------------------------")
    app.run(debug=True, port=5000)