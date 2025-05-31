from .base_screen import BaseScreen
from tkinter import Entry, ttk, messagebox, StringVar
from tombol import tbl
class InsertDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, nomor_kamar): # nomor_kamar
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context
        self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.nomor_kamar=nomor_kamar # Simpan nomor_kamar
        self.nim_entry=None; self.nama_entry=None; self.fakultas_pilihan=StringVar()
        self.fakultas_map={}
    def setup_ui(self):
        self.create_canvas_text(560,50,text=f"Insert Data Kamar {self.nomor_kamar} Asrama {self.asrama_nama}",fill="#F4F0FF",font=("Cooper Black",24,"bold"))
        self.create_canvas_text(365,188,text="NIM",fill="#F4FEFF",font=("Arial",12,"bold"))
        self.nim_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF")); self.nim_entry.place(x=350,y=200)
        self.create_canvas_text(374,270,text="Nama",fill="#F4FEFF",font=("Arial",12,"bold"))
        self.nama_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF")); self.nama_entry.place(x=350,y=280)
        self.create_canvas_text(385,340,text="Fakultas",fill="#F4FEFF",font=("Arial",12,"bold"))
        fakultas_db=self.db_service.get_all_fakultas(); fakultas_display_list=[""]
        if fakultas_db:
            for fak in fakultas_db: self.fakultas_map[fak['nama_fakultas']]=fak['fakultas_id']; fakultas_display_list.append(fak['nama_fakultas'])
        self.fakultas_pilihan.set(fakultas_display_list[0])
        dropdown=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.fakultas_pilihan,values=fakultas_display_list,width=29,font=("Arial",18),state="readonly"))
        dropdown.place(x=350,y=360)
        tbl(self.canvas,300,430,200,70,20,20,90,180,270,360,"#F47B07","Simpan",self._save_data)
        tbl(self.canvas,600,430,200,70,20,20,90,180,270,360,"red","Batal",lambda:self.screen_manager.show_kamar_detail(self.nomor_kamar))
    def _save_data(self):
        nim=self.nim_entry.get(); nama=self.nama_entry.get(); nama_fakultas_terpilih=self.fakultas_pilihan.get()
        user_aksi = self.app_instance.current_username 
        if not nim or not nama: messagebox.showwarning("Input Tidak Lengkap","NIM dan Nama tidak boleh kosong."); return
        if nim and not nim.isdigit(): 
            messagebox.showerror("Kesalahan Input", "NIM harus berupa angka.")
            return
        if self.db_service.add_penghuni(nim,nama,nama_fakultas_terpilih if nama_fakultas_terpilih else None,self.nomor_kamar,self.asrama_id, user_aksi):
            self.screen_manager.show_kamar_detail(self.nomor_kamar)