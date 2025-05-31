import tkinter as tk
from tkinter import ttk, Canvas, NW, PhotoImage, StringVar, Entry, simpledialog
import tkinter.messagebox as messagebox
from PIL import Image, ImageTk, ImageFilter
import mysql.connector # Import MySQL connector
import os 
import re # Untuk validasi regex NIM
from dotenv import load_dotenv 
# import hashlib # Tidak digunakan lagi karena password teks biasa

# Memuat variabel dari file .env ke environment variables
load_dotenv() 

# Diasumsikan file tombol.py ada di direktori yang sama
from tombol import tbl

# --- Kelas Utama 1: DatabaseService (Enkapsulasi Logika Database dengan MySQL) ---
class DatabaseService:
    """
    Mengenkapsulasi semua interaksi dengan database MySQL.
    Menyediakan metode untuk operasi CRUD pada entitas Asrama, Kamar, dan Penghuni.
    Menggunakan View dan Stored Procedure.
    Otomatis mencoba membuat skema database jika belum ada.
    """
    def __init__(self, host, user, password, database_name, parent_window=None):
        self._host = host
        self._user = user
        self._password = password
        self._database_name = database_name
        self._parent_window = parent_window 
        self._conn = None 
        self._cursor = None 
        self._connect()
        if self._conn: 
            self._initialize_database_schema() 
            self._populate_initial_master_data_if_empty() 

    def _connect(self):
        """Membuat koneksi ke database MySQL."""
        try:
            self._conn = mysql.connector.connect(
                host=self._host, 
                user=self._user, 
                password=self._password 
            )
            self._cursor = self._conn.cursor(dictionary=True) 
            self._cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self._database_name}") 
            self._cursor.execute(f"USE {self._database_name}") 
            self._conn.database = self._database_name
            print(f"Berhasil terhubung ke database MySQL dan menggunakan database '{self._database_name}'.")
        except mysql.connector.Error as err:
            print(f"Kesalahan koneksi database MySQL: {err}")
            if self._parent_window and self._parent_window.winfo_exists():
                messagebox.showerror("Kesalahan Database", f"Tidak dapat terhubung ke MySQL: {err}\n\nPastikan server MySQL berjalan dan detail koneksi benar.", parent=self._parent_window)
            else:
                print("Tidak dapat menampilkan messagebox karena parent window tidak valid atau tidak ada.")
            self._conn = None
            self._cursor = None

    def _close(self):
        """Menutup koneksi database."""
        if self._cursor: 
            self._cursor.close()
        if self._conn and self._conn.is_connected(): 
            self._conn.close()
            print("Koneksi MySQL ditutup.")

    def _execute_single_ddl(self, ddl_statement):
        """Mengeksekusi satu pernyataan DDL dan melakukan commit."""
        if not self._conn or not self._conn.is_connected():
            print(f"Eksekusi DDL dibatalkan, tidak ada koneksi: {ddl_statement[:50]}...")
            return False
        try:
            if "$$" in ddl_statement: 
                statements = ddl_statement.split("$$")
                for stmt_part in statements:
                    stmt_part = stmt_part.strip()
                    if stmt_part.upper().startswith("DELIMITER"): 
                        continue
                    if stmt_part: 
                        self._cursor.execute(stmt_part)
            else:
                self._cursor.execute(ddl_statement)
            
            self._conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Peringatan/Error saat menjalankan DDL: {err}\nDDL: {ddl_statement[:200]}...")
            try:
                if self._conn.in_transaction: self._conn.rollback()
            except: pass
            return False

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False, is_ddl_or_commit_managed_elsewhere=False): 
        """Helper untuk eksekusi kueri dengan error handling."""
        if not self._conn or not self._conn.is_connected(): 
            print("Kesalahan Database: Tidak ada koneksi ke database MySQL.")
            return None if fetch_one or fetch_all else False
        try:
            self._cursor.execute(query, params) 
            if not is_ddl_or_commit_managed_elsewhere and \
               query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                self._conn.commit() 
            if fetch_one:
                return self._cursor.fetchone() 
            if fetch_all:
                return self._cursor.fetchall() 
            return True
        except mysql.connector.Error as err:
            print(f"Kesalahan kueri MySQL: {err}\nKueri: {query}\nParams: {params}")
            if not is_ddl_or_commit_managed_elsewhere: 
                 try:
                    if self._conn.in_transaction:  
                        self._conn.rollback() 
                 except mysql.connector.Error as rb_err:
                    print(f"Kesalahan saat rollback: {rb_err}")
            return None if fetch_one or fetch_all else False

    def _initialize_database_schema(self):
        """Membuat semua tabel, view, trigger, dan stored procedure jika belum ada."""
        if not self._conn or not self._conn.is_connected():
            print("Inisialisasi skema dibatalkan: Tidak ada koneksi database.")
            return

        print("Memulai inisialisasi skema database...")

        tables_ddl = [
            """CREATE TABLE IF NOT EXISTS Asrama (
                asrama_id INTEGER PRIMARY KEY,
                nama_asrama VARCHAR(255) NOT NULL UNIQUE
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS Fakultas (
                fakultas_id INT AUTO_INCREMENT PRIMARY KEY,
                nama_fakultas VARCHAR(255) NOT NULL UNIQUE
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS Kamar (
                kamar_id_internal INTEGER PRIMARY KEY AUTO_INCREMENT,
                nomor_kamar INTEGER NOT NULL,
                asrama_id INTEGER NOT NULL,
                kapasitas INTEGER NOT NULL DEFAULT 2,
                FOREIGN KEY (asrama_id) REFERENCES Asrama(asrama_id) ON DELETE CASCADE,
                UNIQUE (nomor_kamar, asrama_id)
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS PenggunaAplikasi (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS Penghuni (
                nim VARCHAR(50) PRIMARY KEY, nama_penghuni VARCHAR(255) NOT NULL,
                fakultas_id INT NULL DEFAULT NULL, kamar_id_internal INTEGER NOT NULL,
                FOREIGN KEY (kamar_id_internal) REFERENCES Kamar(kamar_id_internal) ON DELETE CASCADE,
                FOREIGN KEY (fakultas_id) REFERENCES Fakultas(fakultas_id) ON DELETE SET NULL ON UPDATE CASCADE
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS AuditLogAktivitasPenghuni (
                log_id INT AUTO_INCREMENT PRIMARY KEY, nim VARCHAR(50),
                nama_penghuni_lama VARCHAR(255) DEFAULT NULL, nama_penghuni_baru VARCHAR(255) DEFAULT NULL,
                fakultas_lama VARCHAR(255) DEFAULT NULL, fakultas_baru VARCHAR(255) DEFAULT NULL,
                kamar_id_internal_lama INT DEFAULT NULL, kamar_id_internal_baru INT DEFAULT NULL,
                nomor_kamar_lama INT DEFAULT NULL, nama_asrama_lama VARCHAR(255) DEFAULT NULL,
                nomor_kamar_baru INT DEFAULT NULL, nama_asrama_baru VARCHAR(255) DEFAULT NULL,
                aksi VARCHAR(10) NOT NULL, waktu_aksi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_aksi VARCHAR(50) DEFAULT NULL, keterangan_tambahan TEXT DEFAULT NULL
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS AuditLogAktivitasAsrama (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                asrama_id_aksi INT, 
                nama_asrama_lama VARCHAR(255) DEFAULT NULL,
                nama_asrama_baru VARCHAR(255) DEFAULT NULL,
                aksi VARCHAR(10) NOT NULL,
                waktu_aksi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_aksi VARCHAR(50) DEFAULT NULL,
                keterangan_tambahan TEXT DEFAULT NULL
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS AuditLogAktivitasKamar (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                kamar_id_internal_aksi INT, 
                nomor_kamar_lama INT DEFAULT NULL,
                nomor_kamar_baru INT DEFAULT NULL,
                asrama_id_lama INT DEFAULT NULL, 
                asrama_id_baru INT DEFAULT NULL, 
                nama_asrama_lama VARCHAR(255) DEFAULT NULL,
                nama_asrama_baru VARCHAR(255) DEFAULT NULL,
                kapasitas_lama INT DEFAULT NULL,
                kapasitas_baru INT DEFAULT NULL,
                aksi VARCHAR(10) NOT NULL,
                waktu_aksi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_aksi VARCHAR(50) DEFAULT NULL,
                keterangan_tambahan TEXT DEFAULT NULL
            ) ENGINE=InnoDB;"""
        ]
        for ddl in tables_ddl: self._execute_single_ddl(ddl)
        print("Tabel utama telah diperiksa/dibuat.")

        views_ddl = [
            """CREATE OR REPLACE VIEW vw_DetailKamarPenghuni AS
            SELECT K.nomor_kamar, A.nama_asrama, K.asrama_id, K.kapasitas,
            (SELECT COUNT(*) FROM Penghuni P WHERE P.kamar_id_internal = K.kamar_id_internal) AS jumlah_penghuni_sekarang,
            K.kamar_id_internal FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id;""",
            """CREATE OR REPLACE VIEW vw_DaftarPenghuniLengkap AS
            SELECT P.nim, P.nama_penghuni, F.nama_fakultas AS fakultas, K.nomor_kamar, A.nama_asrama, 
            K.asrama_id AS id_asrama_penghuni, A.asrama_id AS id_asrama_kamar, K.kamar_id_internal, P.fakultas_id
            FROM Penghuni P JOIN Kamar K ON P.kamar_id_internal = K.kamar_id_internal
            JOIN Asrama A ON K.asrama_id = A.asrama_id LEFT JOIN Fakultas F ON P.fakultas_id = F.fakultas_id;"""
        ]
        for ddl in views_ddl: self._execute_single_ddl(ddl)
        print("View telah diperiksa/dibuat.")

        # Triggers for Penghuni
        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogInsertPenghuni")
        self._execute_single_ddl("""
        CREATE TRIGGER trg_LogInsertPenghuni AFTER INSERT ON Penghuni FOR EACH ROW
        BEGIN
            DECLARE v_nk INT; DECLARE v_na VARCHAR(255); DECLARE v_nf VARCHAR(255) DEFAULT NULL; DECLARE v_ua VARCHAR(50) DEFAULT NULL;
            SELECT K.nomor_kamar, A.nama_asrama INTO v_nk, v_na FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = NEW.kamar_id_internal;
            IF NEW.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nf FROM Fakultas WHERE fakultas_id = NEW.fakultas_id; END IF;
            SET v_ua = @session_user_aksi;
            INSERT INTO AuditLogAktivitasPenghuni (nim, nama_penghuni_baru, fakultas_baru, kamar_id_internal_baru, nomor_kamar_baru, nama_asrama_baru, aksi, user_aksi, keterangan_tambahan)
            VALUES (NEW.nim, NEW.nama_penghuni, v_nf, NEW.kamar_id_internal, v_nk, v_na, 'INSERT', v_ua, CONCAT('Penghuni baru ditambahkan ke kamar ', v_nk, ' Asrama ', v_na));
        END""")
        
        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogUpdatePenghuni")
        self._execute_single_ddl("""
        CREATE TRIGGER trg_LogUpdatePenghuni AFTER UPDATE ON Penghuni FOR EACH ROW
        BEGIN
            DECLARE v_nkl INT DEFAULT NULL; DECLARE v_nal VARCHAR(255) DEFAULT NULL; DECLARE v_nfl VARCHAR(255) DEFAULT NULL;
            DECLARE v_nkb INT DEFAULT NULL; DECLARE v_nab VARCHAR(255) DEFAULT NULL; DECLARE v_nfb VARCHAR(255) DEFAULT NULL;
            DECLARE v_ua VARCHAR(50) DEFAULT NULL; DECLARE v_ket TEXT DEFAULT 'Data penghuni diubah.';
            IF OLD.kamar_id_internal IS NOT NULL THEN SELECT K.nomor_kamar, A.nama_asrama INTO v_nkl, v_nal FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = OLD.kamar_id_internal; END IF;
            IF OLD.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nfl FROM Fakultas WHERE fakultas_id = OLD.fakultas_id; END IF;
            IF NEW.kamar_id_internal IS NOT NULL THEN SELECT K.nomor_kamar, A.nama_asrama INTO v_nkb, v_nab FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = NEW.kamar_id_internal; END IF;
            IF NEW.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nfb FROM Fakultas WHERE fakultas_id = NEW.fakultas_id; END IF;
            SET v_ua = @session_user_aksi;
            IF OLD.kamar_id_internal != NEW.kamar_id_internal THEN SET v_ket = CONCAT('Penghuni pindah dari kamar ', IFNULL(v_nkl,'N/A'), ' Asrama ', IFNULL(v_nal,'N/A'), ' ke kamar ', IFNULL(v_nkb,'N/A'), ' Asrama ', IFNULL(v_nab,'N/A'), '.');
            ELSEIF OLD.fakultas_id != NEW.fakultas_id OR (OLD.fakultas_id IS NULL AND NEW.fakultas_id IS NOT NULL) OR (OLD.fakultas_id IS NOT NULL AND NEW.fakultas_id IS NULL) THEN SET v_ket = CONCAT('Fakultas diubah dari ', IFNULL(v_nfl,'N/A'), ' menjadi ', IFNULL(v_nfb,'N/A'), '.');
            ELSEIF OLD.nama_penghuni != NEW.nama_penghuni THEN SET v_ket = CONCAT('Nama diubah dari ', OLD.nama_penghuni, ' menjadi ', NEW.nama_penghuni, '.'); END IF;
            INSERT INTO AuditLogAktivitasPenghuni (nim, nama_penghuni_lama, nama_penghuni_baru, fakultas_lama, fakultas_baru, kamar_id_internal_lama, kamar_id_internal_baru, nomor_kamar_lama, nama_asrama_lama, nomor_kamar_baru, nama_asrama_baru, aksi, user_aksi, keterangan_tambahan)
            VALUES (OLD.nim, OLD.nama_penghuni, NEW.nama_penghuni, v_nfl, v_nfb, OLD.kamar_id_internal, NEW.kamar_id_internal, v_nkl, v_nal, v_nkb, v_nab, 'UPDATE', v_ua, v_ket);
        END""")

        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogDeletePenghuni")
        self._execute_single_ddl("""
        CREATE TRIGGER trg_LogDeletePenghuni AFTER DELETE ON Penghuni FOR EACH ROW
        BEGIN
            DECLARE v_nk INT DEFAULT NULL; DECLARE v_na VARCHAR(255) DEFAULT NULL; DECLARE v_nf VARCHAR(255) DEFAULT NULL; DECLARE v_ua VARCHAR(50) DEFAULT NULL;
            IF OLD.kamar_id_internal IS NOT NULL THEN SELECT K.nomor_kamar, A.nama_asrama INTO v_nk, v_na FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = OLD.kamar_id_internal; END IF;
            IF OLD.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nf FROM Fakultas WHERE fakultas_id = OLD.fakultas_id; END IF;
            SET v_ua = @session_user_aksi;
            INSERT INTO AuditLogAktivitasPenghuni (nim, nama_penghuni_lama, fakultas_lama, kamar_id_internal_lama, nomor_kamar_lama, nama_asrama_lama, aksi, user_aksi, keterangan_tambahan)
            VALUES (OLD.nim, OLD.nama_penghuni, v_nf, OLD.kamar_id_internal, v_nk, v_na, 'DELETE', v_ua, CONCAT('Penghuni dihapus dari kamar ', IFNULL(v_nk, 'N/A'), ' Asrama ', IFNULL(v_na, 'N/A')));
        END""")
        
        # Triggers for Asrama
        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogInsertAsrama")
        self._execute_single_ddl("""
        CREATE TRIGGER trg_LogInsertAsrama AFTER INSERT ON Asrama FOR EACH ROW
        BEGIN
            DECLARE v_user_aksi VARCHAR(50) DEFAULT NULL; SET v_user_aksi = @session_user_aksi;
            INSERT INTO AuditLogAktivitasAsrama (asrama_id_aksi, nama_asrama_baru, aksi, user_aksi, keterangan_tambahan)
            VALUES (NEW.asrama_id, NEW.nama_asrama, 'INSERT', v_user_aksi, CONCAT('Asrama baru: ID ', NEW.asrama_id, ', Nama: ', NEW.nama_asrama));
        END""")

        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogUpdateAsrama")
        self._execute_single_ddl("""
        CREATE TRIGGER trg_LogUpdateAsrama AFTER UPDATE ON Asrama FOR EACH ROW
        BEGIN
            DECLARE v_user_aksi VARCHAR(50) DEFAULT NULL; DECLARE v_keterangan TEXT;
            SET v_user_aksi = @session_user_aksi; SET v_keterangan = CONCAT('Asrama ID ', OLD.asrama_id, ' diubah. ');
            IF OLD.nama_asrama != NEW.nama_asrama THEN SET v_keterangan = CONCAT(v_keterangan, 'Nama dari ''', OLD.nama_asrama, ''' menjadi ''', NEW.nama_asrama, '''.'); END IF;
            INSERT INTO AuditLogAktivitasAsrama (asrama_id_aksi, nama_asrama_lama, nama_asrama_baru, aksi, user_aksi, keterangan_tambahan)
            VALUES (OLD.asrama_id, OLD.nama_asrama, NEW.nama_asrama, 'UPDATE', v_user_aksi, v_keterangan);
        END""")

        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogDeleteAsrama")
        self._execute_single_ddl("""
        CREATE TRIGGER trg_LogDeleteAsrama AFTER DELETE ON Asrama FOR EACH ROW
        BEGIN
            DECLARE v_user_aksi VARCHAR(50) DEFAULT NULL; SET v_user_aksi = @session_user_aksi;
            INSERT INTO AuditLogAktivitasAsrama (asrama_id_aksi, nama_asrama_lama, aksi, user_aksi, keterangan_tambahan)
            VALUES (OLD.asrama_id, OLD.nama_asrama, 'DELETE', v_user_aksi, CONCAT('Asrama dihapus: ID ', OLD.asrama_id, ', Nama: ', OLD.nama_asrama));
        END""")

        # Triggers for Kamar
        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogInsertKamar")
        self._execute_single_ddl("""
        CREATE TRIGGER trg_LogInsertKamar AFTER INSERT ON Kamar FOR EACH ROW
        BEGIN
            DECLARE v_user_aksi VARCHAR(50) DEFAULT NULL; DECLARE v_nama_asrama VARCHAR(255);
            SET v_user_aksi = @session_user_aksi; SELECT nama_asrama INTO v_nama_asrama FROM Asrama WHERE asrama_id = NEW.asrama_id;
            INSERT INTO AuditLogAktivitasKamar (kamar_id_internal_aksi, nomor_kamar_baru, asrama_id_baru, nama_asrama_baru, kapasitas_baru, aksi, user_aksi, keterangan_tambahan)
            VALUES (NEW.kamar_id_internal, NEW.nomor_kamar, NEW.asrama_id, v_nama_asrama, NEW.kapasitas, 'INSERT', v_user_aksi, 
                    CONCAT('Kamar baru: No ', NEW.nomor_kamar, ', Asrama: ', v_nama_asrama, ', Kap: ', NEW.kapasitas));
        END""")

        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogUpdateKamar")
        self._execute_single_ddl("""
        CREATE TRIGGER trg_LogUpdateKamar AFTER UPDATE ON Kamar FOR EACH ROW
        BEGIN
            DECLARE v_user_aksi VARCHAR(50) DEFAULT NULL; DECLARE v_na_lama VARCHAR(255); DECLARE v_na_baru VARCHAR(255); DECLARE v_ket TEXT;
            SET v_user_aksi = @session_user_aksi;
            SELECT nama_asrama INTO v_na_lama FROM Asrama WHERE asrama_id = OLD.asrama_id;
            SELECT nama_asrama INTO v_na_baru FROM Asrama WHERE asrama_id = NEW.asrama_id;
            SET v_ket = CONCAT('Kamar ID Int ', OLD.kamar_id_internal, ' diubah. ');
            IF OLD.nomor_kamar != NEW.nomor_kamar THEN SET v_ket = CONCAT(v_ket, 'No: ', OLD.nomor_kamar, '->', NEW.nomor_kamar, '. '); END IF;
            IF OLD.kapasitas != NEW.kapasitas THEN SET v_ket = CONCAT(v_ket, 'Kap: ', OLD.kapasitas, '->', NEW.kapasitas, '. '); END IF;
            IF OLD.asrama_id != NEW.asrama_id THEN SET v_ket = CONCAT(v_ket, 'Asrama: ', v_na_lama, '->', v_na_baru, '. '); END IF;
            INSERT INTO AuditLogAktivitasKamar (kamar_id_internal_aksi, nomor_kamar_lama, nomor_kamar_baru, asrama_id_lama, asrama_id_baru, nama_asrama_lama, nama_asrama_baru, kapasitas_lama, kapasitas_baru, aksi, user_aksi, keterangan_tambahan)
            VALUES (OLD.kamar_id_internal, OLD.nomor_kamar, NEW.nomor_kamar, OLD.asrama_id, NEW.asrama_id, v_na_lama, v_na_baru, OLD.kapasitas, NEW.kapasitas, 'UPDATE', v_user_aksi, v_ket);
        END""")

        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogDeleteKamar")
        self._execute_single_ddl("""
        CREATE TRIGGER trg_LogDeleteKamar AFTER DELETE ON Kamar FOR EACH ROW
        BEGIN
            DECLARE v_user_aksi VARCHAR(50) DEFAULT NULL; DECLARE v_nama_asrama VARCHAR(255);
            SET v_user_aksi = @session_user_aksi; SELECT nama_asrama INTO v_nama_asrama FROM Asrama WHERE asrama_id = OLD.asrama_id;
            INSERT INTO AuditLogAktivitasKamar (kamar_id_internal_aksi, nomor_kamar_lama, asrama_id_lama, nama_asrama_lama, kapasitas_lama, aksi, user_aksi, keterangan_tambahan)
            VALUES (OLD.kamar_id_internal, OLD.nomor_kamar, OLD.asrama_id, v_nama_asrama, OLD.kapasitas, 'DELETE', v_user_aksi, 
                    CONCAT('Kamar dihapus: No ', OLD.nomor_kamar, ', Asrama: ', v_nama_asrama));
        END""")
        print("Trigger telah diperiksa/dibuat.")

        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_TambahAsrama")
        self._execute_single_ddl("""
        CREATE PROCEDURE sp_TambahAsrama (
            IN p_asrama_id INT,
            IN p_nama_asrama VARCHAR(255)
        )
        BEGIN
            DECLARE v_status_code INT;
            DECLARE v_status_message VARCHAR(255);
            SET v_status_code = 1; 
            SET v_status_message = 'Gagal: Terjadi kesalahan tidak diketahui.';
            IF p_asrama_id IS NULL OR p_nama_asrama IS NULL OR p_nama_asrama = '' THEN
                SET v_status_code = 1;
                SET v_status_message = 'Gagal: ID Asrama dan Nama Asrama tidak boleh kosong.';
            ELSEIF EXISTS (SELECT 1 FROM Asrama WHERE asrama_id = p_asrama_id) THEN
                SET v_status_code = 2;
                SET v_status_message = CONCAT('Gagal: Asrama dengan ID ', p_asrama_id, ' sudah ada.');
            ELSEIF EXISTS (SELECT 1 FROM Asrama WHERE nama_asrama = p_nama_asrama) THEN
                SET v_status_code = 3;
                SET v_status_message = CONCAT('Gagal: Nama Asrama ''', p_nama_asrama, ''' sudah digunakan.');
            ELSE
                SET @session_user_aksi = USER(); 
                INSERT INTO Asrama (asrama_id, nama_asrama) VALUES (p_asrama_id, p_nama_asrama);
                SET v_status_code = 0;
                SET v_status_message = 'Sukses: Asrama berhasil ditambahkan.';
                SET @session_user_aksi = NULL;
            END IF;
            SELECT v_status_code AS p_status_code, v_status_message AS p_status_message;
        END""")

        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_UpdateAsrama")
        self._execute_single_ddl("""
        CREATE PROCEDURE sp_UpdateAsrama (
            IN p_asrama_id INT,
            IN p_nama_asrama_baru VARCHAR(255)
        )
        BEGIN
            DECLARE v_status_code INT; DECLARE v_status_message VARCHAR(255);
            DECLARE v_asrama_exists INT DEFAULT 0; DECLARE v_nama_conflict INT DEFAULT 0;
            SET v_status_code = 1; SET v_status_message = 'Gagal: Terjadi kesalahan tidak diketahui.';
            IF p_asrama_id IS NULL OR p_nama_asrama_baru IS NULL OR p_nama_asrama_baru = '' THEN SET v_status_code = 1; SET v_status_message = 'Gagal: ID Asrama dan Nama Asrama baru tidak boleh kosong.';
            ELSE
                SELECT COUNT(*) INTO v_asrama_exists FROM Asrama WHERE asrama_id = p_asrama_id;
                IF v_asrama_exists = 0 THEN SET v_status_code = 2; SET v_status_message = CONCAT('Gagal: Asrama dengan ID ', p_asrama_id, ' tidak ditemukan.');
                ELSE
                    SELECT COUNT(*) INTO v_nama_conflict FROM Asrama WHERE nama_asrama = p_nama_asrama_baru AND asrama_id != p_asrama_id;
                    IF v_nama_conflict > 0 THEN SET v_status_code = 3; SET v_status_message = CONCAT('Gagal: Nama Asrama ''', p_nama_asrama_baru, ''' sudah digunakan oleh asrama lain.');
                    ELSE
                        SET @session_user_aksi = USER();
                        UPDATE Asrama SET nama_asrama = p_nama_asrama_baru WHERE asrama_id = p_asrama_id;
                        IF ROW_COUNT() > 0 THEN SET v_status_code = 0; SET v_status_message = 'Sukses: Nama asrama berhasil diubah.';
                        ELSE SET v_status_code = 0; SET v_status_message = 'Info: Tidak ada perubahan pada nama asrama (nama baru sama dengan nama lama).';
                        END IF;
                        SET @session_user_aksi = NULL;
                    END IF;
                END IF;
            END IF;
            SELECT v_status_code AS p_status_code, v_status_message AS p_status_message;
        END""")

        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_HapusAsrama")
        self._execute_single_ddl("""
        CREATE PROCEDURE sp_HapusAsrama (
            IN p_asrama_id INT
        )
        BEGIN
            DECLARE v_status_code INT; DECLARE v_status_message VARCHAR(255);
            DECLARE v_kamar_count INT DEFAULT 0;
            SET v_status_code = 1; SET v_status_message = 'Gagal: Terjadi kesalahan tidak diketahui.';
            IF p_asrama_id IS NULL THEN SET v_status_code = 1; SET v_status_message = 'Gagal: ID Asrama tidak boleh kosong.';
            ELSE
                SELECT COUNT(*) INTO v_kamar_count FROM Kamar WHERE asrama_id = p_asrama_id;
                IF v_kamar_count > 0 THEN SET v_status_code = 2; SET v_status_message = 'Gagal: Asrama tidak dapat dihapus karena masih memiliki kamar. Hapus semua kamar di asrama ini terlebih dahulu.';
                ELSE
                    SET @session_user_aksi = USER();
                    DELETE FROM Asrama WHERE asrama_id = p_asrama_id;
                    IF ROW_COUNT() > 0 THEN SET v_status_code = 0; SET v_status_message = 'Sukses: Asrama berhasil dihapus.';
                    ELSE SET v_status_code = 3; SET v_status_message = 'Gagal: Asrama dengan ID tersebut tidak ditemukan.';
                    END IF;
                    SET @session_user_aksi = NULL;
                END IF;
            END IF;
            SELECT v_status_code AS p_status_code, v_status_message AS p_status_message;
        END""")
        
        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_TambahKamar")
        self._execute_single_ddl("""
        CREATE PROCEDURE sp_TambahKamar (
            IN p_nomor_kamar INT, IN p_asrama_id INT, IN p_kapasitas INT
        )
        BEGIN
            DECLARE v_status_code INT; DECLARE v_status_message VARCHAR(255);
            SET v_status_code = 1; SET v_status_message = 'Gagal: Terjadi kesalahan tidak diketahui.';
            IF p_nomor_kamar IS NULL OR p_asrama_id IS NULL OR p_kapasitas IS NULL OR p_kapasitas <= 0 THEN SET v_status_code = 1; SET v_status_message = 'Gagal: Nomor kamar, ID asrama, dan kapasitas (harus > 0) tidak boleh kosong.';
            ELSEIF NOT EXISTS (SELECT 1 FROM Asrama WHERE asrama_id = p_asrama_id) THEN SET v_status_code = 2; SET v_status_message = 'Gagal: Asrama dengan ID tersebut tidak ditemukan.';
            ELSEIF EXISTS (SELECT 1 FROM Kamar WHERE nomor_kamar = p_nomor_kamar AND asrama_id = p_asrama_id) THEN SET v_status_code = 3; SET v_status_message = CONCAT('Gagal: Kamar nomor ', p_nomor_kamar, ' sudah ada di asrama ini.');
            ELSE 
                SET @session_user_aksi = USER();
                INSERT INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES (p_nomor_kamar, p_asrama_id, p_kapasitas); 
                SET v_status_code = 0; SET v_status_message = 'Sukses: Kamar berhasil ditambahkan.';
                SET @session_user_aksi = NULL;
            END IF;
            SELECT v_status_code AS p_status_code, v_status_message AS p_status_message;
        END""")

        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_UpdateKamar")
        self._execute_single_ddl("""
        CREATE PROCEDURE sp_UpdateKamar (
            IN p_kamar_id_internal INT, IN p_nomor_kamar_baru INT, IN p_kapasitas_baru INT, IN p_asrama_id_konteks INT
        )
        BEGIN
            DECLARE v_status_code INT; DECLARE v_status_message VARCHAR(255);
            DECLARE v_kamar_exists INT DEFAULT 0; DECLARE v_nomor_conflict INT DEFAULT 0;
            SET v_status_code = 1; SET v_status_message = 'Gagal: Terjadi kesalahan tidak diketahui.';
            IF p_kamar_id_internal IS NULL OR p_nomor_kamar_baru IS NULL OR p_kapasitas_baru IS NULL OR p_kapasitas_baru <= 0 THEN SET v_status_code = 1; SET v_status_message = 'Gagal: ID Kamar, Nomor Kamar baru, dan Kapasitas baru (harus > 0) tidak boleh kosong.';
            ELSE
                SELECT COUNT(*) INTO v_kamar_exists FROM Kamar WHERE kamar_id_internal = p_kamar_id_internal;
                IF v_kamar_exists = 0 THEN SET v_status_code = 2; SET v_status_message = 'Gagal: Kamar dengan ID tersebut tidak ditemukan.';
                ELSE
                    SELECT COUNT(*) INTO v_nomor_conflict FROM Kamar WHERE nomor_kamar = p_nomor_kamar_baru AND asrama_id = p_asrama_id_konteks AND kamar_id_internal != p_kamar_id_internal;
                    IF v_nomor_conflict > 0 THEN SET v_status_code = 3; SET v_status_message = CONCAT('Gagal: Nomor kamar ', p_nomor_kamar_baru, ' sudah ada di asrama ini.');
                    ELSE
                        SET @session_user_aksi = USER();
                        UPDATE Kamar SET nomor_kamar = p_nomor_kamar_baru, kapasitas = p_kapasitas_baru WHERE kamar_id_internal = p_kamar_id_internal;
                        IF ROW_COUNT() > 0 THEN SET v_status_code = 0; SET v_status_message = 'Sukses: Detail kamar berhasil diubah.';
                        ELSE SET v_status_code = 0; SET v_status_message = 'Info: Tidak ada perubahan pada detail kamar.';
                        END IF;
                        SET @session_user_aksi = NULL;
                    END IF;
                END IF;
            END IF;
            SELECT v_status_code AS p_status_code, v_status_message AS p_status_message;
        END""")

        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_HapusKamar")
        self._execute_single_ddl("""
        CREATE PROCEDURE sp_HapusKamar (
            IN p_kamar_id_internal INT
        )
        BEGIN
            DECLARE v_status_code INT; DECLARE v_status_message VARCHAR(255);
            DECLARE v_penghuni_count INT DEFAULT 0;
            SET v_status_code = 1; SET v_status_message = 'Gagal: Terjadi kesalahan tidak diketahui.';
            IF p_kamar_id_internal IS NULL THEN SET v_status_code = 1; SET v_status_message = 'Gagal: ID Kamar tidak boleh kosong.';
            ELSE
                SELECT COUNT(*) INTO v_penghuni_count FROM Penghuni WHERE kamar_id_internal = p_kamar_id_internal;
                IF v_penghuni_count > 0 THEN SET v_status_code = 2; SET v_status_message = 'Gagal: Kamar tidak dapat dihapus karena masih memiliki penghuni. Hapus semua penghuni di kamar ini terlebih dahulu.';
                ELSE
                    SET @session_user_aksi = USER();
                    DELETE FROM Kamar WHERE kamar_id_internal = p_kamar_id_internal;
                    IF ROW_COUNT() > 0 THEN SET v_status_code = 0; SET v_status_message = 'Sukses: Kamar berhasil dihapus.';
                    ELSE SET v_status_code = 3; SET v_status_message = 'Gagal: Kamar dengan ID tersebut tidak ditemukan.';
                    END IF;
                    SET @session_user_aksi = NULL;
                END IF;
            END IF;
            SELECT v_status_code AS p_status_code, v_status_message AS p_status_message;
        END""")

        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_TambahPenghuni")
        self._execute_single_ddl("""
        CREATE PROCEDURE sp_TambahPenghuni (
            IN p_nim VARCHAR(50), IN p_nama_penghuni VARCHAR(255), IN p_nama_fakultas_input VARCHAR(255), 
            IN p_nomor_kamar INT, IN p_asrama_id INT, IN p_user_aksi VARCHAR(50)
        )
        BEGIN
            DECLARE v_k_id_int INT; DECLARE v_kap_kmr INT; DECLARE v_jml_p_skr INT; DECLARE v_fak_id INT DEFAULT NULL;
            DECLARE v_status_code INT; DECLARE v_status_message VARCHAR(255);
            SET v_status_code = 4; SET v_status_message = 'Terjadi kesalahan tidak diketahui.';
            SET @session_user_aksi = p_user_aksi; 
            IF p_nim IS NULL OR p_nim = '' OR NOT (p_nim REGEXP '^[0-9]+$') THEN SET v_status_code = 5; SET v_status_message = 'Gagal: NIM tidak valid (harus berupa angka dan tidak boleh kosong).';
            ELSE
                IF p_nama_fakultas_input IS NOT NULL AND p_nama_fakultas_input != '' THEN
                    SELECT fakultas_id INTO v_fak_id FROM Fakultas WHERE nama_fakultas = p_nama_fakultas_input;
                    IF v_fak_id IS NULL THEN INSERT INTO Fakultas (nama_fakultas) VALUES (p_nama_fakultas_input); SET v_fak_id = LAST_INSERT_ID(); END IF;
                END IF;
                SELECT kamar_id_internal INTO v_k_id_int FROM Kamar WHERE nomor_kamar = p_nomor_kamar AND asrama_id = p_asrama_id;
                IF v_k_id_int IS NULL THEN SET v_status_code = 1; SET v_status_message = 'Gagal: Kamar tidak ditemukan.';
                ELSE
                    SELECT kapasitas INTO v_kap_kmr FROM Kamar WHERE kamar_id_internal = v_k_id_int;
                    SELECT COUNT(*) INTO v_jml_p_skr FROM Penghuni WHERE kamar_id_internal = v_k_id_int;
                    IF v_jml_p_skr >= v_kap_kmr THEN SET v_status_code = 2; SET v_status_message = 'Gagal: Kamar sudah penuh.';
                    ELSE
                        IF EXISTS (SELECT 1 FROM Penghuni WHERE nim = p_nim) THEN SET v_status_code = 3; SET v_status_message = CONCAT('Gagal: NIM ', p_nim, ' sudah terdaftar.');
                        ELSE INSERT INTO Penghuni (nim, nama_penghuni, fakultas_id, kamar_id_internal) VALUES (p_nim, p_nama_penghuni, v_fak_id, v_k_id_int); SET v_status_code = 0; SET v_status_message = 'Sukses: Penghuni berhasil ditambahkan.';
                        END IF;
                    END IF;
                END IF;
            END IF;
            SET @session_user_aksi = NULL; 
            SELECT v_status_code AS p_status_code, v_status_message AS p_status_message;
        END""")
        
        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_PindahKamarPenghuni")
        self._execute_single_ddl("""
        CREATE PROCEDURE sp_PindahKamarPenghuni (
            IN p_nim VARCHAR(50), IN p_nomor_kamar_baru INT, IN p_asrama_id_baru INT, IN p_user_aksi VARCHAR(50)
        )
        BEGIN
            DECLARE v_k_id_lama INT; DECLARE v_k_id_baru INT; DECLARE v_kap_k_baru INT; DECLARE v_jml_p_k_baru INT;
            DECLARE v_p_exists INT DEFAULT 0;
            DECLARE v_status_code INT; DECLARE v_status_message VARCHAR(255);
            SET v_status_code = 4; SET v_status_message = 'Terjadi kesalahan tidak diketahui.';
            SET @session_user_aksi = p_user_aksi;
            IF p_nim IS NULL OR p_nim = '' OR NOT (p_nim REGEXP '^[0-9]+$') THEN SET v_status_code = 5; SET v_status_message = 'Gagal: NIM tidak valid (harus berupa angka dan tidak boleh kosong).';
            ELSE
                SELECT COUNT(*), kamar_id_internal INTO v_p_exists, v_k_id_lama FROM Penghuni WHERE nim = p_nim;
                IF v_p_exists = 0 THEN SET v_status_code = 1; SET v_status_message = 'Gagal: Penghuni dengan NIM tersebut tidak ditemukan.';
                ELSE
                    SELECT kamar_id_internal INTO v_k_id_baru FROM Kamar WHERE nomor_kamar = p_nomor_kamar_baru AND asrama_id = p_asrama_id_baru;
                    IF v_k_id_baru IS NULL THEN SET v_status_code = 2; SET v_status_message = 'Gagal: Kamar tujuan tidak ditemukan.';
                    ELSE
                        IF v_k_id_lama = v_k_id_baru THEN SET v_status_code = 0; SET v_status_message = 'Info: Penghuni sudah berada di kamar tujuan.';
                        ELSE
                            SELECT kapasitas INTO v_kap_k_baru FROM Kamar WHERE kamar_id_internal = v_k_id_baru;
                            SELECT COUNT(*) INTO v_jml_p_k_baru FROM Penghuni WHERE kamar_id_internal = v_k_id_baru;
                            IF v_jml_p_k_baru >= v_kap_k_baru THEN SET v_status_code = 3; SET v_status_message = 'Gagal: Kamar tujuan sudah penuh.';
                            ELSE UPDATE Penghuni SET kamar_id_internal = v_k_id_baru WHERE nim = p_nim; SET v_status_code = 0; SET v_status_message = 'Sukses: Penghuni berhasil dipindahkan.';
                            END IF;
                        END IF;
                    END IF;
                END IF;
            END IF;
            SET @session_user_aksi = NULL;
            SELECT v_status_code AS p_status_code, v_status_message AS p_status_message;
        END""")
        
        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_RegistrasiPengguna")
        self._execute_single_ddl("""
        CREATE PROCEDURE sp_RegistrasiPengguna (
            IN p_username VARCHAR(50), 
            IN p_password_text VARCHAR(255) 
        )
        BEGIN
            DECLARE v_user_exists INT DEFAULT 0;
            DECLARE v_status_code INT; 
            DECLARE v_status_message VARCHAR(255);
            SET v_status_code = 2; 
            SET v_status_message = 'Gagal melakukan registrasi.';
            IF p_username IS NULL OR p_username = '' OR p_password_text IS NULL OR p_password_text = '' THEN 
                SET v_status_code = 1; 
                SET v_status_message = 'Username dan password tidak boleh kosong.';
            ELSE
                SELECT COUNT(*) INTO v_user_exists FROM PenggunaAplikasi WHERE username = p_username;
                IF v_user_exists > 0 THEN 
                    SET v_status_code = 2; 
                    SET v_status_message = 'Username sudah terdaftar.';
                ELSE 
                    INSERT INTO PenggunaAplikasi (username, password_hash) VALUES (p_username, p_password_text); 
                    SET v_status_code = 0; 
                    SET v_status_message = 'Registrasi berhasil.';
                END IF;
            END IF;
            SELECT v_status_code AS p_status_code, v_status_message AS p_status_message; 
        END""")

        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_LoginPengguna")
        self._execute_single_ddl("""
        CREATE PROCEDURE sp_LoginPengguna (
            IN p_username VARCHAR(50), 
            IN p_input_password_text VARCHAR(255) 
        )
        BEGIN
            DECLARE v_stored_password_text VARCHAR(255) DEFAULT ''; 
            DECLARE v_temp_user_id INT DEFAULT NULL;
            DECLARE v_status_code INT; 
            DECLARE v_status_message VARCHAR(255);
            DECLARE v_logged_in_username VARCHAR(50) DEFAULT NULL;

            SET v_status_code = 3; 
            SET v_status_message = 'Login gagal. Periksa username dan password.'; 
            
            IF p_username IS NULL OR p_username = '' OR p_input_password_text IS NULL OR p_input_password_text = '' THEN 
                SET v_status_code = 1; 
                SET v_status_message = 'Username dan password tidak boleh kosong.';
            ELSE
                SELECT id, username, password_hash INTO v_temp_user_id, v_logged_in_username, v_stored_password_text 
                FROM PenggunaAplikasi WHERE username = p_username;
                
                IF v_temp_user_id IS NULL THEN 
                    SET v_status_code = 2; 
                    SET v_status_message = 'Username tidak ditemukan.'; 
                    SET v_logged_in_username = NULL; 
                ELSE
                    IF v_stored_password_text = p_input_password_text THEN 
                        SET v_status_code = 0; 
                        SET v_status_message = 'Login berhasil.'; 
                    ELSE 
                        SET v_status_code = 3; 
                        SET v_status_message = 'Password salah.'; 
                        SET v_temp_user_id = NULL; 
                        SET v_logged_in_username = NULL;
                    END IF;
                END IF;
            END IF;
            SELECT v_status_code AS p_status_code, v_status_message AS p_status_message, v_temp_user_id AS p_user_id, v_logged_in_username AS p_logged_in_username; 
        END""")
        print("Stored Procedures telah diperiksa/dibuat.")

        print("Inisialisasi skema database selesai.")

    def _populate_initial_master_data_if_empty(self):
        """Mengisi data master awal untuk Asrama dan Fakultas jika tabel kosong."""
        if not self._conn or not self._conn.is_connected(): return

        try:
            self._cursor.execute("SELECT COUNT(*) as count FROM Asrama")
            if (self._cursor.fetchone() or {}).get('count', 0) == 0:
                asramas_data = [
                    (1, "Aster"), (2, "Soka"), (3, "Tulip"), (4, "Edelweiss"),
                    (5, "Lily"), (6, "Dahlia"), (7, "Melati"), (8, "Anyelir")
                ]
                for asrama_id_val, nama in asramas_data:
                    self._execute_query("INSERT INTO Asrama (asrama_id, nama_asrama) VALUES (%s, %s)", (asrama_id_val, nama), is_ddl_or_commit_managed_elsewhere=True)
                self._conn.commit()
                print("Data awal Asrama dimasukkan.")

            self._cursor.execute("SELECT COUNT(*) as count FROM Fakultas")
            if (self._cursor.fetchone() or {}).get('count', 0) == 0:
                fakultas_data = [
                    ('Teknik'), ('Ekonomi dan Bisnis'), ('Ilmu Sosial dan Ilmu Politik'),
                    ('Kedokteran'), ('Ilmu Budaya'), ('MIPA'), ('Ilmu Komputer'),
                    ('Ilmu Keolahragaan'), ('Vokasi'), ('Ilmu Pendidikan')
                ]
                for nama_fak in fakultas_data:
                    self._execute_query("INSERT INTO Fakultas (nama_fakultas) VALUES (%s)", (nama_fak,), is_ddl_or_commit_managed_elsewhere=True)
                self._conn.commit()
                print("Data awal Fakultas dimasukkan.")
            
            self._cursor.execute("SELECT COUNT(*) as count FROM Kamar")
            if (self._cursor.fetchone() or {}).get('count', 0) == 0:
                kamar_data_all = []
                for asrama_id_val in range(1, 9): 
                    for lantai in range(1, 4): 
                        for nomor_urut in range(1, 4): 
                            nomor_kamar_val = (lantai * 100) + nomor_urut
                            kamar_data_all.append((nomor_kamar_val, asrama_id_val, 2)) 
                
                for nk, aid, kap in kamar_data_all:
                     self._execute_query("INSERT INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES (%s, %s, %s)", (nk, aid, kap), is_ddl_or_commit_managed_elsewhere=True)
                self._conn.commit()
                print("Data awal Kamar untuk semua asrama dimasukkan.")

            # Tambahkan Admin Default jika tabel PenggunaAplikasi kosong
            self._cursor.execute("SELECT COUNT(*) as count FROM PenggunaAplikasi")
            if (self._cursor.fetchone() or {}).get('count', 0) == 0:
                print("Membuat pengguna admin default...")
                default_username = "admin"
                default_password_plain = "adminpassword" 
                
                args_admin_reg = (default_username, default_password_plain) 
                self._cursor.callproc('sp_RegistrasiPengguna', args_admin_reg)
                
                admin_reg_result = None
                for result in self._cursor.stored_results():
                    admin_reg_result = result.fetchone()
                    break
                
                if admin_reg_result and admin_reg_result.get('p_status_code') == 0:
                    self._conn.commit()
                    print(f"Pengguna admin default '{default_username}' berhasil dibuat: {admin_reg_result.get('p_status_message')}")
                elif admin_reg_result:
                    print(f"Gagal membuat pengguna admin default: {admin_reg_result.get('p_status_message')}")
                else:
                    print("Gagal membuat pengguna admin default: Tidak ada hasil dari SP.")


        except mysql.connector.Error as e:
            print(f"Kesalahan saat mengisi data master awal: {e}")

    def _hash_password(self, password):
        """Mengembalikan password teks biasa (TIDAK AMAN)."""
        return password 

    def register_user(self, username, password):
        """Mendaftarkan pengguna baru."""
        if not username or not password:
            return False, "Username dan password tidak boleh kosong."
        
        try:
            args_in = (username, password) 
            
            if not self._cursor:
                return False, "Kesalahan koneksi database internal (cursor tidak ada)."

            self._cursor.callproc('sp_RegistrasiPengguna', args_in)
            
            out_params_dict = None
            for result in self._cursor.stored_results(): 
                out_params_dict = result.fetchone()
                break 
            
            if out_params_dict:
                status_code = out_params_dict.get('p_status_code')
                status_message = out_params_dict.get('p_status_message')

                if status_code == 0:
                    self._conn.commit()
                    return True, status_message if status_message else "Registrasi berhasil."
                else:
                    return False, status_message if status_message else "Registrasi gagal karena alasan tidak diketahui."
            else:
                msg = "Gagal mengambil hasil dari Stored Procedure Registrasi (tidak ada result set)."
                print(f"ERROR: {msg}")
                return False, msg
        except mysql.connector.Error as err:
            msg = f"Gagal memanggil sp_RegistrasiPengguna: {err}"
            print(f"ERROR: {msg}")
            try:
                if self._conn.in_transaction: self._conn.rollback()
            except: pass
            return False, msg
        except Exception as e: 
            msg = f"Kesalahan tidak terduga saat registrasi: {e}"
            print(f"ERROR: {msg}")
            return False, msg


    def login_user(self, username, password):
        """Memvalidasi login pengguna."""
        if not username or not password:
            return None, None, "Username dan password tidak boleh kosong."
        
        args_in = (username, password)
        
        try:
            if not self._cursor:
                print("ERROR: Database cursor is not initialized.")
                return None, None, "Kesalahan koneksi database internal."

            self._cursor.callproc('sp_LoginPengguna', args_in)
            
            out_params_dict = None
            for result in self._cursor.stored_results():
                out_params_dict = result.fetchone()
                break
            
            if out_params_dict:
                status_code = out_params_dict.get('p_status_code')
                status_message = out_params_dict.get('p_status_message')
                user_id = out_params_dict.get('p_user_id')
                logged_in_username = out_params_dict.get('p_logged_in_username')

                print(f"DEBUG Login - DatabaseService (from SELECT): Status Code: {status_code}, Message: '{status_message}', UserID: {user_id}, Username: {logged_in_username}")

                if status_code == 0 and user_id is not None: 
                    return user_id, logged_in_username, status_message
                else: 
                    final_message = status_message if status_message else "Login gagal: Informasi tidak diketahui dari server."
                    if status_code == 0 and user_id is None: 
                        final_message = "Login berhasil menurut SP, tetapi data pengguna tidak diterima."
                        print(f"ERROR: {final_message}")
                    return None, None, final_message
            else:
                msg = "Gagal mengambil hasil dari Stored Procedure Login (tidak ada result set)."
                print(f"ERROR: {msg}")
                return None, None, msg

        except mysql.connector.Error as err:
            msg = f"Kesalahan Database SP saat login: {err}"
            print(f"ERROR: {msg}") 
            return None, None, msg
        except Exception as e: 
            msg = f"Kesalahan tidak terduga saat login: {e}"
            print(f"ERROR: {msg}") 
            return None, None, msg


    def add_penghuni(self, nim, nama, nama_fakultas, nomor_kamar_val, asrama_id_val, user_aksi):
        if not self._conn or not self._conn.is_connected(): 
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.", parent=self._parent_window)
            return False
        try:
            args_in = (nim, nama, nama_fakultas, nomor_kamar_val, asrama_id_val, user_aksi)
            self._cursor.callproc('sp_TambahPenghuni', args_in) 
            
            out_params_dict = None
            for result in self._cursor.stored_results():
                out_params_dict = result.fetchone()
                break
            
            if out_params_dict:
                status_code = out_params_dict.get('p_status_code')
                status_message = out_params_dict.get('p_status_message', "Status tidak diketahui.")

                if status_code == 0: 
                    messagebox.showinfo("Sukses", status_message, parent=self._parent_window)
                    self._conn.commit()  
                    return True
                else:
                    messagebox.showerror("Gagal Menambah Penghuni", status_message, parent=self._parent_window)
                    return False
            else:
                messagebox.showerror("Kesalahan SP", "Tidak dapat mengambil status dari SP Tambah Penghuni.", parent=self._parent_window)
                return False
        except mysql.connector.Error as err:
            messagebox.showerror("Kesalahan Database SP", f"Gagal memanggil sp_TambahPenghuni: {err}", parent=self._parent_window)
            try:
                if self._conn.in_transaction: self._conn.rollback() 
            except: pass
            return False

    def pindah_kamar_penghuni(self, nim, nomor_kamar_baru, asrama_id_baru, user_aksi):
        if not self._conn or not self._conn.is_connected(): 
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.", parent=self._parent_window)
            return False, "Tidak ada koneksi database."
        try:
            args_in = (nim, nomor_kamar_baru, asrama_id_baru, user_aksi)
            self._cursor.callproc('sp_PindahKamarPenghuni', args_in) 
            
            out_params_dict = None
            for result in self._cursor.stored_results():
                out_params_dict = result.fetchone()
                break

            if out_params_dict:
                status_code = out_params_dict.get('p_status_code')
                status_message = out_params_dict.get('p_status_message', "Status tidak diketahui.")

                if status_code == 0: 
                    if status_message and "Info:" in status_message: 
                        messagebox.showinfo("Info Pindah Kamar", status_message, parent=self._parent_window)
                    else:
                        messagebox.showinfo("Sukses Pindah Kamar", status_message if status_message else "Operasi berhasil.", parent=self._parent_window)
                    self._conn.commit() 
                    return True, status_message
                else:
                    messagebox.showerror("Gagal Pindah Kamar", status_message, parent=self._parent_window)
                    return False, status_message
            else:
                messagebox.showerror("Kesalahan SP", "Tidak dapat mengambil status dari SP Pindah Kamar.", parent=self._parent_window)
                return False, "Gagal mengambil status SP."
        except mysql.connector.Error as err:
            messagebox.showerror("Kesalahan Database SP", f"Gagal memanggil sp_PindahKamarPenghuni: {err}", parent=self._parent_window)
            try:
                if self._conn.in_transaction: self._conn.rollback() 
            except: pass
            return False, str(err)


    def update_penghuni(self, nim_original, nim_baru, nama_baru, nama_fakultas_baru, user_aksi):
        if not self._conn or not self._conn.is_connected(): 
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.", parent=self._parent_window)
            return "ERROR_CONNECTION" 

        check_exists_query = "SELECT 1 FROM Penghuni WHERE nim = %s"
        self._cursor.execute(check_exists_query, (nim_original,)) 
        if not self._cursor.fetchone(): 
            messagebox.showwarning("Perhatian", f"Tidak ada data penghuni yang cocok dengan NIM original: {nim_original}.", parent=self._parent_window)
            return "ERROR_NIM_ORIGINAL_NOT_FOUND"

        updates = []
        params = []
        
        if nim_baru and nim_original != nim_baru:
            if not nim_baru.isdigit(): 
                messagebox.showerror("Kesalahan Input", "NIM baru harus berupa angka.", parent=self._parent_window)
                return "ERROR_INVALID_NIM_FORMAT"
            check_nim_conflict_query = "SELECT 1 FROM Penghuni WHERE nim = %s"
            self._cursor.execute(check_nim_conflict_query, (nim_baru,)) 
            if self._cursor.fetchone(): 
                messagebox.showerror("Kesalahan", f"NIM baru '{nim_baru}' sudah digunakan oleh penghuni lain.", parent=self._parent_window)
                return "ERROR_NIM_CONFLICT"
            updates.append("nim = %s")
            params.append(nim_baru)
        
        if nama_baru: 
            updates.append("nama_penghuni = %s")
            params.append(nama_baru)

        fakultas_id_to_update = None 
        if nama_fakultas_baru is not None: 
            if nama_fakultas_baru == "": 
                 fakultas_id_to_update = None 
                 updates.append("fakultas_id = %s") 
                 params.append(fakultas_id_to_update)
            else:
                fakultas_id_to_update = self.get_fakultas_id_by_name(nama_fakultas_baru)
                if fakultas_id_to_update is None: 
                    try: 
                        self._cursor.execute("INSERT INTO Fakultas (nama_fakultas) VALUES (%s)", (nama_fakultas_baru,)) 
                        fakultas_id_to_update = self._cursor.lastrowid  
                        if fakultas_id_to_update: 
                            self._conn.commit()  
                            print(f"Fakultas baru '{nama_fakultas_baru}' ditambahkan dengan ID: {fakultas_id_to_update}")
                        else: 
                            messagebox.showerror("Kesalahan", f"Gagal menambahkan fakultas baru '{nama_fakultas_baru}'.", parent=self._parent_window)
                            return "ERROR_ADD_FAKULTAS"
                    except mysql.connector.Error as e_fak:
                        messagebox.showerror("Kesalahan Database", f"Gagal menambahkan fakultas baru: {e_fak}", parent=self._parent_window)
                        return "ERROR_ADD_FAKULTAS_DB"
                updates.append("fakultas_id = %s")
                params.append(fakultas_id_to_update)
        
        if not updates:
            messagebox.showinfo("Info", "Tidak ada data yang akan diubah (semua input kosong atau sama dengan data lama).", parent=self._parent_window)
            return "SUCCESS_NO_CHANGE" 

        params_for_update = list(params) 
        params_for_update.append(nim_original)
        query = f"UPDATE Penghuni SET {', '.join(updates)} WHERE nim = %s"
        
        try:
            self._cursor.execute("SET @session_user_aksi = %s", (user_aksi,))
            success = self._execute_query(query, tuple(params_for_update), is_ddl_or_commit_managed_elsewhere=False) 
            self._cursor.execute("SET @session_user_aksi = NULL") 
        except mysql.connector.Error as e_sess:
            messagebox.showerror("Kesalahan Database", f"Gagal mengatur session variable: {e_sess}", parent=self._parent_window)
            return "ERROR_SESSION_VAR"

        if success:
            if self._cursor.rowcount > 0: 
                messagebox.showinfo("Sukses", "Data penghuni berhasil diubah.", parent=self._parent_window)
                return "SUCCESS_DATA_CHANGED" 
            else:
                messagebox.showwarning("Perhatian", "Tidak ada perubahan aktual pada data (data baru mungkin sama dengan data lama).", parent=self._parent_window)
                return "SUCCESS_NO_ACTUAL_CHANGE" 
        else:
            return "ERROR_UPDATE_FAILED"


    def delete_penghuni(self, nim, user_aksi):
        if not self._conn or not self._conn.is_connected(): 
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.", parent=self._parent_window)
            return False
        try:
            self._cursor.execute("SET @session_user_aksi = %s", (user_aksi,))
            success = self._execute_query("DELETE FROM Penghuni WHERE nim = %s", (nim,), is_ddl_or_commit_managed_elsewhere=False) 
            self._cursor.execute("SET @session_user_aksi = NULL") 
        except mysql.connector.Error as e_sess:
            messagebox.showerror("Kesalahan Database", f"Gagal mengatur session variable: {e_sess}", parent=self._parent_window)
            return False

        if success and self._cursor.rowcount > 0: 
            messagebox.showinfo("Sukses", f"Data penghuni dengan NIM {nim} berhasil dihapus.", parent=self._parent_window)
            return True
        elif success and self._cursor.rowcount == 0: 
            messagebox.showwarning("Gagal", f"Penghuni dengan NIM {nim} tidak ditemukan.", parent=self._parent_window)
            return False
        return False

    def get_audit_log_penghuni(self, limit=100): 
        """Mengambil data log aktivitas penghuni dengan batasan jumlah."""
        query = """
            SELECT 
                log_id, DATE_FORMAT(waktu_aksi, '%Y-%m-%d %H:%i:%S') AS waktu_aksi_formatted, 
                aksi, nim, user_aksi, 
                IFNULL(nama_penghuni_baru, nama_penghuni_lama) AS nama_terkait,
                IF(aksi = 'INSERT', 
                   CONCAT('Ke: ', IFNULL(nomor_kamar_baru, 'N/A'), ' (', IFNULL(nama_asrama_baru, 'N/A'), ') - Fak: ', IFNULL(fakultas_baru, 'N/A')),
                   IF(aksi = 'DELETE',
                      CONCAT('Dari: ', IFNULL(nomor_kamar_lama, 'N/A'), ' (', IFNULL(nama_asrama_lama, 'N/A'), ') - Fak: ', IFNULL(fakultas_lama, 'N/A')),
                      CONCAT('Dari: ', IFNULL(nomor_kamar_lama, 'N/A'), ' (', IFNULL(nama_asrama_lama, 'N/A'), ') Fak: ', IFNULL(fakultas_lama, 'N/A'),
                             ' Ke: ', IFNULL(nomor_kamar_baru, 'N/A'), ' (', IFNULL(nama_asrama_baru, 'N/A'), ') Fak: ', IFNULL(fakultas_baru, 'N/A'))
                   )
                ) AS detail_perubahan,
                keterangan_tambahan
            FROM AuditLogAktivitasPenghuni 
            ORDER BY waktu_aksi DESC 
            LIMIT %s
        """ 
        return self._execute_query(query, (limit,), fetch_all=True) or [] 
    
    def get_audit_log_asrama(self, limit=100):
        query = """
            SELECT log_id, asrama_id_aksi, nama_asrama_lama, nama_asrama_baru, aksi, 
                   DATE_FORMAT(waktu_aksi, '%Y-%m-%d %H:%i:%S') AS waktu_aksi_formatted, 
                   user_aksi, keterangan_tambahan
            FROM AuditLogAktivitasAsrama
            ORDER BY waktu_aksi DESC
            LIMIT %s
        """
        return self._execute_query(query, (limit,), fetch_all=True) or []

    def get_audit_log_kamar(self, limit=100):
        query = """
            SELECT log_id, kamar_id_internal_aksi, 
                   nomor_kamar_lama, nomor_kamar_baru, 
                   asrama_id_lama, asrama_id_baru,
                   nama_asrama_lama, nama_asrama_baru,
                   kapasitas_lama, kapasitas_baru, 
                   aksi, DATE_FORMAT(waktu_aksi, '%Y-%m-%d %H:%i:%S') AS waktu_aksi_formatted, 
                   user_aksi, keterangan_tambahan
            FROM AuditLogAktivitasKamar
            ORDER BY waktu_aksi DESC
            LIMIT %s
        """
        return self._execute_query(query, (limit,), fetch_all=True) or []

    # --- CRUD Asrama ---
    def get_all_asrama(self):
        return self._execute_query("SELECT asrama_id, nama_asrama FROM Asrama ORDER BY nama_asrama", fetch_all=True) or []

    def add_asrama(self, asrama_id, nama_asrama):
        try:
            args = (asrama_id, nama_asrama)
            self._cursor.callproc('sp_TambahAsrama', args)
            stored_results = list(self._cursor.stored_results()) 
            if stored_results:
                result_set = stored_results[0]
                result = result_set.fetchone()
                if result:
                    if result.get('p_status_code') == 0: self._conn.commit()
                    return result.get('p_status_code'), result.get('p_status_message')
            return -1, "Gagal mengambil hasil dari SP Tambah Asrama."
        except mysql.connector.Error as err:
            return -1, f"Error database: {err}"

    def update_asrama(self, asrama_id, nama_asrama_baru):
        try:
            args = (asrama_id, nama_asrama_baru)
            self._cursor.callproc('sp_UpdateAsrama', args)
            stored_results = list(self._cursor.stored_results())
            if stored_results:
                result_set = stored_results[0]
                result = result_set.fetchone()
                if result:
                    if result.get('p_status_code') == 0: self._conn.commit()
                    return result.get('p_status_code'), result.get('p_status_message')
            return -1, "Gagal mengambil hasil dari SP Update Asrama."
        except mysql.connector.Error as err:
            return -1, f"Error database: {err}"

    def delete_asrama(self, asrama_id):
        try:
            args = (asrama_id,)
            self._cursor.callproc('sp_HapusAsrama', args)
            stored_results = list(self._cursor.stored_results())
            if stored_results:
                result_set = stored_results[0]
                result = result_set.fetchone()
                if result:
                    if result.get('p_status_code') == 0: self._conn.commit()
                    return result.get('p_status_code'), result.get('p_status_message')
            return -1, "Gagal mengambil hasil dari SP Hapus Asrama."
        except mysql.connector.Error as err:
            return -1, f"Error database: {err}"

    # --- CRUD Kamar ---
    def get_all_kamar_in_asrama(self, asrama_id):
        query = "SELECT kamar_id_internal, nomor_kamar, kapasitas FROM Kamar WHERE asrama_id = %s ORDER BY nomor_kamar"
        return self._execute_query(query, (asrama_id,), fetch_all=True) or []

    def add_kamar(self, nomor_kamar, asrama_id, kapasitas):
        try:
            args = (nomor_kamar, asrama_id, kapasitas)
            self._cursor.callproc('sp_TambahKamar', args)
            stored_results = list(self._cursor.stored_results())
            if stored_results:
                result_set = stored_results[0]
                result = result_set.fetchone()
                if result:
                    if result.get('p_status_code') == 0: self._conn.commit()
                    return result.get('p_status_code'), result.get('p_status_message')
            return -1, "Gagal mengambil hasil dari SP Tambah Kamar."
        except mysql.connector.Error as err:
            return -1, f"Error database: {err}"
            
    def update_kamar(self, kamar_id_internal, nomor_kamar_baru, kapasitas_baru, asrama_id_konteks):
        try:
            args = (kamar_id_internal, nomor_kamar_baru, kapasitas_baru, asrama_id_konteks)
            self._cursor.callproc('sp_UpdateKamar', args)
            stored_results = list(self._cursor.stored_results())
            if stored_results:
                result_set = stored_results[0]
                result = result_set.fetchone()
                if result:
                    if result.get('p_status_code') == 0: self._conn.commit()
                    return result.get('p_status_code'), result.get('p_status_message')
            return -1, "Gagal mengambil hasil dari SP Update Kamar."
        except mysql.connector.Error as err:
            return -1, f"Error database: {err}"

    def delete_kamar(self, kamar_id_internal):
        try:
            args = (kamar_id_internal,)
            self._cursor.callproc('sp_HapusKamar', args)
            stored_results = list(self._cursor.stored_results())
            if stored_results:
                result_set = stored_results[0]
                result = result_set.fetchone()
                if result:
                    if result.get('p_status_code') == 0: self._conn.commit()
                    return result.get('p_status_code'), result.get('p_status_message')
            return -1, "Gagal mengambil hasil dari SP Hapus Kamar."
        except mysql.connector.Error as err:
            return -1, f"Error database: {err}"
            
    # --- Metode untuk Penghuni (sudah ada, pastikan menggunakan stored_results jika SP diubah) ---
    def get_penghuni_in_kamar(self, nomor_kamar, asrama_id):
        """Mengambil daftar penghuni dalam satu kamar menggunakan vw_DaftarPenghuniLengkap."""
        query = """
            SELECT nim, nama_penghuni, fakultas 
            FROM vw_DaftarPenghuniLengkap 
            WHERE nomor_kamar = %s AND id_asrama_kamar = %s
            ORDER BY nama_penghuni;
        """
        penghuni = self._execute_query(query, (nomor_kamar, asrama_id), fetch_all=True)
        
        options_display = []
        if penghuni:
            options_display = [f"{p['nim']} - {p['nama_penghuni']}" for p in penghuni]
        
        if not options_display:
            options_display = ["Info: Belum ada penghuni di kamar ini."]
            
        return options_display, penghuni or []


    def get_jumlah_penghuni(self, nomor_kamar, asrama_id):
        """Mengambil jumlah penghuni saat ini di kamar tertentu."""
        query = "SELECT jumlah_penghuni_sekarang FROM vw_DetailKamarPenghuni WHERE nomor_kamar = %s AND asrama_id = %s"
        result = self._execute_query(query, (nomor_kamar, asrama_id), fetch_one=True)
        return result['jumlah_penghuni_sekarang'] if result else 0

    def get_kapasitas_kamar(self, nomor_kamar, asrama_id):
        """Mengambil kapasitas kamar tertentu."""
        query = "SELECT kapasitas FROM vw_DetailKamarPenghuni WHERE nomor_kamar = %s AND asrama_id = %s"
        result = self._execute_query(query, (nomor_kamar, asrama_id), fetch_one=True)
        return result['kapasitas'] if result else 0
        
    def get_all_fakultas(self):
        return self._execute_query("SELECT fakultas_id, nama_fakultas FROM Fakultas ORDER BY nama_fakultas", fetch_all=True) or []

    def get_fakultas_id_by_name(self, nama_fakultas):
        result = self._execute_query("SELECT fakultas_id FROM Fakultas WHERE nama_fakultas = %s", (nama_fakultas,), fetch_one=True)
        return result['fakultas_id'] if result else None


    def __del__(self):
        self._close()

