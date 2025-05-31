from .base_screen import BaseScreen
from tombol import tbl
from tkinter import messagebox,StringVar, ttk
class KamarListScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, asrama_id, asrama_nama):
        super().__init__(screen_manager, db_service)
        self.asrama_id = asrama_id
        self.asrama_nama = asrama_nama
        self.kamar_dropdown_var = StringVar()
        self.kamar_options_map = {}
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

        y_pos = 300
        self.create_canvas_text(self.app_instance.appwidth / 2 - 110, y_pos - 17, text="Pilih Kamar:", 
                                fill="#F4FEFF", font=("Arial", 16, "bold"), anchor="e")
        self.kamar_dropdown = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.kamar_dropdown_var, 
                                                            width=40, font=("Arial", 14), state="readonly"))
        self.kamar_dropdown.place(x=self.app_instance.appwidth / 2 - 230, y=y_pos)
        self._populate_kamar_dropdown()
        y_pos += 70

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
        
        tbl(self.canvas, 445, 550, 180, 50, 10, 10, 90, 180, 270, 360, 
            "red", "Kembali ke Asrama", self.screen_manager.show_asrama_selection)

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
