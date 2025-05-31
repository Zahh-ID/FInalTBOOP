from .base_screen import BaseScreen
from tkinter import StringVar, ttk, messagebox
from tombol import tbl
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
        self.create_canvas_text(520, 290, text="Pilih Mahasiswa (NIM - Nama) untuk Dihapus", fill="#F4FEFF", font=("Arial", 12, "bold"))
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
