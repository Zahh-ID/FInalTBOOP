from tkinter import messagebox

# Contoh di screen_manager.py
from screens import (
    LoginScreen,
    SignUpScreen,
    MainMenuScreen,
    AsramaSelectionScreen,
    AddAsramaScreen,
    UpdateAsramaScreen,
    KamarListScreen,
    AddKamarScreen,
    UpdateKamarScreen,
    KamarDetailScreen,
    InsertDataScreen,
    UpdateDataScreen,
    DeleteDataScreen,
    PindahKamarScreen,
    RiwayatUtamaScreen,
    RiwayatPenghuniScreen,
    RiwayatAsramaScreen,
    RiwayatKamarScreen,
)
from tkinter import messagebox

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
