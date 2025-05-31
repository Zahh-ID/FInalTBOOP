from .base_screen import BaseScreen
from tkinter import StringVar, ttk, Entry,messagebox
import tkinter as tk
from tombol import tbl
class UpdateDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, nomor_kamar): # nomor_kamar
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context
        self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.nomor_kamar=nomor_kamar # Simpan nomor_kamar
        self.selected_mahasiswa_nim_original=None; self.nim_baru_entry=None; self.nama_baru_entry=None
        self.fakultas_baru_pilihan=StringVar(); self.plh_mahasiswa_var=StringVar(); self.data_lengkap_mahasiswa_cache=[]; self.fakultas_map={}
    def setup_ui(self):
        self.create_canvas_text(560,50,text=f"Ubah Data Kamar {self.nomor_kamar} Asrama {self.asrama_nama}",fill="#F4FEFF",font=("Cooper Black",20,"bold"))
        opsi_display_db,self.data_lengkap_mahasiswa_cache=self.db_service.get_penghuni_in_kamar(self.nomor_kamar,self.asrama_id)
        self.create_canvas_text(460, 110, text="Pilih Mahasiswa (NIM - Nama)", fill="#F4FEFF", font=("Arial", 12, "bold"))
        m_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.plh_mahasiswa_var,font=("Arial",15),state="readonly",values=opsi_display_db,width=34))
        m_dd.place(x=350,y=120);m_dd.bind("<<ComboboxSelected>>",self._on_mahasiswa_selected)
        self.create_canvas_text(500, 178, text="NIM Baru (Kosongkan jika tidak diubah)", fill="#F4FEFF", font=("Arial", 12, "bold"))
        self.nim_baru_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF"));self.nim_baru_entry.place(x=350,y=190)
        self.create_canvas_text(510, 258, text="Nama Baru (Kosongkan jika tidak diubah)", fill="#F4FEFF", font=("Arial", 12, "bold"))
        self.nama_baru_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF"));self.nama_baru_entry.place(x=350,y=270)
        self.create_canvas_text(405, 340, text="Fakultas Baru", fill="#F4FEFF", font=("Arial", 12, "bold"))
        fakultas_db=self.db_service.get_all_fakultas();fakultas_display_list=[""]
        if fakultas_db:
            for fak in fakultas_db:self.fakultas_map[fak['nama_fakultas']]=fak['fakultas_id'];fakultas_display_list.append(fak['nama_fakultas'])
        f_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.fakultas_baru_pilihan,values=fakultas_display_list,width=29,font=("Arial",18),state="readonly"))
        f_dd.place(x=350,y=350)
        if opsi_display_db and not opsi_display_db[0].startswith("Info:")and not opsi_display_db[0].startswith("Kesalahan:"):
            self.plh_mahasiswa_var.set(opsi_display_db[0]);self._on_mahasiswa_selected()
        elif opsi_display_db and(opsi_display_db[0].startswith("Info:")or opsi_display_db[0].startswith("Kesalahan:")):self.plh_mahasiswa_var.set(opsi_display_db[0])
        else:
            self.plh_mahasiswa_var.set("Tidak ada data penghuni.")
            if self.nim_baru_entry:self.nim_baru_entry.delete(0,tk.END)
            if self.nama_baru_entry:self.nama_baru_entry.delete(0,tk.END)
            self.fakultas_baru_pilihan.set("")
        tbl(self.canvas,300,430,200,70,20,20,90,180,270,360,"#F47B07","Ubah",self._update_data_action)
        tbl(self.canvas,600,430,200,70,20,20,90,180,270,360,"red","Batal",lambda:self.screen_manager.show_kamar_detail(self.nomor_kamar))
    def _get_nim_from_selection(self,s):return s.split(" - ")[0]if" - "in s else None
    def _on_mahasiswa_selected(self,e=None):
        if not all([self.nim_baru_entry,self.nama_baru_entry,hasattr(self.fakultas_baru_pilihan,'set')]):return
        s_disp_s=self.plh_mahasiswa_var.get();nim_orig=self._get_nim_from_selection(s_disp_s)
        self.selected_mahasiswa_nim_original=nim_orig
        self.nim_baru_entry.delete(0,tk.END);self.nama_baru_entry.delete(0,tk.END);self.fakultas_baru_pilihan.set("")
        if nim_orig and self.data_lengkap_mahasiswa_cache:
            for d_mhs in self.data_lengkap_mahasiswa_cache:
                if str(d_mhs['nim'])==str(nim_orig):
                    self.nama_baru_entry.insert(0,str(d_mhs['nama_penghuni']))
                    self.fakultas_baru_pilihan.set(str(d_mhs.get('fakultas'))if d_mhs.get('fakultas')else"")
                    break
    def _update_data_action(self):
        if not self.selected_mahasiswa_nim_original:messagebox.showwarning("Peringatan","Pilih mahasiswa.");return
        nim_n=self.nim_baru_entry.get().strip();nama_n=self.nama_baru_entry.get().strip();fak_n=self.fakultas_baru_pilihan.get()
        user_aksi = self.app_instance.current_username
        
        if nim_n and not nim_n.isdigit():
            messagebox.showerror("Kesalahan Input", "NIM baru harus berupa angka.")
            return
        
        current_nama_e_v=self.nama_baru_entry.get()
        if not nama_n and current_nama_e_v.strip() != "": 
             messagebox.showwarning("Input Tidak Valid","Nama baru tidak boleh dikosongkan jika field diisi.")
             return
        
        update_status = self.db_service.update_penghuni(self.selected_mahasiswa_nim_original,nim_n,nama_n,fak_n if fak_n else None, user_aksi)
        
        if update_status == "SUCCESS_DATA_CHANGED":
            self.screen_manager.show_kamar_detail(self.nomor_kamar)