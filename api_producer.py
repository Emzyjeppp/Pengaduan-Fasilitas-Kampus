import json
import uuid
import os
import redis
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- KONFIGURASI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(BASE_DIR, 'database_laporan.json')
# Folder untuk menyimpan foto upload
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Pastikan folder upload ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CONST_QUEUE_NAME = 'antrean_laporan'

# --- KONEKSI REDIS ---
try:
    broker = redis.Redis(host='localhost', port=6379, db=0)
    broker.ping() 
except redis.ConnectionError:
    print(" [!] ERROR: Redis mati. Jalankan redis-server.exe!")

# --- HELPER ---
def baca_database():
    if not os.path.exists(DATABASE_FILE): return []
    try:
        with open(DATABASE_FILE, 'r') as f: return json.load(f)
    except: return []

def simpan_database(data_list):
    try:
        with open(DATABASE_FILE, 'w') as f: json.dump(data_list, f, indent=4)
        return True
    except: return False

# --- FRONTEND ---
@app.route('/', methods=['GET'])
def home(): return render_template('index.html')

@app.route('/admin', methods=['GET'])
def halaman_admin(): return render_template('admin.html')

# --- API ENDPOINTS ---

# [POST] TERIMA LAPORAN + FOTO + PRIORITAS
@app.route('/api/lapor', methods=['POST'])
def buat_laporan():
    # 1. Ambil Data Teks (Form Data)
    nama = request.form.get('nama')
    lokasi = request.form.get('lokasi')
    deskripsi = request.form.get('deskripsi')
    prioritas = request.form.get('prioritas', 'Biasa') # Default Biasa

    if not nama or not deskripsi:
        return jsonify({"error": "Data tidak lengkap"}), 400

    # 2. Proses Upload Foto (Jika Ada)
    nama_file_foto = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file.filename != '':
            # Amankan nama file dan simpan
            filename = secure_filename(file.filename)
            # Tambahkan timestamp agar nama file unik
            unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
            nama_file_foto = unique_name

    laporan_id = str(uuid.uuid4())[:8]
    payload = {
        "id": laporan_id,
        "waktu_lapor": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pelapor": {"nama": nama},
        "lokasi": lokasi,          # SUDAH DITAMBAHKAN
        "prioritas": prioritas,    # SUDAH DITAMBAHKAN
        "foto": nama_file_foto,    # SUDAH DITAMBAHKAN
        "deskripsi": deskripsi,
        "status": "PENDING"
    }

    try:
        broker.lpush(CONST_QUEUE_NAME, json.dumps(payload))
    except redis.ConnectionError:
        return jsonify({"error": "Broker mati"}), 500

    return jsonify({"message": "Sukses", "id_laporan": laporan_id, "status": "PENDING"}), 202

# [GET] Cek Status
@app.route('/api/lapor/<laporan_id>', methods=['GET'])
def get_laporan(laporan_id):
    semua = baca_database()
    laporan = next((i for i in semua if i["id"] == laporan_id), None)
    return jsonify(laporan) if laporan else (jsonify({"status": "PENDING"}), 404)

# [PUT] Update Status
@app.route('/api/lapor/<laporan_id>', methods=['PUT'])
def update_status(laporan_id):
    data = request.json
    semua = baca_database()
    for item in semua:
        if item['id'] == laporan_id:
            item['status'] = data.get('status')
            item['waktu_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            simpan_database(semua)
            return jsonify({"msg": "Updated"}), 200
    return jsonify({"error": "Not found"}), 404

# [GET] Semua Laporan (Untuk Admin)
@app.route('/api/semua_laporan', methods=['GET'])
def get_semua(): return jsonify(baca_database()), 200

# [GET] Antrean
@app.route('/api/antrean', methods=['GET'])
def cek_antrean():
    try: return jsonify({"jumlah_antrean": broker.llen(CONST_QUEUE_NAME)}), 200
    except: return jsonify({"jumlah_antrean": 0}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')