-- ====================================
-- Database: sekolah_renang_sibahah
-- ====================================



-- ====================================
-- Tabel 1: admin_users
-- Untuk login/register admin
-- ====================================
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- Tabel 2: pendaftaran
-- Data siswa yang mendaftar
-- ====================================
CREATE TABLE IF NOT EXISTS pendaftaran (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama VARCHAR(255) NOT NULL,
    usia INT NULL,
    gender VARCHAR(20) NULL,
    ortu VARCHAR(255) NOT NULL,
    wa VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100) NULL,
    kelas VARCHAR(50) NULL,
    jadwal VARCHAR(100) NULL,
    catatan TEXT NULL,
    status_pembayaran VARCHAR(50) DEFAULT 'BELUM_BAYAR' COMMENT 'BELUM_BAYAR atau SUDAH_BAYAR',
    metode_pembayaran VARCHAR(100) NULL,
    tanggal_daftar DATETIME DEFAULT CURRENT_TIMESTAMP,
    tanggal_pembayaran DATETIME NULL,
    keterangan TEXT NULL,
    nama_pengirim VARCHAR(255) NULL,
    nomor_rekening_pengirim VARCHAR(100) NULL,
    catatan_transfer TEXT NULL,
    bukti_transfer LONGTEXT NULL COMMENT 'Base64 encoded file',
    total_biaya DECIMAL(12, 2) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_wa (wa),
    INDEX idx_status_pembayaran (status_pembayaran),
    INDEX idx_tanggal_daftar (tanggal_daftar)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- Tabel 3: biaya_sekolah
-- Konfigurasi biaya pendaftaran dan SPP
-- ====================================
CREATE TABLE IF NOT EXISTS biaya_sekolah (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uang_pendaftaran DECIMAL(12, 2) DEFAULT 40000,
    uang_spp DECIMAL(12, 2) DEFAULT 160000,
    keterangan TEXT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default biaya jika belum ada
INSERT INTO biaya_sekolah (id, uang_pendaftaran, uang_spp) 
VALUES (1, 40000, 160000) 
ON DUPLICATE KEY UPDATE id=id;

-- ====================================
-- Tabel 4: spp_payments
-- Pembayaran SPP per bulan
-- ====================================
CREATE TABLE IF NOT EXISTS spp_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pendaftaran_id INT NULL,
    siswa_id VARCHAR(100) NULL,
    payment_month VARCHAR(20) NULL COMMENT 'Bulan pembayaran (1-12 atau format lain)',
    amount DECIMAL(12, 2) NULL,
    nama_pengirim VARCHAR(255) NULL,
    nomor_rekening_pengirim VARCHAR(100) NULL,
    catatan TEXT NULL,
    bukti_transfer LONGTEXT NULL COMMENT 'Base64 encoded file',
    tanggal_pembayaran DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pendaftaran_id) REFERENCES pendaftaran(id) ON DELETE SET NULL,
    INDEX idx_siswa_id (siswa_id),
    INDEX idx_payment_month (payment_month),
    INDEX idx_tanggal_pembayaran (tanggal_pembayaran)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- Tabel 5: jadwal_latihan
-- Jadwal latihan untuk pendaftaran
-- ====================================
CREATE TABLE IF NOT EXISTS jadwal_latihan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hari VARCHAR(50) NOT NULL,
    jam_mulai VARCHAR(10) NOT NULL,
    jam_selesai VARCHAR(10) NOT NULL,
    kelas VARCHAR(100) NOT NULL,
    jenis VARCHAR(50) NOT NULL COMMENT 'Putra atau Putri',
    instruktur VARCHAR(100) NULL,
    kapasitas INT DEFAULT 15,
    peserta INT DEFAULT 0,
    keterangan TEXT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_jenis (jenis),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- Tabel 6: master_classes (Opsional)
-- Untuk mengelola kelas/jadwal renang
-- ====================================
CREATE TABLE IF NOT EXISTS master_classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama_kelas VARCHAR(100) NOT NULL UNIQUE,
    jadwal VARCHAR(100) NULL,
    deskripsi TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- Insert Data Default (Opsional)
-- ====================================

-- Default admin user (username: admin, password: admin123)
INSERT INTO admin_users (username, password) 
VALUES ('admin', 'admin123') 
ON DUPLICATE KEY UPDATE id=id;

-- Default jadwal latihan
INSERT INTO jadwal_latihan (hari, jam_mulai, jam_selesai, kelas, jenis, instruktur, kapasitas) 
VALUES 
    ('Selasa', '17:00', '18:00', 'Pemula', 'Putra', 'Coach Fikri', 15),
    ('Jumat', '15:00', '16:00', 'Pemula', 'Putra', 'Coach Fikri', 15),
    ('Sabtu', '09:00', '10:00', 'Pemula', 'Putra', 'Coach Fikri', 15),
    ('Sabtu', '15:00', '16:00', 'Lanjutan', 'Putra', 'Coach Fikri', 15),
    ('Selasa', '16:00', '17:00', 'Pemula', 'Putri', 'Coach Fikri', 15),
    ('Jumat', '14:00', '15:00', 'Pemula', 'Putri', 'Coach Fikri', 15),
    ('Sabtu', '08:00', '09:00', 'Pemula', 'Putri', 'Coach Fikri', 15),
    ('Sabtu', '14:00', '15:00', 'Lanjutan', 'Putri', 'Coach Fikri', 15)
ON DUPLICATE KEY UPDATE id=id;

-- Default kelas (sesuaikan dengan data Anda)
INSERT INTO master_classes (nama_kelas, jadwal) 
VALUES 
    ('Kelas A', 'Senin-Rabu 10:00'),
    ('Kelas B', 'Selasa-Kamis 14:00'),
    ('Kelas C', 'Sabtu 09:00')
ON DUPLICATE KEY UPDATE id=id;
