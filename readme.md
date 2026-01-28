# 📢 Sistem Pengaduan Fasilitas Kampus (Distributed System)

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-green?style=flat&logo=flask)
![Redis](https://img.shields.io/badge/Redis-Message%20Broker-red?style=flat&logo=redis)
![Status](https://img.shields.io/badge/Status-Active-success)

Sistem pelaporan kerusakan fasilitas kampus berbasis **Sistem Terdistribusi**. Proyek ini memisahkan layanan penerima pesan (*Producer*) dan pemroses pesan (*Consumer*) menggunakan **Redis Message Broker** untuk menjamin data laporan tetap aman dan antarmuka pengguna tetap responsif (*Non-blocking*) meskipun server sedang sibuk.

> **Tugas Besar / Project Based Learning (PBL) - Mata Kuliah Sistem Terdistribusi**

---

## 🌟 Fitur Unggulan

* ✅ **Arsitektur Asinkron:** Pengiriman laporan tidak membuat antarmuka pengguna macet.
* ✅ **Message Queue:** Menggunakan Redis `LPUSH` dan `BRPOP` untuk antrean tugas yang persisten.
* ✅ **Prioritas Laporan:** Kategorisasi urgensi (Darurat 🔴, Sedang 🟡, Biasa 🟢).
* ✅ **Bukti Foto:** Mahasiswa dapat mengunggah foto kerusakan fasilitas.
* ✅ **Real-time Monitoring:** Status laporan (Pending -> Diproses -> Selesai) terpantau langsung.
* ✅ **Push Notification:** Notifikasi browser muncul otomatis saat laporan selesai diperbaiki.

---

## 🏗️ Arsitektur Sistem

Sistem ini terdiri dari 3 komponen utama yang berjalan secara independen:

1.  **Producer (Flask API):** Menerima input HTTP dari mahasiswa dan mengirimkan *payload* ke antrean Redis.
2.  **Message Broker (Redis):** Menampung antrean laporan (buffer) di memori.
3.  **Consumer (Python Worker):** Mengambil tugas dari Redis, memprosesnya (simulasi perbaikan), dan menyimpan ke database JSON.

```mermaid
graph LR
    A[Mahasiswa] -- POST /api/lapor --> B(Flask API)
    B -- Push Job --> C[(Redis Queue)]
    C -- Pop Job --> D[Python Worker]
    D -- Save Data --> E[(Database JSON)]
    D -- Update Status --> E

## 📂 Struktur Folder

```text
Sistem-Pengaduan-Kampus/
├── static/
│   └── uploads/          # Folder penyimpanan foto bukti pelapor
├── templates/
│   ├── index.html        # Halaman Utama (Form Pelaporan Mahasiswa)
│   └── admin.html        # Dashboard Admin (Teknisi)
├── api_producer.py       # Server Backend (Flask App)
├── worker.py             # Background Worker (Consumer)
├── database_laporan.json # Database sederhana berbasis file
├── requirements.txt      # Daftar library Python
└── README.md             # Dokumentasi Proyek

## 🚀 Cara Menjalankan (Installation)

### Prasyarat
* Python 3.x terinstall.
* Redis Server terinstall dan berjalan (Default Port 6379).

### Langkah 1: Clone & Install
```bash
git clone [https://github.com/Emzyjeppp/Sistem-Pengaduan-Kampus.git](https://github.com/Emzyjeppp/Sistem-Pengaduan-Kampus.git)
cd Sistem-Pengaduan-Kampus
pip install flask redis