# --- Kelas Dasar untuk Semua Layar ---
class BaseScreen:
    def __init__(self, screen_manager, db_service):
        self.screen_manager = screen_manager
        self.db_service = db_service
        self.app_instance = screen_manager.app
        self.canvas = self.app_instance.canvas
        self.widgets_on_screen = []
        self.canvas_items_on_screen = []
    def clear_screen_elements(self):
        for widget in self.widgets_on_screen: widget.destroy()
        self.widgets_on_screen = []
        for item in self.canvas_items_on_screen: self.canvas.delete(item)
        self.canvas_items_on_screen = []
    def add_widget(self, widget):
        self.widgets_on_screen.append(widget)
        return widget
    def create_canvas_text(self, *args, **kwargs):
        item = self.canvas.create_text(*args, **kwargs)
        self.canvas_items_on_screen.append(item)
        return item
    def create_canvas_image(self, *args, **kwargs):
        item = self.canvas.create_image(*args, **kwargs)
        self.canvas_items_on_screen.append(item)
        return item
    def setup_ui(self): raise NotImplementedError("Subclass harus mengimplementasikan metode setup_ui")

# --- Kelas Layar-Layar Aplikasi ---

# --- Layar Login ---
class LoginScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.username_var = StringVar()
        self.password_var = StringVar()
        self.username_entry = None
        self.password_entry = None

    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 150, 
                                text="LOGIN APLIKASI ASRAMA", 
                                fill="#F4FEFF", font=("Cooper Black", 30, "bold"))
        
        y_pos = 250
        self.create_canvas_text(self.app_instance.appwidth / 2 - 180, y_pos + 10, text="Username:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.username_entry = self.add_widget(Entry(self.canvas, textvariable=self.username_var, 
                                                       width=25, font=("Arial", 14)))
        self.username_entry.place(x=self.app_instance.appwidth / 2 - 170, y=y_pos)
        y_pos += 50

        self.create_canvas_text(self.app_instance.appwidth / 2 - 180, y_pos + 10, text="Password:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.password_entry = self.add_widget(Entry(self.canvas, textvariable=self.password_var, 
                                                       width=25, font=("Arial", 14), show="*"))
        self.password_entry.place(x=self.app_instance.appwidth / 2 - 170, y=y_pos)
        y_pos += 70

        tbl(self.canvas, self.app_instance.appwidth / 2 - 220, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "#F47B07", "Login", self._attempt_login)
        tbl(self.canvas, self.app_instance.appwidth / 2 + 20, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "#4682B4", "Sign Up", self.screen_manager.show_signup_screen)

    def _attempt_login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showerror("Login Gagal", "Username dan password tidak boleh kosong.", parent=self.app_instance.window)
            return

        user_id, logged_in_username, status_message = self.db_service.login_user(username, password) 
        
        if user_id: 
            self.app_instance.current_user_id = user_id 
            self.app_instance.current_username = logged_in_username 
            self.screen_manager.logged_in_user_id = user_id 
            self.screen_manager.show_main_menu() 
        else:
            if status_message: 
                 messagebox.showerror("Login Gagal", status_message, parent=self.app_instance.window)
            else: 
                 messagebox.showerror("Login Gagal", "Terjadi kesalahan tidak diketahui saat login.", parent=self.app_instance.window)


