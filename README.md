# Aplikasi Manajemen Asrama

## Deskripsi Proyek
Aplikasi Manajemen Asrama adalah sistem informasi berbasis desktop yang dikembangkan menggunakan Python dengan GUI Tkinter dan database MySQL. Aplikasi ini bertujuan untuk mempermudah pengelolaan data asrama, termasuk unit asrama, kamar, penghuni, serta menyediakan fitur pelacakan riwayat aktivitas perubahan data.

Aplikasi ini dirancang untuk administrator atau pengelola asrama agar dapat melakukan pendataan dan pengelolaan informasi secara lebih efisien dan terpusat.

## Fitur Utama
* **Manajemen Pengguna**:
    * Registrasi pengguna baru (Sign Up).
    * Login pengguna terautentikasi.
    * Pembuatan akun admin default (`admin`/`adminpassword`) saat inisialisasi pertama jika tidak ada pengguna.
* **Manajemen Data Master Asrama (CRUD)**:
    * Menambah data asrama baru dengan ID dan nama yang unik.
    * Melihat daftar semua asrama melalui dropdown.
    * Mengubah nama asrama yang sudah ada.
    * Menghapus data asrama (dengan validasi jika masih memiliki kamar terkait).
* **Manajemen Data Master Kamar (CRUD)**:
    * Menambah data kamar baru untuk asrama tertentu, dengan nomor kamar dan kapasitas.
    * Melihat daftar kamar per asrama melalui dropdown.
    * Mengubah nomor dan/atau kapasitas kamar.
    * Menghapus data kamar (dengan validasi jika masih memiliki penghuni).
* **Manajemen Data Penghuni (CRUD)**:
    * Menambah data penghuni baru ke kamar tertentu, termasuk NIM, nama, dan fakultas.
    * Melihat daftar penghuni per kamar.
    * Mengubah data detail penghuni.
    * Menghapus data penghuni dari kamar.
* **Fitur Pindah Kamar**:
    * Memindahkan penghuni dari satu kamar ke kamar lain, baik di dalam asrama yang sama maupun ke asrama yang berbeda, dengan validasi kapasitas kamar tujuan.
* **Riwayat Aktivitas**:
    * Pencatatan otomatis setiap perubahan data (INSERT, UPDATE, DELETE) untuk:
        * Data Penghuni
        * Data Asrama
        * Data Kamar
    * Layar terpisah untuk melihat masing-masing riwayat aktivitas dengan detail seperti waktu, aksi, pengguna yang melakukan, dan keterangan.

## Teknologi yang Digunakan
* **Bahasa Pemrograman**: Python 3.x
* **GUI Framework**: Tkinter (modul standar Python)
* **Database**: MySQL Server
* **Konektor Database Python**: `mysql-connector-python`
* **Manajemen Gambar**: `Pillow` (PIL Fork)
* **Manajemen Konfigurasi**: `python-dotenv`

## Persyaratan Sistem
* Python 3.6 atau lebih tinggi.
* MySQL Server yang berjalan dan dapat diakses.
* Pustaka Python: `Pillow`, `mysql-connector-python`, `python-dotenv`.

## Instalasi & Setup

1.  **Clone Repository (Jika Ada)**:
    ```bash
    git clone [URL_REPOSITORY_ANDA]
    cd [NAMA_DIREKTORI_PROYEK]
    ```

2.  **Instal Dependensi Python**:
    Pastikan Anda memiliki `pip` terinstal. Buka terminal atau command prompt di direktori proyek dan jalankan:
    ```bash
    pip install Pillow mysql-connector-python python-dotenv
    ```

3.  **Setup Database MySQL**:
    * Pastikan MySQL server Anda sudah berjalan.
    * Buat sebuah database baru di MySQL. Anda dapat menggunakan nama seperti `asrama_db_mysql`.
    * Aplikasi ini akan mencoba membuat tabel, view, trigger, dan stored procedure yang diperlukan secara otomatis saat pertama kali dijalankan jika database sudah ada.
    * Sebagai alternatif, Anda dapat menjalankan skrip DDL SQL yang disediakan (misalnya, dalam file `sql_ddl_asrama_lengkap_v2.sql`) secara manual menggunakan tool manajemen database MySQL (seperti phpMyAdmin, MySQL Workbench, HeidiSQL, atau DBeaver).

