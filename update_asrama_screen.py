

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
