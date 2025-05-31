from .base_screen import BaseScreen
from tkinter import StringVar, Entry, messagebox
from tombol import tbl
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