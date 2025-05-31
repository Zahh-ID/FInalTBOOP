from tkinter import StringVar, messagebox, Entry
from .base_screen import BaseScreen
from tombol import tbl
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
