from .base_screen import BaseScreen
from tkinter import StringVar, ttk, messagebox
from tombol import tbl
class PindahKamarScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, nomor_kamar_asal): # nomor_kamar_asal
        super().__init__(screen_manager, db_service)
        self.nomor_kamar_asal=nomor_kamar_asal # Simpan nomor_kamar_asal
        self.asrama_id_asal=screen_manager.current_asrama_id_context
        self.asrama_nama_asal=screen_manager.current_asrama_nama_context
        self.selected_nim_var=StringVar(); self.selected_asrama_tujuan_var=StringVar(); self.selected_kamar_tujuan_var=StringVar()
        self.penghuni_asal_options=[]; self.asrama_tujuan_options_map={}; self.kamar_tujuan_options_map={}
    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth/2,50,text=f"Pindah Kamar dari {self.asrama_nama_asal} - Kamar {self.nomor_kamar_asal}",fill="#F4FEFF",font=("Cooper Black",20,"bold"))
        y_curr=110;lbl_w=150;dd_w_char=30;est_dd_px_w=dd_w_char*7;form_w=lbl_w+10+est_dd_px_w
        x_lbl=(self.app_instance.appwidth-form_w)/2;x_dd=x_lbl+lbl_w+10
        self.create_canvas_text(x_lbl,y_curr+10,text="Pilih Penghuni:",fill="#F4FEFF",font=("Arial",12,"bold"),anchor="w")
        opsi_p,_=self.db_service.get_penghuni_in_kamar(self.nomor_kamar_asal,self.asrama_id_asal)
        self.penghuni_asal_options=opsi_p if not(opsi_p and opsi_p[0].startswith("Info:"))else["Tidak ada penghuni"]
        p_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.selected_nim_var,values=self.penghuni_asal_options,width=dd_w_char,state="readonly",font=("Arial",14)))
        p_dd.place(x=x_dd,y=y_curr);y_curr+=50
        if self.penghuni_asal_options and self.penghuni_asal_options[0]!="Tidak ada penghuni":self.selected_nim_var.set(self.penghuni_asal_options[0])
        
        self.create_canvas_text(x_lbl,y_curr+10,text="Asrama Tujuan:",fill="#F4FEFF",font=("Arial",12,"bold"),anchor="w")
        all_a=self.db_service.get_all_asrama();
        self.asrama_tujuan_options_map={a['nama_asrama']:a['asrama_id']for a in all_a}
        a_disp_opts=list(self.asrama_tujuan_options_map.keys())
        a_t_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.selected_asrama_tujuan_var,values=a_disp_opts,width=dd_w_char,state="readonly",font=("Arial",14)))
        a_t_dd.place(x=x_dd,y=y_curr);a_t_dd.bind("<<ComboboxSelected>>",self._on_asrama_tujuan_selected);y_curr+=50
        
        self.create_canvas_text(x_lbl,y_curr+10,text="Kamar Tujuan:",fill="#F4FEFF",font=("Arial",12,"bold"),anchor="w")
        self.kamar_tujuan_dropdown=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.selected_kamar_tujuan_var,values=[],width=dd_w_char,state="disabled",font=("Arial",14)))
        self.kamar_tujuan_dropdown.place(x=x_dd,y=y_curr);y_curr+=70
        
        btn_w=200;x_btn_p=self.app_instance.appwidth/2-btn_w-10;x_btn_b=self.app_instance.appwidth/2+10
        tbl(self.canvas,x_btn_p,y_curr,btn_w,50,10,10,90,180,270,360,"blue","Pindahkan",self._proses_pindah_kamar)
        tbl(self.canvas,x_btn_b,y_curr,btn_w,50,10,10,90,180,270,360,"red","Batal",lambda:self.screen_manager.show_kamar_detail(self.nomor_kamar_asal))

    def _on_asrama_tujuan_selected(self,e=None):
        nama_a=self.selected_asrama_tujuan_var.get()
        id_a_t=self.asrama_tujuan_options_map.get(nama_a)
        self.kamar_tujuan_options_map = {} # Reset map kamar
        if id_a_t:
            kamars=self.db_service.get_all_kamar_in_asrama(id_a_t)
            kamar_display_options = []
            for k in kamars:
                # Pastikan kamar tujuan tidak sama dengan kamar asal jika asramanya sama
                if not (id_a_t == self.asrama_id_asal and k['nomor_kamar'] == self.nomor_kamar_asal):
                    display_text = f"Kamar {k['nomor_kamar']} (Kapasitas: {k['kapasitas']})"
                    self.kamar_tujuan_options_map[display_text] = k['nomor_kamar']
                    kamar_display_options.append(display_text)

            self.kamar_tujuan_dropdown['values']=kamar_display_options
            if kamar_display_options:
                self.selected_kamar_tujuan_var.set(kamar_display_options[0])
                self.kamar_tujuan_dropdown['state']="readonly"
            else:
                self.selected_kamar_tujuan_var.set("Tidak ada kamar tersedia")
                self.kamar_tujuan_dropdown['state']="disabled"
        else:
            self.kamar_tujuan_dropdown['values']=[]
            self.selected_kamar_tujuan_var.set("")
            self.kamar_tujuan_dropdown['state']="disabled"

    def _proses_pindah_kamar(self):
        nim_s=self.selected_nim_var.get()
        if not nim_s or nim_s=="Tidak ada penghuni":
            messagebox.showwarning("Peringatan","Pilih penghuni yang akan dipindahkan.", parent=self.app_instance.window)
            return
        nim_m=nim_s.split(" - ")[0]
        
        nama_a_t=self.selected_asrama_tujuan_var.get()
        id_a_t=self.asrama_tujuan_options_map.get(nama_a_t)
        
        kamar_tujuan_display = self.selected_kamar_tujuan_var.get()
        no_k_t = self.kamar_tujuan_options_map.get(kamar_tujuan_display)

        user_aksi = self.app_instance.current_username
        
        if not id_a_t or not no_k_t or kamar_tujuan_display == "Tidak ada kamar tersedia":
            messagebox.showwarning("Peringatan","Pilih asrama & kamar tujuan yang valid.", parent=self.app_instance.window)
            return
        
        succ,msg=self.db_service.pindah_kamar_penghuni(nim_m,no_k_t,id_a_t, user_aksi)
        if succ:
            # Pesan sukses sudah ditampilkan oleh db_service, cukup kembali
            self.screen_manager.show_kamar_detail(self.nomor_kamar_asal)
        # Pesan error juga sudah ditangani oleh db_service
