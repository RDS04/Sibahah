-- ========== TABLE UNTUK MANAJEMEN BIAYA ==========

-- Hapus tabel jika sudah ada
DROP TABLE IF EXISTS biaya_sekolah;

-- Buat tabel untuk manajemen biaya
CREATE TABLE biaya_sekolah (
    id INT PRIMARY KEY AUTO_INCREMENT,
    uang_pendaftaran INT NOT NULL DEFAULT 0 COMMENT 'Biaya pendaftaran saat daftar (Rp)',
    uang_spp INT NOT NULL DEFAULT 0 COMMENT 'Biaya SPP per bulan (Rp)',
    tanggal_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    keterangan VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert data default
INSERT INTO biaya_sekolah (id, uang_pendaftaran, uang_spp, keterangan) 
VALUES (1, 40000, 100000, 'Biaya standar sekolah renang');

-- Alter table pendaftaran untuk menambah kolom biaya
ALTER TABLE pendaftaran ADD COLUMN IF NOT EXISTS uang_pendaftaran INT DEFAULT 40000;
ALTER TABLE pendaftaran ADD COLUMN IF NOT EXISTS uang_spp INT DEFAULT 100000;
ALTER TABLE pendaftaran ADD COLUMN IF NOT EXISTS jumlah_bulan INT DEFAULT 1;
ALTER TABLE pendaftaran ADD COLUMN IF NOT EXISTS total_biaya INT DEFAULT 40000;