# --- Layar Sign Up ---
class SignUpScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.username_var = StringVar()
        self.password_var = StringVar()
        self.confirm_password_var = StringVar()
        self.username_entry = None
        self.password_entry = None
        self.confirm_password_entry = None

    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 150, 
                                text="REGISTRASI PENGGUNA BARU", 
                                fill="#F4FEFF", font=("Cooper Black", 30, "bold"))
        
        y_pos = 230
        self.create_canvas_text(self.app_instance.appwidth / 2 - 200, y_pos + 10, text="Username Baru:", 
                                fill="#F4FEFF", font=("Arial", 12, "bold"), anchor="e")
        self.username_entry = self.add_widget(Entry(self.canvas, textvariable=self.username_var, 
                                                       width=25, font=("Arial", 12)))
        self.username_entry.place(x=self.app_instance.appwidth / 2 - 190, y=y_pos)
        y_pos += 40

        self.create_canvas_text(self.app_instance.appwidth / 2 - 200, y_pos + 10, text="Password Baru:", 
                                fill="#F4FEFF", font=("Arial", 12, "bold"), anchor="e")
        self.password_entry = self.add_widget(Entry(self.canvas, textvariable=self.password_var, 
                                                       width=25, font=("Arial", 12), show="*"))
        self.password_entry.place(x=self.app_instance.appwidth / 2 - 190, y=y_pos)
        y_pos += 40

        self.create_canvas_text(self.app_instance.appwidth / 2 - 200, y_pos + 10, text="Konfirmasi Password:", 
                                fill="#F4FEFF", font=("Arial", 12, "bold"), anchor="e")
        self.confirm_password_entry = self.add_widget(Entry(self.canvas, textvariable=self.confirm_password_var, 
                                                       width=25, font=("Arial", 12), show="*"))
        self.confirm_password_entry.place(x=self.app_instance.appwidth / 2 - 190, y=y_pos)
        y_pos += 60

        tbl(self.canvas, self.app_instance.appwidth / 2 - 220, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "#4CAF50", "Daftar", self._attempt_signup) 
        tbl(self.canvas, self.app_instance.appwidth / 2 + 20, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "gray", "Kembali ke Login", self.screen_manager.show_login_screen)

    def _attempt_signup(self):
        username = self.username_var.get()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()

        if not username or not password or not confirm_password:
            messagebox.showerror("Input Tidak Valid", "Semua field harus diisi.", parent=self.app_instance.window)
            return
        if password != confirm_password:
            messagebox.showerror("Password Tidak Cocok", "Password dan konfirmasi password tidak sama.", parent=self.app_instance.window)
            return
        if len(password) < 6: 
            messagebox.showerror("Password Lemah", "Password minimal harus 6 karakter.", parent=self.app_instance.window)
            return

        success, message = self.db_service.register_user(username, password)
        if success:
            messagebox.showinfo("Registrasi Berhasil", message, parent=self.app_instance.window) 
            self.screen_manager.show_login_screen()
        else:
            if message: 
                messagebox.showerror("Gagal Registrasi", message, parent=self.app_instance.window)
            else: 
                messagebox.showerror("Gagal Registrasi", "Terjadi kesalahan tidak diketahui.", parent=self.app_instance.window)


