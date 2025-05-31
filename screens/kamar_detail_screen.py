from tkinter import ttk
from .base_screen import BaseScreen
from tombol import tbl
import tkinter as tk

class KamarDetailScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id): 
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context
        self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.nomor_kamar=kamar_id 
        self.penghuni_treeview=None; self.treeview_scrollbar=None
    def setup_ui(self):
        style=ttk.Style(); style.configure("Custom.Treeview", background="#E1E1E1", fieldbackground="#FFFFFF", foreground="black")
        style.configure("Custom.Treeview.Heading", background="yellow", foreground="black", font=('Arial',10,'bold'), relief="flat")
        style.map("Custom.Treeview.Heading", background=[('active','#FFD700')])
        self.create_canvas_text(self.app_instance.appwidth/2, 80, text=f"Asrama {self.asrama_nama} - Kamar {self.nomor_kamar}", fill="#000000", font=("Cooper Black",22,"bold"))
        info_text_x=self.app_instance.appwidth/2; info_text_y=120
        jml_penghuni=self.db_service.get_jumlah_penghuni(self.nomor_kamar,self.asrama_id)
        kapasitas=self.db_service.get_kapasitas_kamar(self.nomor_kamar,self.asrama_id)
        self.create_canvas_text(info_text_x,info_text_y, text=f"Data Penghuni ({jml_penghuni}/{kapasitas})", fill="#F4F0FF", font=("Cooper Black",18,"bold"))
        table_x=50; table_y=info_text_y+20+20; table_container_width=self.app_instance.appwidth-(2*50)
        scrollbar_width=20; treeview_actual_width=table_container_width-scrollbar_width
        treeview_display_height=self.app_instance.appheight-table_y-70-120
        columns=("no","nim","nama","fakultas"); self.penghuni_treeview=ttk.Treeview(self.canvas,columns=columns,show='headings',style="Custom.Treeview")
        for col,txt,w,anc in [("no","No.",0.05,tk.CENTER),("nim","NIM",0.25,tk.W),("nama","Nama Mahasiswa",0.40,tk.W),("fakultas","Fakultas",0.30,tk.W)]:
            self.penghuni_treeview.heading(col,text=txt); self.penghuni_treeview.column(col,width=int(treeview_actual_width*w),anchor=anc,stretch=tk.YES if col!="no" else tk.NO)
        self.treeview_scrollbar=ttk.Scrollbar(self.canvas,orient="vertical",command=self.penghuni_treeview.yview)
        self.penghuni_treeview.configure(yscrollcommand=self.treeview_scrollbar.set)
        _,daftar_penghuni=self.db_service.get_penghuni_in_kamar(self.nomor_kamar,self.asrama_id)
        for i in self.penghuni_treeview.get_children(): self.penghuni_treeview.delete(i)
        if daftar_penghuni and not (isinstance(daftar_penghuni[0],str) and daftar_penghuni[0].startswith("Info:")):
            for i,p in enumerate(daftar_penghuni): self.penghuni_treeview.insert("","end",values=(i+1,p['nim'],p['nama_penghuni'],p.get('fakultas') or "N/A")) 
        else:
            if not self.penghuni_treeview.get_children(): self.penghuni_treeview.insert("","end",values=("","Belum ada penghuni.","",""))
        self.add_widget(self.penghuni_treeview); self.add_widget(self.treeview_scrollbar)
        self.canvas.create_window(table_x,table_y,anchor=tk.NW,window=self.penghuni_treeview,width=treeview_actual_width,height=treeview_display_height)
        self.canvas.create_window(table_x+treeview_actual_width,table_y,anchor=tk.NW,window=self.treeview_scrollbar,height=treeview_display_height)
        y_buttons=15; btn_width=150; btn_spacing=273; current_x=50
        actions=[("Kembali","red",lambda:self.screen_manager.show_kamar_list(self.asrama_id,self.asrama_nama)),
                 ("Tambah Data","#F47B07",lambda:self.screen_manager.show_insert_data_form(self.nomor_kamar)),
                 ("Ubah Data","#F47B07",lambda:self.screen_manager.show_update_data_form(self.nomor_kamar)),
                 ("Hapus Data","#F47B07",lambda:self.screen_manager.show_delete_data_form(self.nomor_kamar))]
        for i, (text,color,cmd) in enumerate(actions):
            tbl(self.canvas,current_x + (i*btn_spacing),y_buttons,btn_width,50,10,10,90,180,270,360,color,text,cmd)
        y_pindah=table_y+treeview_display_height+25; lebar_pindah=200; x_pindah=(self.app_instance.appwidth/2)-(lebar_pindah/2)
        tbl(self.canvas,x_pindah,y_pindah,lebar_pindah,50,10,10,90,180,270,360,"blue","Pindah Kamar",lambda:self.screen_manager.show_pindah_kamar_form(self.nomor_kamar))

    def clear_screen_elements(self): super().clear_screen_elements(); self.penghuni_treeview=None; self.treeview_scrollbar=None
