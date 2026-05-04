# Sistem Manajemen Biaya Sekolah Renang Sibahah

## 📋 Ringkasan

Sistem ini memungkinkan admin untuk mengelola biaya pendaftaran (Uang Pendaftaran) dan SPP bulanan (Uang SPP) yang akan ditampilkan secara otomatis di halaman pendaftaran dan pembayaran.

## 🗄️ Database Schema

### Tabel: `biaya_sekolah`
Menyimpan konfigurasi biaya sekolah yang dapat diubah kapan saja.

```sql
CREATE TABLE biaya_sekolah (
    id INT PRIMARY KEY AUTO_INCREMENT,
    uang_pendaftaran INT NOT NULL DEFAULT 0,    -- Biaya pendaftaran (Rp)
    uang_spp INT NOT NULL DEFAULT 0,            -- Biaya SPP per bulan (Rp)
    tanggal_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    keterangan VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Kolom di Tabel `pendaftaran` (ditambahkan)
- `uang_pendaftaran INT` - Biaya pendaftaran saat siswa terdaftar
- `uang_spp INT` - Biaya SPP per bulan
- `jumlah_bulan INT` - Jumlah bulan berlangganan (default 1)
- `total_biaya INT` - Total biaya = uang_pendaftaran + (uang_spp × jumlah_bulan)

## 🔧 Setup Instructions

### 1. Jalankan SQL Script
```bash
# Import file sql_biaya.sql ke database
mysql -u root -p sekolah_renang_sibahah < sql_biaya.sql
```

atau via phpMyAdmin:
- Buka Database: `sekolah_renang_sibahah`
- Klik Import
- Pilih file `sql_biaya.sql`
- Klik Go

### 2. Flask API Endpoints

#### GET `/api/biaya`
Mengambil data biaya saat ini.

**Response:**
```json
{
    "success": true,
    "uang_pendaftaran": 40000,
    "uang_spp": 100000,
    "keterangan": "Biaya standar sekolah renang"
}
```

#### PUT `/api/biaya`
Memperbarui data biaya (hanya admin).

**Request Body:**
```json
{
    "uang_pendaftaran": 40000,
    "uang_spp": 100000,
    "keterangan": "Biaya standar sekolah renang"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Biaya berhasil diperbarui"
}
```

## 📱 Frontend Components

### 1. **Admin Settings** (`/admin/settings`)
- Form input untuk mengubah Uang Pendaftaran dan SPP
- Button Simpan untuk menyimpan perubahan ke database
- Button Reset untuk memuat ulang data dari database
- Validasi input (tidak boleh 0 atau negatif)
- Pesan feedback (sukses/error)

### 2. **Halaman Pendaftaran** (`/pendaftaran`)
- Menampilkan biaya secara dinamis dari API
- Update otomatis jika admin mengubah biaya
- Format Rupiah dengan pemisah ribuan
- Hitung total = Uang Pendaftaran + SPP (1 bulan)

### 3. **Halaman Pembayaran** (`/pembayaran`)
- Menampilkan biaya pendaftaran siswa
- Menampilkan SPP untuk 1 bulan
- Menampilkan total pembayaran
- "Jumlah Transfer" di atas menampilkan total yang sama

## 🎯 Fitur Utama

✅ **Admin dapat mengubah biaya kapan saja**
- Perubahan otomatis muncul di halaman pendaftaran & pembayaran
- Data tersimpan di database (bukan hardcoded)

✅ **Format Rupiah Otomatis**
- Contoh: 40000 → Rp40.000
- Dengan pemisah ribuan yang rapi

✅ **Validasi Input**
- Biaya tidak boleh kosong
- Biaya tidak boleh negatif
- Pesan error jika validasi gagal

✅ **Loading Data dari API**
- Fallback ke nilai default jika API error
- Async/await untuk non-blocking

✅ **User Experience**
- Loading indicator saat menyimpan
- Pesan feedback (hijau = sukses, merah = error)
- Responsive design untuk mobile

## 🔄 Data Flow

```
┌─────────────────────────────────────┐
│  Admin mengubah biaya di Settings   │
└──────────────┬──────────────────────┘
               │
               ▼
        PUT /api/biaya
               │
               ▼
┌─────────────────────────────────────┐
│   Database (biaya_sekolah table)    │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
  GET /api/biaya   GET /api/biaya
       │                │
       ▼                ▼
Pendaftaran.html   Pembayaran.html
```

## 📝 Contoh Perubahan Biaya

### Scenario 1: Ubah Uang Pendaftaran
- Admin: Ubah dari Rp40.000 → Rp50.000
- Hasil: Semua calon siswa akan melihat biaya pendaftaran Rp50.000

### Scenario 2: Ubah SPP
- Admin: Ubah dari Rp100.000 → Rp120.000
- Hasil: Semua calon siswa akan melihat SPP Rp120.000

## 🚀 Testing

### Test di Halaman Pendaftaran:
1. Buka `http://localhost:5000/pendaftaran`
2. Tunggu halaman load
3. Lihat ringkasan biaya
4. Ubah biaya di admin settings
5. Refresh halaman pendaftaran
6. Verifikasi biaya berubah

### Test di Halaman Pembayaran:
1. Lakukan pendaftaran lengkap
2. Lanjut ke pembayaran
3. Lihat biaya di "Data Registrasi Anda"
4. Lihat "Jumlah Transfer" di atas
5. Ubah biaya di admin settings
6. Refresh pembayaran.html
7. Verifikasi biaya berubah

## ⚠️ Catatan Penting

- API `/api/biaya` harus accessible dari frontend
- Database koneksi harus sudah setup di `main.py`
- Default value adalah Rp40.000 (pendaftaran) + Rp100.000 (SPP)
- Perubahan biaya hanya mempengaruhi pendaftaran baru
- Untuk mengubah biaya siswa yang sudah terdaftar, update langsung di database

## 📞 Support

Jika ada pertanyaan atau error:
1. Cek browser console (F12 → Console)
2. Cek Network tab untuk response API
3. Cek Flask server logs
4. Verifikasi database connection

---
**Last Updated**: January 2025
**Version**: 1.0.0