class MainMenuScreen(BaseScreen):
    def setup_ui(self):
        self.create_canvas_text(270, 300, text="MANAJEMEN\nSISTEM\nASRAMA", fill="#F47B07", font=("Cooper Black", 50, "bold"), anchor="w")
        tbl(self.canvas, 700, 180, 300, 100, 20, 20, 90, 180, 270, 360, "#F47B07", "Masuk", self.screen_manager.show_asrama_selection)
        tbl(self.canvas, 700, 300, 300, 100, 20, 20, 90, 180, 270, 360, "#4682B4", "Riwayat Aktivitas", self.screen_manager.show_riwayat_utama_screen) # Diubah ke RiwayatUtamaScreen
        tbl(self.canvas, 700, 420, 300, 100, 20, 20, 90, 180, 270, 360, "red", "Keluar", self.app_instance.quit)

class AsramaSelectionScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.selected_asrama_nama_var = StringVar() 
        self.asrama_options_map = {} 
        self.asrama_dropdown = None

    def _populate_asrama_dropdown(self):
        asramas_data = self.db_service.get_all_asrama()
        self.asrama_options_map = {asrama['nama_asrama']: asrama['asrama_id'] for asrama in asramas_data}
        asrama_names = list(self.asrama_options_map.keys())
        
        if self.asrama_dropdown:
            self.asrama_dropdown['values'] = asrama_names
            if asrama_names:
                self.selected_asrama_nama_var.set(asrama_names[0]) 
            else:
                self.selected_asrama_nama_var.set("")
        elif asrama_names: 
             self.selected_asrama_nama_var.set(asrama_names[0])


    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 50, 
                                text="MANAJEMEN DATA ASRAMA", 
                                fill="#F4FEFF", font=("Cooper Black", 30, "bold"))
        
        tbl(self.canvas, 50, 15, 150, 50, 10, 10, 90, 180, 270, 360, 
            "red", "Kembali", self.screen_manager.show_main_menu)

        y_pos = 120
        self.create_canvas_text(self.app_instance.appwidth / 2 - 250, y_pos + 10, text="Pilih Asrama:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.asrama_dropdown = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.selected_asrama_nama_var, 
                                                            width=30, font=("Arial", 14), state="readonly"))
        self.asrama_dropdown.place(x=self.app_instance.appwidth / 2 - 240, y=y_pos)
        self._populate_asrama_dropdown() 
        y_pos += 60

        button_width = 220
        button_height = 50
        x_start_buttons = self.app_instance.appwidth / 2 - (button_width * 2 + 20) / 2 

        tbl(self.canvas, x_start_buttons, y_pos, button_width, button_height, 10, 10, 90, 180, 270, 360,
            "#007bff", "Lihat Kamar Asrama Ini", self._lihat_kamar_asrama)
        
        tbl(self.canvas, x_start_buttons + button_width + 20, y_pos, button_width, button_height, 10, 10, 90, 180, 270, 360,
            "#28a745", "Tambah Asrama Baru", self._tambah_asrama)
        y_pos += button_height + 15

        tbl(self.canvas, x_start_buttons, y_pos, button_width, button_height, 10, 10, 90, 180, 270, 360,
            "#ffc107", "Ubah Nama Asrama Ini", self._ubah_asrama)
        
        tbl(self.canvas, x_start_buttons + button_width + 20, y_pos, button_width, button_height, 10, 10, 90, 180, 270, 360,
            "#dc3545", "Hapus Asrama Ini", self._hapus_asrama)

    def _get_selected_asrama_details(self):
        selected_nama_asrama = self.selected_asrama_nama_var.get()
        if not selected_nama_asrama:
            messagebox.showwarning("Pilihan Kosong", "Silakan pilih asrama terlebih dahulu.", parent=self.app_instance.window)
            return None, None
        asrama_id = self.asrama_options_map.get(selected_nama_asrama)
        return asrama_id, selected_nama_asrama

    def _lihat_kamar_asrama(self):
        asrama_id, nama_asrama = self._get_selected_asrama_details()
        if asrama_id:
            self.screen_manager.show_kamar_list(asrama_id, nama_asrama)

    def _tambah_asrama(self):
        self.screen_manager.show_add_asrama_form()

    def _ubah_asrama(self):
        asrama_id, nama_asrama_lama = self._get_selected_asrama_details()
        if asrama_id:
            self.screen_manager.show_update_asrama_form(asrama_id, nama_asrama_lama)
            
    def _hapus_asrama(self):
        asrama_id, nama_asrama = self._get_selected_asrama_details()
        if asrama_id:
            if messagebox.askyesno("Konfirmasi Hapus", f"Anda yakin ingin menghapus asrama '{nama_asrama}' (ID: {asrama_id})?", parent=self.app_instance.window):
                status_code, status_message = self.db_service.delete_asrama(asrama_id)
                if status_code == 0:
                    messagebox.showinfo("Sukses", status_message, parent=self.app_instance.window)
                    self._populate_asrama_dropdown() 
                else:
                    messagebox.showerror("Gagal Menghapus", status_message, parent=self.app_instance.window)

