import json
import uuid
import os
from datetime import datetime
from flask import Flask, request, jsonify
import redis

app = Flask(__name__)

# --- KONFIGURASI ---
# Koneksi ke Redis (Message Broker)
# Pastikan Redis server sudah berjalan di port default 6379
broker = redis.Redis(host='localhost', port=6379, db=0)

CONST_QUEUE_NAME = 'antrean_laporan'
CONST_DB_FILE = 'database_laporan.json'

# --- HELPER FUNCTION ---
def baca_database():
    """Membaca data dari file JSON (Simulasi Database Shared)"""
    if not os.path.exists(CONST_DB_FILE):
        return []
    try:
        with open(CONST_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

# --- ENDPOINTS ---

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "info": "Sistem Pengaduan Fasilitas Kampus API",
        "endpoints": {
            "POST /api/lapor": "Kirim laporan baru",
            "GET /api/laporan/<id>": "Cek status laporan spesifik",
            "GET /api/antrean": "Cek jumlah antrean di broker"
        }
    })

# 1. Endpoint POST: Menerima Laporan (Producer)
# Memenuhi syarat: Melibatkan minimal dua komponen layanan 
@app.route('/api/lapor', methods=['POST'])
def buat_laporan():
    data = request.json
    
    # Validasi Input Sederhana
    if not data or 'deskripsi' not in data or 'pelapor' not in data:
        return jsonify({"error": "Data tidak lengkap. Wajib ada 'deskripsi' dan 'pelapor'"}), 400

    # Menyiapkan Data
    laporan_id = str(uuid.uuid4())[:8]  # ID unik pendek
    payload = {
        "id": laporan_id,
        "waktu_lapor": datetime.now().isoformat(),
        "pelapor": data['pelapor'],
        "lokasi": data.get('lokasi', '-'),
        "kerusakan": data.get('kerusakan', 'Umum'),
        "deskripsi": data['deskripsi'],
        "status": "PENDING"  # Status awal
    }

    # Serialisasi ke JSON String
    pesan_json = json.dumps(payload)

    # KIRIM KE MESSAGE BROKER (Redis)
    # Memenuhi syarat: Menggunakan message broker untuk komunikasi asinkron 
    try:
        broker.lpush(CONST_QUEUE_NAME, pesan_json)
    except redis.ConnectionError:
        return jsonify({"error": "Gagal terhubung ke Message Broker"}), 500

    # Respon Cepat ke Client (Asinkron)
    # API langsung menjawab tanpa menunggu Worker selesai memproses
    return jsonify({
        "message": "Laporan berhasil diterima dan masuk antrean.",
        "id_laporan": laporan_id,
        "status": "PENDING",
        "info": "Gunakan ID laporan untuk cek status secara berkala."
    }), 202


# 2. Endpoint GET: Cek Status Laporan Tertentu
# Memenuhi syarat: Minimal 2 endpoint dasar (POST, GET) 
@app.route('/api/laporan/<laporan_id>', methods=['GET'])
def get_laporan(laporan_id):
    # Cek di database yang sudah diproses worker
    semua_laporan = baca_database()
    
    # Mencari laporan berdasarkan ID
    laporan = next((item for item in semua_laporan if item["id"] == laporan_id), None)
    
    if laporan:
        return jsonify(laporan), 200
    else:
        # Jika tidak ada di DB, mungkin masih di antrean Redis?
        return jsonify({
            "message": "Laporan tidak ditemukan atau masih dalam antrean tunggu.",
            "id": laporan_id
        }), 404


# 3. Endpoint GET: Cek Kesehatan Sistem (Monitoring)
@app.route('/api/antrean', methods=['GET'])
def cek_antrean():
    try:
        # Menghitung jumlah pesan yang belum diambil Worker
        jumlah = broker.llen(CONST_QUEUE_NAME)
        return jsonify({
            "status_broker": "Connected",
            "jumlah_antrean": jumlah
        }), 200
    except redis.ConnectionError:
        return jsonify({"status_broker": "Disconnected"}), 500

if __name__ == '__main__':
    # Menjalankan server Flask
    print("API Server berjalan di http://localhost:5000")
    app.run(debug=True, port=5000)