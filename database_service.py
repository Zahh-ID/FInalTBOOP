import mysql.connector
from tkinter import messagebox # messagebox diimpor di siniimport hashlib
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