# --- Layar Tambah Asrama (Baru) ---
class AddAsramaScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.asrama_id_var = StringVar()
        self.nama_asrama_var = StringVar()

    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 100, 
                                text="TAMBAH ASRAMA BARU", 
                                fill="#F4FEFF", font=("Cooper Black", 26, "bold"))
        
        y_pos = 200
        self.create_canvas_text(self.app_instance.appwidth / 2 - 150, y_pos + 10, text="ID Asrama:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.add_widget(Entry(self.canvas, textvariable=self.asrama_id_var, 
                               width=20, font=("Arial", 14))).place(x=self.app_instance.appwidth / 2 - 140, y=y_pos)
        y_pos += 50

        self.create_canvas_text(self.app_instance.appwidth / 2 - 150, y_pos + 10, text="Nama Asrama:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.add_widget(Entry(self.canvas, textvariable=self.nama_asrama_var, 
                               width=30, font=("Arial", 14))).place(x=self.app_instance.appwidth / 2 - 140, y=y_pos)
        y_pos += 70

        tbl(self.canvas, self.app_instance.appwidth / 2 - 220, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "#28a745", "Simpan Asrama", self._simpan_asrama)
        tbl(self.canvas, self.app_instance.appwidth / 2 + 20, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "gray", "Batal", self.screen_manager.show_asrama_selection)

    def _simpan_asrama(self):
        try:
            asrama_id = int(self.asrama_id_var.get())
        except ValueError:
            messagebox.showerror("Input Tidak Valid", "ID Asrama harus berupa angka.", parent=self.app_instance.window)
            return
        nama_asrama = self.nama_asrama_var.get().strip()

        if not nama_asrama:
            messagebox.showerror("Input Tidak Valid", "Nama Asrama tidak boleh kosong.", parent=self.app_instance.window)
            return

        status_code, status_message = self.db_service.add_asrama(asrama_id, nama_asrama)
        if status_code == 0:
            messagebox.showinfo("Sukses", status_message, parent=self.app_instance.window)
            self.screen_manager.show_asrama_selection() 
        else:
            messagebox.showerror("Gagal Menyimpan", status_message, parent=self.app_instance.window)


class UpdateAsramaScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, asrama_id, nama_asrama_lama): 
        super().__init__(screen_manager, db_service)
        self.asrama_id_to_update = asrama_id
        self.nama_asrama_baru_var = StringVar(value=nama_asrama_lama) 
        self.nama_asrama_lama = nama_asrama_lama

    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 100, 
                                text=f"UBAH NAMA ASRAMA (ID: {self.asrama_id_to_update})", 
                                fill="#F4FEFF", font=("Cooper Black", 22, "bold"))
        
        y_pos = 200
        self.create_canvas_text(self.app_instance.appwidth / 2 - 150, y_pos + 10, text="Nama Asrama Baru:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.add_widget(Entry(self.canvas, textvariable=self.nama_asrama_baru_var, 
                               width=30, font=("Arial", 14))).place(x=self.app_instance.appwidth / 2 - 140, y=y_pos)
        y_pos += 70
        
        tbl(self.canvas, self.app_instance.appwidth / 2 - 220, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "#ffc107", "Simpan Perubahan", self._save_update_asrama) 
        tbl(self.canvas, self.app_instance.appwidth / 2 + 20, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "gray", "Batal", self.screen_manager.show_asrama_selection)

    def _save_update_asrama(self):
        nama_baru = self.nama_asrama_baru_var.get().strip()
        if not nama_baru:
            messagebox.showerror("Input Tidak Valid", "Nama asrama baru tidak boleh kosong.", parent=self.app_instance.window)
            return
        if nama_baru == self.nama_asrama_lama:
            messagebox.showinfo("Info", "Tidak ada perubahan pada nama asrama.", parent=self.app_instance.window)
            self.screen_manager.show_asrama_selection()
            return 

        status_code, status_message = self.db_service.update_asrama(self.asrama_id_to_update, nama_baru)
        if status_code == 0:
            messagebox.showinfo("Sukses", status_message, parent=self.app_instance.window)
            self.screen_manager.show_asrama_selection()
        else:
            messagebox.showerror("Gagal Mengubah", status_message, parent=self.app_instance.window)


# --- Layar Tambah Kamar (Baru) ---
class AddKamarScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, asrama_id, asrama_nama):
        super().__init__(screen_manager, db_service)
        self.asrama_id = asrama_id
        self.asrama_nama = asrama_nama
        self.nomor_kamar_var = StringVar()
        self.kapasitas_var = StringVar(value="2") 

    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 100, 
                                text=f"TAMBAH KAMAR BARU DI ASRAMA {self.asrama_nama.upper()}", 
                                fill="#F4FEFF", font=("Cooper Black", 22, "bold"))
        
        y_pos = 200
        self.create_canvas_text(self.app_instance.appwidth / 2 - 150, y_pos + 10, text="Nomor Kamar:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.add_widget(Entry(self.canvas, textvariable=self.nomor_kamar_var, 
                               width=15, font=("Arial", 14))).place(x=self.app_instance.appwidth / 2 - 140, y=y_pos)
        y_pos += 50

        self.create_canvas_text(self.app_instance.appwidth / 2 - 150, y_pos + 10, text="Kapasitas:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.add_widget(Entry(self.canvas, textvariable=self.kapasitas_var, 
                               width=15, font=("Arial", 14))).place(x=self.app_instance.appwidth / 2 - 140, y=y_pos)
        y_pos += 70

        tbl(self.canvas, self.app_instance.appwidth / 2 - 220, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "#28a745", "Simpan Kamar", self._simpan_kamar)
        tbl(self.canvas, self.app_instance.appwidth / 2 + 20, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "gray", "Batal", lambda: self.screen_manager.show_kamar_list(self.asrama_id, self.asrama_nama))

    def _simpan_kamar(self):
        try:
            nomor_kamar = int(self.nomor_kamar_var.get())
            kapasitas = int(self.kapasitas_var.get())
        except ValueError:
            messagebox.showerror("Input Tidak Valid", "Nomor kamar dan kapasitas harus berupa angka.", parent=self.app_instance.window)
            return
        
        if kapasitas <= 0:
            messagebox.showerror("Input Tidak Valid", "Kapasitas harus lebih besar dari 0.", parent=self.app_instance.window)
            return

        status_code, status_message = self.db_service.add_kamar(nomor_kamar, self.asrama_id, kapasitas)
        if status_code == 0:
            messagebox.showinfo("Sukses", status_message, parent=self.app_instance.window)
            self.screen_manager.show_kamar_list(self.asrama_id, self.asrama_nama)
        else:
            messagebox.showerror("Gagal Menyimpan", status_message, parent=self.app_instance.window)


class UpdateKamarScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id_internal, asrama_id, asrama_nama, nomor_kamar_lama, kapasitas_lama): 
        super().__init__(screen_manager, db_service)
        self.kamar_id_internal_to_update = kamar_id_internal
        self.asrama_id = asrama_id
        self.asrama_nama = asrama_nama
        self.nomor_kamar_baru_var = StringVar(value=str(nomor_kamar_lama))
        self.kapasitas_baru_var = StringVar(value=str(kapasitas_lama))
        self.nomor_kamar_lama = nomor_kamar_lama
        self.kapasitas_lama = kapasitas_lama

    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 100, 
                                text=f"UBAH KAMAR DI ASRAMA {self.asrama_nama.upper()}", 
                                fill="#F4FEFF", font=("Cooper Black", 20, "bold"))
        
        y_pos = 180
        self.create_canvas_text(self.app_instance.appwidth / 2 - 180, y_pos + 10, text="Nomor Kamar Baru:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.add_widget(Entry(self.canvas, textvariable=self.nomor_kamar_baru_var, 
                               width=20, font=("Arial", 14))).place(x=self.app_instance.appwidth / 2 - 170, y=y_pos)
        y_pos += 50

        self.create_canvas_text(self.app_instance.appwidth / 2 - 180, y_pos + 10, text="Kapasitas Baru:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.add_widget(Entry(self.canvas, textvariable=self.kapasitas_baru_var, 
                               width=20, font=("Arial", 14))).place(x=self.app_instance.appwidth / 2 - 170, y=y_pos)
        y_pos += 70

        tbl(self.canvas, self.app_instance.appwidth / 2 - 220, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "#ffc107", "Simpan Perubahan", self._save_update_kamar)
        tbl(self.canvas, self.app_instance.appwidth / 2 + 20, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "gray", "Batal", lambda: self.screen_manager.show_kamar_list(self.asrama_id, self.asrama_nama))

    def _save_update_kamar(self):
        try:
            nomor_baru = int(self.nomor_kamar_baru_var.get())
            kapasitas_baru = int(self.kapasitas_baru_var.get())
        except ValueError:
            messagebox.showerror("Input Tidak Valid", "Nomor kamar dan kapasitas harus berupa angka.", parent=self.app_instance.window)
            return

        if kapasitas_baru <= 0:
            messagebox.showerror("Input Tidak Valid", "Kapasitas harus lebih besar dari 0.", parent=self.app_instance.window)
            return
            
        if nomor_baru == self.nomor_kamar_lama and kapasitas_baru == self.kapasitas_lama:
            messagebox.showinfo("Info", "Tidak ada perubahan pada data kamar.", parent=self.app_instance.window)
            self.screen_manager.show_kamar_list(self.asrama_id, self.asrama_nama)
            return 

        status_code, status_message = self.db_service.update_kamar(
            self.kamar_id_internal_to_update, 
            nomor_baru, 
            kapasitas_baru,
            self.asrama_id 
        )
        if status_code == 0:
            messagebox.showinfo("Sukses", status_message, parent=self.app_instance.window)
            self.screen_manager.show_kamar_list(self.asrama_id, self.asrama_nama)
        else:
            messagebox.showerror("Gagal Mengubah", status_message, parent=self.app_instance.window)


class KamarListScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, asrama_id, asrama_nama):
        super().__init__(screen_manager, db_service)
        self.asrama_id = asrama_id
        self.asrama_nama = asrama_nama
        self.kamar_dropdown_var = StringVar()
        self.kamar_options_map = {} # nomor_kamar -> (kamar_id_internal, kapasitas)
        self.kamar_dropdown = None

    def _populate_kamar_dropdown(self):
        kamars_data = self.db_service.get_all_kamar_in_asrama(self.asrama_id)
        self.kamar_options_map = {
            str(k['nomor_kamar']): (k['kamar_id_internal'], k['kapasitas']) 
            for k in kamars_data
        }
        kamar_numbers = list(self.kamar_options_map.keys())
        
        if self.kamar_dropdown:
            self.kamar_dropdown['values'] = kamar_numbers
            if kamar_numbers:
                self.kamar_dropdown_var.set(kamar_numbers[0])
            else:
                self.kamar_dropdown_var.set("")
        elif kamar_numbers:
            self.kamar_dropdown_var.set(kamar_numbers[0])


    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 50, 
                                text=f"MANAJEMEN KAMAR ASRAMA {self.asrama_nama.upper()}", 
                                fill="#F4FEFF", font=("Cooper Black", 24, "bold"))
        
        tbl(self.canvas, 50, 15, 150, 50, 10, 10, 90, 180, 270, 360, 
            "red", "Kembali ke Asrama", self.screen_manager.show_asrama_selection)

        y_pos = 120
        self.create_canvas_text(self.app_instance.appwidth / 2 - 250, y_pos + 10, text="Pilih Kamar:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.kamar_dropdown = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.kamar_dropdown_var, 
                                                            width=20, font=("Arial", 14), state="readonly"))
        self.kamar_dropdown.place(x=self.app_instance.appwidth / 2 - 240, y=y_pos)
        self._populate_kamar_dropdown()
        y_pos += 60

        button_width = 220
        button_height = 50
        x_start_buttons = self.app_instance.appwidth / 2 - (button_width * 2 + 20) / 2 

        tbl(self.canvas, x_start_buttons, y_pos, button_width, button_height, 10, 10, 90, 180, 270, 360,
            "#007bff", "Lihat Detail Kamar Ini", self._lihat_detail_kamar)
        
        tbl(self.canvas, x_start_buttons + button_width + 20, y_pos, button_width, button_height, 10, 10, 90, 180, 270, 360,
            "#28a745", "Tambah Kamar Baru", self._tambah_kamar)
        y_pos += button_height + 15

        tbl(self.canvas, x_start_buttons, y_pos, button_width, button_height, 10, 10, 90, 180, 270, 360,
            "#ffc107", "Ubah Kamar Ini", self._ubah_kamar)
        
        tbl(self.canvas, x_start_buttons + button_width + 20, y_pos, button_width, button_height, 10, 10, 90, 180, 270, 360,
            "#dc3545", "Hapus Kamar Ini", self._hapus_kamar)

    def _get_selected_kamar_details(self):
        selected_nomor_kamar_str = self.kamar_dropdown_var.get()
        if not selected_nomor_kamar_str:
            messagebox.showwarning("Pilihan Kosong", "Silakan pilih kamar terlebih dahulu.", parent=self.app_instance.window)
            return None, None, None
        try:
            selected_nomor_kamar = int(selected_nomor_kamar_str)
        except ValueError:
            messagebox.showerror("Kesalahan", "Nomor kamar tidak valid.", parent=self.app_instance.window)
            return None, None, None

        kamar_data = self.kamar_options_map.get(str(selected_nomor_kamar)) 
        if kamar_data:
            kamar_id_internal, kapasitas = kamar_data
            return kamar_id_internal, selected_nomor_kamar, kapasitas
        else:
             messagebox.showerror("Kesalahan", "Detail kamar tidak ditemukan.", parent=self.app_instance.window)
             return None, None, None


    def _lihat_detail_kamar(self):
        _, nomor_kamar, _ = self._get_selected_kamar_details()
        if nomor_kamar is not None:
            self.screen_manager.show_kamar_detail(nomor_kamar) 

    def _tambah_kamar(self):
        self.screen_manager.show_add_kamar_form(self.asrama_id, self.asrama_nama)

    def _ubah_kamar(self):
        kamar_id_internal, nomor_kamar, kapasitas = self._get_selected_kamar_details()
        if kamar_id_internal:
            self.screen_manager.show_update_kamar_form(kamar_id_internal, self.asrama_id, self.asrama_nama, nomor_kamar, kapasitas)
            
    def _hapus_kamar(self):
        kamar_id_internal, nomor_kamar, _ = self._get_selected_kamar_details()
        if kamar_id_internal:
            if messagebox.askyesno("Konfirmasi Hapus", f"Anda yakin ingin menghapus Kamar {nomor_kamar} di Asrama {self.asrama_nama}?", parent=self.app_instance.window):
                status_code, status_message = self.db_service.delete_kamar(kamar_id_internal)
                if status_code == 0:
                    messagebox.showinfo("Sukses", status_message, parent=self.app_instance.window)
                    self._populate_kamar_dropdown() 
                else:
                    messagebox.showerror("Gagal Menghapus", status_message, parent=self.app_instance.window)


class KamarDetailScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id): 
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context
        self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.nomor_kamar=kamar_id 
        self.penghuni_treeview=None; self.treeview_scrollbar=None
    def setup_ui(self):
        style=ttk.Style(); style.configure("Custom.Treeview", background="#E1E1E1", fieldbackground="#FFFFFF", foreground="black")
        style.configure("Custom.Treeview.Heading", background="yellow", foreground="black", font=('Arial',10,'bold'), relief="flat")
        style.map("Custom.Treeview.Heading", background=[('active','#FFD700')])
        self.create_canvas_text(self.app_instance.appwidth/2, 80, text=f"Asrama {self.asrama_nama} - Kamar {self.nomor_kamar}", fill="#000000", font=("Cooper Black",22,"bold"))
        info_text_x=self.app_instance.appwidth/2; info_text_y=120
        jml_penghuni=self.db_service.get_jumlah_penghuni(self.nomor_kamar,self.asrama_id)
        kapasitas=self.db_service.get_kapasitas_kamar(self.nomor_kamar,self.asrama_id)
        self.create_canvas_text(info_text_x,info_text_y, text=f"Data Penghuni ({jml_penghuni}/{kapasitas})", fill="#000000", font=("Cooper Black",18,"bold"))
        table_x=50; table_y=info_text_y+20+20; table_container_width=self.app_instance.appwidth-(2*50)
        scrollbar_width=20; treeview_actual_width=table_container_width-scrollbar_width
        treeview_display_height=self.app_instance.appheight-table_y-70-120
        columns=("no","nim","nama","fakultas"); self.penghuni_treeview=ttk.Treeview(self.canvas,columns=columns,show='headings',style="Custom.Treeview")
        for col,txt,w,anc in [("no","No.",0.05,tk.CENTER),("nim","NIM",0.25,tk.W),("nama","Nama Mahasiswa",0.40,tk.W),("fakultas","Fakultas",0.30,tk.W)]:
            self.penghuni_treeview.heading(col,text=txt); self.penghuni_treeview.column(col,width=int(treeview_actual_width*w),anchor=anc,stretch=tk.YES if col!="no" else tk.NO)
        self.treeview_scrollbar=ttk.Scrollbar(self.canvas,orient="vertical",command=self.penghuni_treeview.yview)
        self.penghuni_treeview.configure(yscrollcommand=self.treeview_scrollbar.set)
        _,daftar_penghuni=self.db_service.get_penghuni_in_kamar(self.nomor_kamar,self.asrama_id)
        for i in self.penghuni_treeview.get_children(): self.penghuni_treeview.delete(i)
        if daftar_penghuni and not (isinstance(daftar_penghuni[0],str) and daftar_penghuni[0].startswith("Info:")):
            for i,p in enumerate(daftar_penghuni): self.penghuni_treeview.insert("","end",values=(i+1,p['nim'],p['nama_penghuni'],p.get('fakultas') or "N/A")) 
        else:
            if not self.penghuni_treeview.get_children(): self.penghuni_treeview.insert("","end",values=("","Belum ada penghuni.","",""))
        self.add_widget(self.penghuni_treeview); self.add_widget(self.treeview_scrollbar)
        self.canvas.create_window(table_x,table_y,anchor=tk.NW,window=self.penghuni_treeview,width=treeview_actual_width,height=treeview_display_height)
        self.canvas.create_window(table_x+treeview_actual_width,table_y,anchor=tk.NW,window=self.treeview_scrollbar,height=treeview_display_height)
        y_buttons=15; btn_width=150; btn_spacing=160; current_x=50
        actions=[("Kembali","red",lambda:self.screen_manager.show_kamar_list(self.asrama_id,self.asrama_nama)),
                 ("Tambah Data","#F47B07",lambda:self.screen_manager.show_insert_data_form(self.nomor_kamar)),
                 ("Ubah Data","#F47B07",lambda:self.screen_manager.show_update_data_form(self.nomor_kamar)),
                 ("Hapus Data","#F47B07",lambda:self.screen_manager.show_delete_data_form(self.nomor_kamar))]
        for i, (text,color,cmd) in enumerate(actions):
            tbl(self.canvas,current_x + (i*btn_spacing),y_buttons,btn_width,50,10,10,90,180,270,360,color,text,cmd)
        y_pindah=table_y+treeview_display_height+25; lebar_pindah=200; x_pindah=(self.app_instance.appwidth/2)-(lebar_pindah/2)
        tbl(self.canvas,x_pindah,y_pindah,lebar_pindah,50,10,10,90,180,270,360,"blue","Pindah Kamar",lambda:self.screen_manager.show_pindah_kamar_form(self.nomor_kamar))

    def clear_screen_elements(self): super().clear_screen_elements(); self.penghuni_treeview=None; self.treeview_scrollbar=None

class InsertDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, nomor_kamar): # nomor_kamar
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context
        self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.nomor_kamar=nomor_kamar # Simpan nomor_kamar
        self.nim_entry=None; self.nama_entry=None; self.fakultas_pilihan=StringVar()
        self.fakultas_map={}
    def setup_ui(self):
        self.create_canvas_text(560,50,text=f"Insert Data Kamar {self.nomor_kamar} Asrama {self.asrama_nama}",fill="#F4F0FF",font=("Cooper Black",24,"bold"))
        self.create_canvas_text(365,188,text="NIM",fill="#F4FEFF",font=("Arial",12,"bold"))
        self.nim_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF")); self.nim_entry.place(x=350,y=200)
        self.create_canvas_text(374,270,text="Nama",fill="#F4FEFF",font=("Arial",12,"bold"))
        self.nama_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF")); self.nama_entry.place(x=350,y=280)
        self.create_canvas_text(385,340,text="Fakultas",fill="#F4FEFF",font=("Arial",12,"bold"))
        fakultas_db=self.db_service.get_all_fakultas(); fakultas_display_list=[""]
        if fakultas_db:
            for fak in fakultas_db: self.fakultas_map[fak['nama_fakultas']]=fak['fakultas_id']; fakultas_display_list.append(fak['nama_fakultas'])
        self.fakultas_pilihan.set(fakultas_display_list[0])
        dropdown=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.fakultas_pilihan,values=fakultas_display_list,width=29,font=("Arial",18),state="readonly"))
        dropdown.place(x=350,y=360)
        tbl(self.canvas,300,430,200,70,20,20,90,180,270,360,"#F47B07","Simpan",self._save_data)
        tbl(self.canvas,600,430,200,70,20,20,90,180,270,360,"red","Batal",lambda:self.screen_manager.show_kamar_detail(self.nomor_kamar))
    def _save_data(self):
        nim=self.nim_entry.get(); nama=self.nama_entry.get(); nama_fakultas_terpilih=self.fakultas_pilihan.get()
        user_aksi = self.app_instance.current_username 
        if not nim or not nama: messagebox.showwarning("Input Tidak Lengkap","NIM dan Nama tidak boleh kosong."); return
        if nim and not nim.isdigit(): 
            messagebox.showerror("Kesalahan Input", "NIM harus berupa angka.")
            return
        if self.db_service.add_penghuni(nim,nama,nama_fakultas_terpilih if nama_fakultas_terpilih else None,self.nomor_kamar,self.asrama_id, user_aksi):
            self.screen_manager.show_kamar_detail(self.nomor_kamar)

class UpdateDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, nomor_kamar): # nomor_kamar
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context
        self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.nomor_kamar=nomor_kamar # Simpan nomor_kamar
        self.selected_mahasiswa_nim_original=None; self.nim_baru_entry=None; self.nama_baru_entry=None
        self.fakultas_baru_pilihan=StringVar(); self.plh_mahasiswa_var=StringVar(); self.data_lengkap_mahasiswa_cache=[]; self.fakultas_map={}
    def setup_ui(self):
        self.create_canvas_text(560,50,text=f"Ubah Data Kamar {self.nomor_kamar} Asrama {self.asrama_nama}",fill="#F4FEFF",font=("Cooper Black",20,"bold"))
        opsi_display_db,self.data_lengkap_mahasiswa_cache=self.db_service.get_penghuni_in_kamar(self.nomor_kamar,self.asrama_id)
        self.create_canvas_text(413,100,text="Pilih Mahasiswa (NIM - Nama)",fill="#F4FEFF",font=("Arial",12,"bold"))
        m_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.plh_mahasiswa_var,font=("Arial",15),state="readonly",values=opsi_display_db,width=34))
        m_dd.place(x=350,y=120);m_dd.bind("<<ComboboxSelected>>",self._on_mahasiswa_selected)
        self.create_canvas_text(386,178,text="NIM Baru (Kosongkan jika tidak diubah)",fill="#F4FEFF",font=("Arial",10,"bold"))
        self.nim_baru_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF"));self.nim_baru_entry.place(x=350,y=190)
        self.create_canvas_text(391,258,text="Nama Baru (Kosongkan jika tidak diubah)",fill="#F4FEFF",font=("Arial",10,"bold"))
        self.nama_baru_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF"));self.nama_baru_entry.place(x=350,y=270)
        self.create_canvas_text(405,328,text="Fakultas Baru",fill="#F4FEFF",font=("Arial",12,"bold"))
        fakultas_db=self.db_service.get_all_fakultas();fakultas_display_list=[""]
        if fakultas_db:
            for fak in fakultas_db:self.fakultas_map[fak['nama_fakultas']]=fak['fakultas_id'];fakultas_display_list.append(fak['nama_fakultas'])
        f_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.fakultas_baru_pilihan,values=fakultas_display_list,width=29,font=("Arial",18),state="readonly"))
        f_dd.place(x=350,y=350)
        if opsi_display_db and not opsi_display_db[0].startswith("Info:")and not opsi_display_db[0].startswith("Kesalahan:"):
            self.plh_mahasiswa_var.set(opsi_display_db[0]);self._on_mahasiswa_selected()
        elif opsi_display_db and(opsi_display_db[0].startswith("Info:")or opsi_display_db[0].startswith("Kesalahan:")):self.plh_mahasiswa_var.set(opsi_display_db[0])
        else:
            self.plh_mahasiswa_var.set("Tidak ada data penghuni.")
            if self.nim_baru_entry:self.nim_baru_entry.delete(0,tk.END)
            if self.nama_baru_entry:self.nama_baru_entry.delete(0,tk.END)
            self.fakultas_baru_pilihan.set("")
        tbl(self.canvas,300,430,200,70,20,20,90,180,270,360,"#F47B07","Ubah",self._update_data_action)
        tbl(self.canvas,600,430,200,70,20,20,90,180,270,360,"red","Batal",lambda:self.screen_manager.show_kamar_detail(self.nomor_kamar))
    def _get_nim_from_selection(self,s):return s.split(" - ")[0]if" - "in s else None
    def _on_mahasiswa_selected(self,e=None):
        if not all([self.nim_baru_entry,self.nama_baru_entry,hasattr(self.fakultas_baru_pilihan,'set')]):return
        s_disp_s=self.plh_mahasiswa_var.get();nim_orig=self._get_nim_from_selection(s_disp_s)
        self.selected_mahasiswa_nim_original=nim_orig
        self.nim_baru_entry.delete(0,tk.END);self.nama_baru_entry.delete(0,tk.END);self.fakultas_baru_pilihan.set("")
        if nim_orig and self.data_lengkap_mahasiswa_cache:
            for d_mhs in self.data_lengkap_mahasiswa_cache:
                if str(d_mhs['nim'])==str(nim_orig):
                    self.nama_baru_entry.insert(0,str(d_mhs['nama_penghuni']))
                    self.fakultas_baru_pilihan.set(str(d_mhs.get('fakultas'))if d_mhs.get('fakultas')else"")
                    break
    def _update_data_action(self):
        if not self.selected_mahasiswa_nim_original:messagebox.showwarning("Peringatan","Pilih mahasiswa.");return
        nim_n=self.nim_baru_entry.get().strip();nama_n=self.nama_baru_entry.get().strip();fak_n=self.fakultas_baru_pilihan.get()
        user_aksi = self.app_instance.current_username
        
        if nim_n and not nim_n.isdigit():
            messagebox.showerror("Kesalahan Input", "NIM baru harus berupa angka.")
            return
        
        current_nama_e_v=self.nama_baru_entry.get()
        if not nama_n and current_nama_e_v.strip() != "": 
             messagebox.showwarning("Input Tidak Valid","Nama baru tidak boleh dikosongkan jika field diisi.")
             return
        
        update_status = self.db_service.update_penghuni(self.selected_mahasiswa_nim_original,nim_n,nama_n,fak_n if fak_n else None, user_aksi)
        
        if update_status == "SUCCESS_DATA_CHANGED":
            self.screen_manager.show_kamar_detail(self.nomor_kamar)

class DeleteDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, nomor_kamar): # nomor_kamar
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context
        self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.nomor_kamar=nomor_kamar # Simpan nomor_kamar
        self.plh_mahasiswa_var=StringVar(); self.selected_mahasiswa_nim_to_delete=None
    def setup_ui(self):
        self.create_canvas_text(560,50,text=f"Hapus Data Kamar {self.nomor_kamar} Asrama {self.asrama_nama}",fill="#F4FEFF",font=("Cooper Black",20,"bold"))
        opsi_display_db,_=self.db_service.get_penghuni_in_kamar(self.nomor_kamar,self.asrama_id)
        self.create_canvas_text(413,290,text="Pilih Mahasiswa (NIM - Nama) untuk Dihapus",fill="#F4FEFF",font=("Arial",12,"bold"))
        m_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.plh_mahasiswa_var,font=("Arial",15),state="readonly",values=opsi_display_db,width=34))
        m_dd.place(x=350,y=310);m_dd.bind("<<ComboboxSelected>>",self._on_mahasiswa_selected)
        if opsi_display_db and not opsi_display_db[0].startswith("Info:")and not opsi_display_db[0].startswith("Kesalahan:"):
            self.plh_mahasiswa_var.set(opsi_display_db[0]);self._on_mahasiswa_selected()
        elif opsi_display_db and(opsi_display_db[0].startswith("Info:")or opsi_display_db[0].startswith("Kesalahan:")):self.plh_mahasiswa_var.set(opsi_display_db[0])
        else:self.plh_mahasiswa_var.set("Tidak ada data penghuni.")
        tbl(self.canvas,300,430,200,70,20,20,90,180,270,360,"red","Hapus",self._delete_data_action)
        tbl(self.canvas,600,430,200,70,20,20,90,180,270,360,"#F47B07","Batal",lambda:self.screen_manager.show_kamar_detail(self.nomor_kamar))
    def _get_nim_from_selection(self,s):return s.split(" - ")[0]if" - "in s else None
    def _on_mahasiswa_selected(self,e=None):self.selected_mahasiswa_nim_to_delete=self._get_nim_from_selection(self.plh_mahasiswa_var.get())
    def _delete_data_action(self):
        if not self.selected_mahasiswa_nim_to_delete:messagebox.showwarning("Peringatan","Pilih mahasiswa.");return
        user_aksi = self.app_instance.current_username
        if messagebox.askyesno("Konfirmasi Hapus",f"Yakin hapus NIM {self.selected_mahasiswa_nim_to_delete}?"):
            if self.db_service.delete_penghuni(self.selected_mahasiswa_nim_to_delete, user_aksi):self.screen_manager.show_kamar_detail(self.nomor_kamar)

class PindahKamarScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, nomor_kamar_asal): # nomor_kamar_asal
        super().__init__(screen_manager, db_service)
        self.nomor_kamar_asal=nomor_kamar_asal # Simpan nomor_kamar_asal
        self.asrama_id_asal=screen_manager.current_asrama_id_context
        self.asrama_nama_asal=screen_manager.current_asrama_nama_context
        self.selected_nim_var=StringVar(); self.selected_asrama_tujuan_var=StringVar(); self.selected_kamar_tujuan_var=StringVar()
        self.penghuni_asal_options=[]; self.asrama_tujuan_options_map={}; self.kamar_tujuan_options_map={}
    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth/2,50,text=f"Pindah Kamar dari {self.asrama_nama_asal} - Kamar {self.nomor_kamar_asal}",fill="#F4FEFF",font=("Cooper Black",20,"bold"))
        y_curr=110;lbl_w=150;dd_w_char=30;est_dd_px_w=dd_w_char*7;form_w=lbl_w+10+est_dd_px_w
        x_lbl=(self.app_instance.appwidth-form_w)/2;x_dd=x_lbl+lbl_w+10
        self.create_canvas_text(x_lbl,y_curr+10,text="Pilih Penghuni:",fill="#F4FEFF",font=("Arial",12,"bold"),anchor="w")
        opsi_p,_=self.db_service.get_penghuni_in_kamar(self.nomor_kamar_asal,self.asrama_id_asal)
        self.penghuni_asal_options=opsi_p if not(opsi_p and opsi_p[0].startswith("Info:"))else["Tidak ada penghuni"]
        p_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.selected_nim_var,values=self.penghuni_asal_options,width=dd_w_char,state="readonly",font=("Arial",14)))
        p_dd.place(x=x_dd,y=y_curr);y_curr+=50
        if self.penghuni_asal_options and self.penghuni_asal_options[0]!="Tidak ada penghuni":self.selected_nim_var.set(self.penghuni_asal_options[0])
        
        self.create_canvas_text(x_lbl,y_curr+10,text="Asrama Tujuan:",fill="#F4FEFF",font=("Arial",12,"bold"),anchor="w")
        all_a=self.db_service.get_all_asrama();
        self.asrama_tujuan_options_map={a['nama_asrama']:a['asrama_id']for a in all_a}
        a_disp_opts=list(self.asrama_tujuan_options_map.keys())
        a_t_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.selected_asrama_tujuan_var,values=a_disp_opts,width=dd_w_char,state="readonly",font=("Arial",14)))
        a_t_dd.place(x=x_dd,y=y_curr);a_t_dd.bind("<<ComboboxSelected>>",self._on_asrama_tujuan_selected);y_curr+=50
        
        self.create_canvas_text(x_lbl,y_curr+10,text="Kamar Tujuan:",fill="#F4FEFF",font=("Arial",12,"bold"),anchor="w")
        self.kamar_tujuan_dropdown=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.selected_kamar_tujuan_var,values=[],width=dd_w_char,state="disabled",font=("Arial",14)))
        self.kamar_tujuan_dropdown.place(x=x_dd,y=y_curr);y_curr+=70
        
        btn_w=200;x_btn_p=self.app_instance.appwidth/2-btn_w-10;x_btn_b=self.app_instance.appwidth/2+10
        tbl(self.canvas,x_btn_p,y_curr,btn_w,50,10,10,90,180,270,360,"blue","Pindahkan",self._proses_pindah_kamar)
        tbl(self.canvas,x_btn_b,y_curr,btn_w,50,10,10,90,180,270,360,"red","Batal",lambda:self.screen_manager.show_kamar_detail(self.nomor_kamar_asal))

    def _on_asrama_tujuan_selected(self,e=None):
        nama_a=self.selected_asrama_tujuan_var.get()
        id_a_t=self.asrama_tujuan_options_map.get(nama_a)
        self.kamar_tujuan_options_map = {} # Reset map kamar
        if id_a_t:
            kamars=self.db_service.get_all_kamar_in_asrama(id_a_t)
            kamar_display_options = []
            for k in kamars:
                # Pastikan kamar tujuan tidak sama dengan kamar asal jika asramanya sama
                if not (id_a_t == self.asrama_id_asal and k['nomor_kamar'] == self.nomor_kamar_asal):
                    display_text = f"Kamar {k['nomor_kamar']} (Kapasitas: {k['kapasitas']})"
                    self.kamar_tujuan_options_map[display_text] = k['nomor_kamar']
                    kamar_display_options.append(display_text)

            self.kamar_tujuan_dropdown['values']=kamar_display_options
            if kamar_display_options:
                self.selected_kamar_tujuan_var.set(kamar_display_options[0])
                self.kamar_tujuan_dropdown['state']="readonly"
            else:
                self.selected_kamar_tujuan_var.set("Tidak ada kamar tersedia")
                self.kamar_tujuan_dropdown['state']="disabled"
        else:
            self.kamar_tujuan_dropdown['values']=[]
            self.selected_kamar_tujuan_var.set("")
            self.kamar_tujuan_dropdown['state']="disabled"

    def _proses_pindah_kamar(self):
        nim_s=self.selected_nim_var.get()
        if not nim_s or nim_s=="Tidak ada penghuni":
            messagebox.showwarning("Peringatan","Pilih penghuni yang akan dipindahkan.", parent=self.app_instance.window)
            return
        nim_m=nim_s.split(" - ")[0]
        
        nama_a_t=self.selected_asrama_tujuan_var.get()
        id_a_t=self.asrama_tujuan_options_map.get(nama_a_t)
        
        kamar_tujuan_display = self.selected_kamar_tujuan_var.get()
        no_k_t = self.kamar_tujuan_options_map.get(kamar_tujuan_display)

        user_aksi = self.app_instance.current_username
        
        if not id_a_t or not no_k_t or kamar_tujuan_display == "Tidak ada kamar tersedia":
            messagebox.showwarning("Peringatan","Pilih asrama & kamar tujuan yang valid.", parent=self.app_instance.window)
            return
        
        succ,msg=self.db_service.pindah_kamar_penghuni(nim_m,no_k_t,id_a_t, user_aksi)
        if succ:
            # Pesan sukses sudah ditampilkan oleh db_service, cukup kembali
            self.screen_manager.show_kamar_detail(self.nomor_kamar_asal)
        # Pesan error juga sudah ditangani oleh db_service

# --- Layar Riwayat Utama ---
class RiwayatUtamaScreen(BaseScreen):
    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 100, 
                                text="PILIH RIWAYAT AKTIVITAS", 
                                fill="#F4FEFF", font=("Cooper Black", 30, "bold"))
        
        y_pos = 200
        button_width = 300
        button_height = 70
        spacing = 20
        
        tbl(self.canvas, self.app_instance.appwidth / 2 - button_width / 2, y_pos, 
            button_width, button_height, 15, 15, 90, 180, 270, 360,
            "#17a2b8", "Riwayat Data Penghuni", self.screen_manager.show_riwayat_penghuni_screen)
        y_pos += button_height + spacing

        tbl(self.canvas, self.app_instance.appwidth / 2 - button_width / 2, y_pos, 
            button_width, button_height, 15, 15, 90, 180, 270, 360,
            "#17a2b8", "Riwayat Data Asrama", self.screen_manager.show_riwayat_asrama_screen)
        y_pos += button_height + spacing
        
        tbl(self.canvas, self.app_instance.appwidth / 2 - button_width / 2, y_pos, 
            button_width, button_height, 15, 15, 90, 180, 270, 360,
            "#17a2b8", "Riwayat Data Kamar", self.screen_manager.show_riwayat_kamar_screen)
        y_pos += button_height + spacing*2

        tbl(self.canvas, self.app_instance.appwidth / 2 - 100, y_pos, 
            200, 50, 10, 10, 90, 180, 270, 360,
            "gray", "Kembali ke Menu Utama", self.screen_manager.show_main_menu)