4.  **Konfigurasi Environment Database**:
    * Buat file bernama `.env` di direktori root proyek Anda.
    * Isi file `.env` dengan detail koneksi database Anda, contoh:
        ```env
        DB_HOST=localhost
        DB_USER=root
        DB_PASSWORD=password_database_anda
        DB_NAME=asrama_db_mysql
        ```
    * Ganti `password_database_anda` dengan password pengguna MySQL Anda. Sesuaikan `DB_HOST`, `DB_USER`, dan `DB_NAME` jika berbeda.

## Cara Menjalankan Aplikasi

1.  Pastikan semua langkah instalasi dan setup telah selesai.
2.  Buka terminal atau command prompt.
3.  Navigasikan ke direktori root proyek Anda.
4.  Jalankan file Python utama aplikasi (misalnya, `asrama_oop_mysql_sp_view_configured_final.py` atau `main.py`):
    ```bash
    python nama_file_utama.py
    ```
    Ganti `nama_file_utama.py` dengan nama file skrip Python utama Anda.

5.  Jendela aplikasi akan muncul, dimulai dengan layar Login.

## Pengguna Admin Default
Saat aplikasi pertama kali dijalankan dan tabel `PenggunaAplikasi` masih kosong, sebuah akun admin default akan dibuat secara otomatis untuk memudahkan akses awal:
* **Username**: `admin`
* **Password**: `adminpassword`

**Penting**: Sangat disarankan untuk mengubah password admin default ini sesegera mungkin setelah login pertama kali demi keamanan sistem. (Catatan: Fitur ubah password pengguna mungkin perlu diimplementasikan secara terpisah jika belum ada).

## Struktur Proyek (Contoh)

.
├── assets/
│   └── um.png         # Gambar latar belakang
├── sql_ddl_asrama_lengkap_v2.sql # Skrip DDL untuk setup database
├── asrama_oop_mysql_sp_view_configured_final.py # File Python utama aplikasi
├── tombol.py          # Modul untuk membuat tombol kustom (jika ada)
├── .env               # File konfigurasi environment (JANGAN DI-COMMIT KE REPOSITORY PUBLIK)
└── README.md          # File ini


## Catatan Keamanan Mengenai Password
**PERHATIAN SANGAT PENTING!**
Versi aplikasi ini, sesuai dengan permintaan pengembangan, saat ini menyimpan dan membandingkan password pengguna (termasuk akun admin default) sebagai **teks biasa** di dalam database.

**Ini adalah praktik yang SANGAT TIDAK AMAN dan TIDAK DIREKOMENDASIKAN untuk aplikasi yang akan digunakan di lingkungan produksi atau yang menangani data sensitif.**

Untuk aplikasi nyata, implementasikan mekanisme penyimpanan password yang aman:
1.  **Hashing**: Gunakan algoritma hashing kriptografi yang kuat seperti bcrypt, scrypt, atau Argon2. SHA-256 (yang mungkin pernah digunakan sebelumnya) lebih baik dari teks biasa, tetapi algoritma yang lebih modern dan dirancang khusus untuk password lebih disarankan.
2.  **Salting**: Tambahkan *salt* (nilai acak unik) untuk setiap password sebelum di-hash. Ini mencegah serangan tabel pelangi (rainbow table attacks).
3.  Saat login, hash password yang dimasukkan pengguna (dengan salt yang sama) dan bandingkan hash tersebut dengan hash yang tersimpan di database.

## Troubleshooting Umum
* **Tidak Bisa Login / Pesan Error Login**:
    * Pastikan username dan password benar (case-sensitive).
    * Coba akun admin default jika baru pertama kali atau lupa.
    * Pastikan server MySQL berjalan dan konfigurasi di `.env` benar.
* **Error "Incorrect number of arguments for PROCEDURE..."**:
    * Pastikan definisi Stored Procedure di database MySQL Anda (terutama parameter IN dan bagaimana parameter OUT dikembalikan/di-SELECT) sesuai dengan cara pemanggilan di kode Python (`DatabaseService`).
* **Aplikasi Tidak Menampilkan Data / Tombol Tidak Berfungsi**:
    * Periksa koneksi database dan log konsol Python untuk pesan error.
    * Pastikan skema database (tabel, view, SP, trigger) telah terinisialisasi dengan benar.
* **Gambar Latar Belakang Tidak Muncul**:
    * Pastikan file gambar ada di direktori `assets/` dan nama file di kode sudah benar.
    * Pastikan pustaka Pillow terinstal.

---
Semoga README ini memberikan gambaran yang jelas tentang Aplikasi Manajemen Asrama Anda!
