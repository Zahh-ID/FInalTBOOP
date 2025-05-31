from .base_screen import BaseScreen
from tkinter import messagebox,StringVar, ttk
from tombol import tbl

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

        y_pos = 300
        self.create_canvas_text(self.app_instance.appwidth / 2 - 100, y_pos-17 , text="Pilih Asrama:", 
                                fill="#F4FEFF", font=("Arial", 16, "bold"), anchor="e")
        self.asrama_dropdown = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.selected_asrama_nama_var, 
                                                            width=40, font=("Arial", 14), state="readonly"))
        self.asrama_dropdown.place(x=self.app_instance.appwidth / 2 -230, y=y_pos)
        self._populate_asrama_dropdown() 
        y_pos += 70

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
        
        tbl(self.canvas, 460, 550, 150, 50, 10, 10, 90, 180, 270, 360, 
            "red", "Kembali", self.screen_manager.show_main_menu)

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