class RiwayatPenghuniScreen(BaseScreen): # Sebelumnya RiwayatAktivitasScreen
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.log_treeview=None; self.log_scrollbar=None
    def setup_ui(self):
        style=ttk.Style(); style.configure("Riwayat.Treeview",background="#F0F0F0",fieldbackground="#FFFFFF",foreground="black",rowheight=25)
        style.configure("Riwayat.Treeview.Heading",background="#BFBFBF",foreground="black",font=('Arial',10,'bold'),relief="flat")
        style.map("Riwayat.Treeview.Heading",background=[('active','#A0A0A0')])
        
        y_buttons = 15
        tbl(self.canvas, 50, y_buttons, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali", self.screen_manager.show_riwayat_utama_screen)
        
        self.create_canvas_text(self.app_instance.appwidth/2, 50,text="Riwayat Aktivitas Penghuni",fill="#000000",font=("Cooper Black",24,"bold"))

        table_padding_horizontal = 30
        table_padding_top = y_buttons + 50 + 20 
        table_padding_bottom = 20 
        
        table_x = table_padding_horizontal
        table_y = table_padding_top
        
        table_container_width = self.app_instance.appwidth-(2*table_padding_horizontal);scr_w=20;tree_w=table_container_width-scr_w 
        tree_h=self.app_instance.appheight-table_y-table_padding_bottom - 50 

        cols=("log_id","waktu","aksi","nim", "user_aksi", "nama","detail_kamar","keterangan") 
        self.log_treeview=ttk.Treeview(self.canvas,columns=cols,show='headings',style="Riwayat.Treeview")
        hdrs={"log_id":"ID","waktu":"Waktu","aksi":"Aksi","nim":"NIM", "user_aksi":"User", "nama":"Nama Terkait","detail_kamar":"Detail Perubahan","keterangan":"Keterangan"}
        cols_cfg={"log_id":{"w":0.04,"anc":tk.CENTER,"st":tk.NO},"waktu":{"w":0.15,"anc":tk.W,"st":tk.YES},"aksi":{"w":0.07,"anc":tk.W,"st":tk.YES},
                  "nim":{"w":0.10,"anc":tk.W,"st":tk.YES}, "user_aksi":{"w":0.10,"anc":tk.W,"st":tk.YES}, "nama":{"w":0.15,"anc":tk.W,"st":tk.YES},
                  "detail_kamar":{"w":0.22,"anc":tk.W,"st":tk.YES},"keterangan":{"w":0.17,"anc":tk.W,"st":tk.YES}}
        for c,t in hdrs.items(): self.log_treeview.heading(c,text=t); self.log_treeview.column(c,width=int(tree_w*cols_cfg[c]["w"]),anchor=cols_cfg[c]["anc"],stretch=cols_cfg[c]["st"])
        self.log_scrollbar=ttk.Scrollbar(self.canvas,orient="vertical",command=self.log_treeview.yview); self.log_treeview.configure(yscrollcommand=self.log_scrollbar.set)
        logs=self.db_service.get_audit_log_penghuni(limit=200)
        for i in self.log_treeview.get_children(): self.log_treeview.delete(i)
        if logs:
            for log in logs: self.log_treeview.insert("","end",values=(
                log['log_id'],log['waktu_aksi_formatted'],log['aksi'],log['nim'],
                log.get('user_aksi', 'N/A'), 
                log['nama_terkait'],log['detail_perubahan'],log['keterangan_tambahan']
                ))
        else: self.log_treeview.insert("","end",values=("","Belum ada riwayat.","","","","","",""))
        self.add_widget(self.log_treeview); self.add_widget(self.log_scrollbar)
        self.canvas.create_window(table_x,table_y,anchor=tk.NW,window=self.log_treeview,width=tree_w,height=tree_h)
        self.canvas.create_window(table_x+tree_w,table_y,anchor=tk.NW,window=self.log_scrollbar,height=tree_h) # Disesuaikan dengan tbl_y
        
    def clear_screen_elements(self): super().clear_screen_elements(); self.log_treeview=None; self.log_scrollbar=None

class RiwayatAsramaScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.log_treeview = None
        self.log_scrollbar = None

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Riwayat.Treeview", background="#F0F0F0", fieldbackground="#FFFFFF", foreground="black", rowheight=25)
        style.configure("Riwayat.Treeview.Heading", background="#BFBFBF", foreground="black", font=('Arial', 10, 'bold'), relief="flat")
        style.map("Riwayat.Treeview.Heading", background=[('active', '#A0A0A0')])

        y_buttons = 15
        tbl(self.canvas, 50, y_buttons, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali", self.screen_manager.show_riwayat_utama_screen)
        self.create_canvas_text(self.app_instance.appwidth / 2, 50, text="Riwayat Aktivitas Asrama", fill="#000000", font=("Cooper Black", 24, "bold"))

        table_padding_horizontal = 30
        table_padding_top = y_buttons + 50 + 20
        table_padding_bottom = 20
        table_x = table_padding_horizontal
        table_y = table_padding_top
        table_container_width = self.app_instance.appwidth - (2 * table_padding_horizontal)
        scrollbar_width = 20
        treeview_actual_width = table_container_width - scrollbar_width
        treeview_display_height = self.app_instance.appheight - table_y - table_padding_bottom - 50

        cols = ("log_id", "waktu", "aksi", "asrama_id", "nama_lama", "nama_baru", "user_aksi", "keterangan")
        self.log_treeview = ttk.Treeview(self.canvas, columns=cols, show='headings', style="Riwayat.Treeview")
        
        headers_config = {
            "log_id": {"text": "ID Log", "width": 0.05, "anchor": tk.CENTER},
            "waktu": {"text": "Waktu Aksi", "width": 0.15, "anchor": tk.W},
            "aksi": {"text": "Aksi", "width": 0.08, "anchor": tk.W},
            "asrama_id": {"text": "ID Asrama", "width": 0.08, "anchor": tk.CENTER},
            "nama_lama": {"text": "Nama Lama", "width": 0.15, "anchor": tk.W},
            "nama_baru": {"text": "Nama Baru", "width": 0.15, "anchor": tk.W},
            "user_aksi": {"text": "User Aksi", "width": 0.10, "anchor": tk.W},
            "keterangan": {"text": "Keterangan", "width": 0.24, "anchor": tk.W}
        }

        for col, config in headers_config.items():
            self.log_treeview.heading(col, text=config["text"])
            self.log_treeview.column(col, width=int(treeview_actual_width * config["width"]), anchor=config["anchor"], stretch=tk.YES)

        self.log_scrollbar = ttk.Scrollbar(self.canvas, orient="vertical", command=self.log_treeview.yview)
        self.log_treeview.configure(yscrollcommand=self.log_scrollbar.set)

        logs = self.db_service.get_audit_log_asrama(limit=200)
        for i in self.log_treeview.get_children(): self.log_treeview.delete(i)
        if logs:
            for log in logs:
                self.log_treeview.insert("", "end", values=(
                    log['log_id'], log['waktu_aksi_formatted'], log['aksi'],
                    log.get('asrama_id_aksi', 'N/A'),
                    log.get('nama_asrama_lama', 'N/A'),
                    log.get('nama_asrama_baru', 'N/A'),
                    log.get('user_aksi', 'N/A'),
                    log.get('keterangan_tambahan', '')
                ))
        else:
            self.log_treeview.insert("", "end", values=("", "Belum ada riwayat.", "", "", "", "", "", ""))

        self.add_widget(self.log_treeview)
        self.add_widget(self.log_scrollbar)
        self.canvas.create_window(table_x, table_y, anchor=tk.NW, window=self.log_treeview, width=treeview_actual_width, height=treeview_display_height)
        self.canvas.create_window(table_x + treeview_actual_width, table_y, anchor=tk.NW, window=self.log_scrollbar, height=treeview_display_height)

class RiwayatKamarScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.log_treeview = None
        self.log_scrollbar = None

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Riwayat.Treeview", background="#F0F0F0", fieldbackground="#FFFFFF", foreground="black", rowheight=25)
        style.configure("Riwayat.Treeview.Heading", background="#BFBFBF", foreground="black", font=('Arial', 10, 'bold'), relief="flat")
        style.map("Riwayat.Treeview.Heading", background=[('active', '#A0A0A0')])

        y_buttons = 15
        tbl(self.canvas, 50, y_buttons, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali", self.screen_manager.show_riwayat_utama_screen)
        self.create_canvas_text(self.app_instance.appwidth / 2, 50, text="Riwayat Aktivitas Kamar", fill="#000000", font=("Cooper Black", 24, "bold"))

        table_padding_horizontal = 20
        table_padding_top = y_buttons + 50 + 20
        table_padding_bottom = 20
        table_x = table_padding_horizontal
        table_y = table_padding_top
        table_container_width = self.app_instance.appwidth - (2 * table_padding_horizontal)
        scrollbar_width = 20
        treeview_actual_width = table_container_width - scrollbar_width
        treeview_display_height = self.app_instance.appheight - table_y - table_padding_bottom - 50

        cols = ("log_id", "waktu", "aksi", "kamar_id", "no_kamar_lama", "no_kamar_baru", "asrama_lama", "asrama_baru", "kap_lama", "kap_baru", "user_aksi", "keterangan")
        self.log_treeview = ttk.Treeview(self.canvas, columns=cols, show='headings', style="Riwayat.Treeview")
        
        headers_config = {
            "log_id": {"text": "ID", "width": 0.03}, "waktu": {"text": "Waktu", "width": 0.12},
            "aksi": {"text": "Aksi", "width": 0.06}, "kamar_id": {"text": "ID Kamar", "width": 0.07},
            "no_kamar_lama": {"text": "No. Lama", "width": 0.07}, "no_kamar_baru": {"text": "No. Baru", "width": 0.07},
            "asrama_lama": {"text": "Asrama Lama", "width": 0.10}, "asrama_baru": {"text": "Asrama Baru", "width": 0.10},
            "kap_lama": {"text": "Kap. Lama", "width": 0.07}, "kap_baru": {"text": "Kap. Baru", "width": 0.07},
            "user_aksi": {"text": "User", "width": 0.08}, "keterangan": {"text": "Keterangan", "width": 0.16}
        }

        for col, config in headers_config.items():
            self.log_treeview.heading(col, text=config["text"])
            self.log_treeview.column(col, width=int(treeview_actual_width * config["width"]), anchor=tk.W, stretch=tk.YES)
        self.log_treeview.column("log_id", anchor=tk.CENTER)
        self.log_treeview.column("kamar_id", anchor=tk.CENTER)


        self.log_scrollbar = ttk.Scrollbar(self.canvas, orient="vertical", command=self.log_treeview.yview)
        self.log_treeview.configure(yscrollcommand=self.log_scrollbar.set)

        logs = self.db_service.get_audit_log_kamar(limit=200)
        for i in self.log_treeview.get_children(): self.log_treeview.delete(i)
        if logs:
            for log in logs:
                self.log_treeview.insert("", "end", values=(
                    log['log_id'], log['waktu_aksi_formatted'], log['aksi'],
                    log.get('kamar_id_internal_aksi', 'N/A'),
                    log.get('nomor_kamar_lama', 'N/A'), log.get('nomor_kamar_baru', 'N/A'),
                    log.get('nama_asrama_lama', 'N/A'), log.get('nama_asrama_baru', 'N/A'),
                    log.get('kapasitas_lama', 'N/A'), log.get('kapasitas_baru', 'N/A'),
                    log.get('user_aksi', 'N/A'),
                    log.get('keterangan_tambahan', '')
                ))
        else:
            self.log_treeview.insert("", "end", values=("", "Belum ada riwayat.", "", "", "", "", "", "", "", "", "", ""))

        self.add_widget(self.log_treeview)
        self.add_widget(self.log_scrollbar)
        self.canvas.create_window(table_x, table_y, anchor=tk.NW, window=self.log_treeview, width=treeview_actual_width, height=treeview_display_height)
        self.canvas.create_window(table_x + treeview_actual_width, table_y, anchor=tk.NW, window=self.log_scrollbar, height=treeview_display_height)


# ==============================================================================
# == KELAS ScreenManager ==
# ==============================================================================
class ScreenManager:
    def __init__(self, app, db_service):
        self.app = app 
        self.db_service = db_service
        self.current_screen_instance = None
        self.current_asrama_id_context = None
        self.current_asrama_nama_context = None
        self.logged_in_user_id = None 

    def _display_screen(self, screen_class, *args, **kwargs): 
        if self.current_screen_instance: self.current_screen_instance.clear_screen_elements()
        self.app._clear_canvas_for_new_screen()
        self.app._draw_background() 
        self.current_screen_instance = screen_class(self, self.db_service, *args, **kwargs) 
        self.current_screen_instance.setup_ui() 

    def show_login_screen(self): 
        self._display_screen(LoginScreen)

    def show_signup_screen(self): 
        self._display_screen(SignUpScreen)

    def show_main_menu(self): 
        if not self.logged_in_user_id: 
            self.show_login_screen()
        else:
            self._display_screen(MainMenuScreen)

    def show_asrama_selection(self):
        self.current_asrama_id_context = None 
        self.current_asrama_nama_context = None
        self._display_screen(AsramaSelectionScreen)

    def show_add_asrama_form(self): 
        self._display_screen(AddAsramaScreen)

    def show_update_asrama_form(self, asrama_id, nama_asrama_lama): 
        self._display_screen(UpdateAsramaScreen, asrama_id=asrama_id, nama_asrama_lama=nama_asrama_lama)

    def show_kamar_list(self, asrama_id, asrama_nama):
        self.current_asrama_id_context = asrama_id
        self.current_asrama_nama_context = asrama_nama
        self._display_screen(KamarListScreen, asrama_id, asrama_nama)

    def show_add_kamar_form(self, asrama_id, asrama_nama): 
        self._display_screen(AddKamarScreen, asrama_id=asrama_id, asrama_nama=asrama_nama)

    def show_update_kamar_form(self, kamar_id_internal, asrama_id, asrama_nama, nomor_kamar_lama, kapasitas_lama): 
        self._display_screen(UpdateKamarScreen, kamar_id_internal=kamar_id_internal, asrama_id=asrama_id, asrama_nama=asrama_nama, nomor_kamar_lama=nomor_kamar_lama, kapasitas_lama=kapasitas_lama)

    def show_kamar_detail(self, kamar_id): 
        if self.current_asrama_id_context is None:
            messagebox.showerror("Kesalahan Navigasi", "Konteks asrama tidak ditemukan.")
            self.show_asrama_selection()
            return
        self._display_screen(KamarDetailScreen, kamar_id)
    def show_insert_data_form(self, kamar_id): self._display_screen(InsertDataScreen, kamar_id)
    def show_update_data_form(self, kamar_id): self._display_screen(UpdateDataScreen, kamar_id)
    def show_delete_data_form(self, kamar_id): self._display_screen(DeleteDataScreen, kamar_id)
    def show_pindah_kamar_form(self, kamar_id_asal): 
        self._display_screen(PindahKamarScreen, kamar_id_asal)
    
    def show_riwayat_utama_screen(self): # Baru
        self._display_screen(RiwayatUtamaScreen)

    def show_riwayat_penghuni_screen(self): # Baru (menggantikan show_riwayat_aktivitas)
        self._display_screen(RiwayatPenghuniScreen)

    def show_riwayat_asrama_screen(self): # Baru
        self._display_screen(RiwayatAsramaScreen)

    def show_riwayat_kamar_screen(self): # Baru
        self._display_screen(RiwayatKamarScreen)
    

# ==============================================================================
# == KELAS AppGui (Aplikasi Utama) ==
# ==============================================================================
class AppGui: 
    def __init__(self, root_window):
        self.window = root_window
        self.window.title("Manajemen Asrama OOP - MySQL")
        self.appwidth = 1080
        self.appheight = 700
        self.current_user_id = None 
        self.current_username = None 
        self._setup_window_geometry()
        self.canvas = Canvas(self.window, width=self.appwidth, height=self.appheight)
        self.canvas.place(x=0, y=0)
        self.bg_image_tk = None
        self.asset_path = "./assets/um.png" 
        self._load_assets()
        
        MYSQL_HOST = os.getenv("DB_HOST", "localhost")
        MYSQL_USER = os.getenv("DB_USER", "root")
        MYSQL_PASSWORD = os.getenv("DB_PASSWORD", "") 
        MYSQL_DB_NAME = os.getenv("DB_NAME", "asrama_db_mysql") 
        
        self.db_service = DatabaseService(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database_name=MYSQL_DB_NAME, parent_window=self.window) 
        self.screen_manager = ScreenManager(self, self.db_service)
        
        if self.db_service._conn and self.db_service._conn.is_connected(): 
            self._draw_background()
            self.screen_manager.show_login_screen() 
        else:
            self.canvas.create_text(self.appwidth / 2, self.appheight / 2, text="Koneksi ke Database Gagal.\nPeriksa konfigurasi dan server MySQL Anda.\nAplikasi tidak dapat dimulai.", font=("Arial", 16, "bold"), fill="red", justify=tk.CENTER)

    def _setup_window_geometry(self):
        screen_width = self.window.winfo_screenwidth()
        x_pos = (screen_width / 2) - (self.appwidth / 2)
        y_pos = 0
        self.window.geometry(f"{self.appwidth}x{self.appheight}+{int(x_pos)}+{int(y_pos)}")
        self.window.resizable(False, False)

    def _load_assets(self):
        try:
            current_script_dir = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
            assets_dir = os.path.join(current_script_dir, "assets")
            
            if not os.path.isdir(assets_dir): 
                try:
                    os.makedirs(assets_dir)
                    print(f"Direktori '{assets_dir}' dibuat. Harap letakkan 'um.png' di dalamnya.")
                except OSError as e:
                    print(f"Gagal membuat direktori '{assets_dir}': {e}")
            
            image_path = os.path.join(assets_dir, "um.png")

            if not os.path.exists(image_path):
                 messagebox.showwarning("Aset Tidak Ditemukan", f"File gambar '{image_path}' tidak ditemukan. Background akan default.", parent=self.window if self.window.winfo_exists() else None)
                 self.bg_image_tk = None
                 return

            bg_img_pil = Image.open(image_path).resize((self.appwidth, self.appheight))
            self.bg_image_tk = ImageTk.PhotoImage(bg_img_pil)
        except FileNotFoundError: 
            messagebox.showwarning("Aset Tidak Ditemukan", f"Pastikan file '{self.asset_path}' ada di direktori 'assets'.", parent=self.window if self.window.winfo_exists() else None)
            self.bg_image_tk = None 
        except Exception as e: 
            messagebox.showerror("Kesalahan Aset", f"Gagal memuat gambar: {e}", parent=self.window if self.window.winfo_exists() else None)
            self.bg_image_tk = None 

    def _draw_background(self):
        if self.bg_image_tk: 
            self.canvas.create_image(0, 0, image=self.bg_image_tk, anchor=NW, tags="app_background")
        else: 
            self.canvas.create_rectangle(0,0, self.appwidth, self.appheight, fill="#CCCCCC", tags="app_background")

    def _clear_canvas_for_new_screen(self):
        all_items = self.canvas.find_all()
        for item in all_items:
            if "app_background" not in self.canvas.gettags(item): 
                self.canvas.delete(item)

    def quit(self):
        if messagebox.askokcancel("Keluar", "Anda yakin ingin keluar dari aplikasi?", parent=self.window):
            if self.db_service: 
                self.db_service._close()
            self.window.quit()
            self.window.destroy()

# ==============================================================================
# == TITIK MASUK APLIKASI ==
# ==============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    main_app = AppGui(root) 
    root.mainloop()
