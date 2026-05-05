-- Buat Database
CREATE DATABASE IF NOT EXISTS sekolah_renang_sibahah;
USE sekolah_renang_sibahah;

-- Tabel Pendaftaran Siswa
CREATE TABLE IF NOT EXISTS pendaftaran (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nama VARCHAR(100) NOT NULL,
    usia INT,
    gender VARCHAR(20) NOT NULL,
    ortu VARCHAR(100) NOT NULL,
    wa VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(100),
    kelas VARCHAR(50) NOT NULL,
    jadwal VARCHAR(100) NOT NULL,
    catatan LONGTEXT,
    status_pembayaran VARCHAR(20) DEFAULT 'BELUM_BAYAR',
    metode_pembayaran VARCHAR(50),
    tanggal_daftar TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tanggal_pembayaran DATETIME,
    keterangan TEXT,
    nama_pengirim VARCHAR(100),
    nomor_rekening_pengirim VARCHAR(50),
    catatan_transfer TEXT,
    bukti_transfer LONGBLOB,
    uang_pendaftaran INT DEFAULT 40000,
    uang_spp INT DEFAULT 100000,
    total_pembayaran INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indexing untuk pencarian lebih cepat
CREATE INDEX idx_wa ON pendaftaran(wa);
CREATE INDEX idx_status ON pendaftaran(status_pembayaran);
CREATE INDEX idx_tanggal ON pendaftaran(tanggal_daftar);
