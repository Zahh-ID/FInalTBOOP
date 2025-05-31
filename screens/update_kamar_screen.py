from .base_screen import BaseScreen
from tkinter import StringVar, messagebox, Entry, ttk
from tombol import tbl

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
