from .base_screen import BaseScreen
from tkinter import ttk
import tkinter as tk
from tombol import tbl
class RiwayatPenghuniScreen(BaseScreen): # Sebelumnya RiwayatAktivitasScreen
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.log_treeview=None; self.log_scrollbar=None
    def setup_ui(self):
        style=ttk.Style(); style.configure("Riwayat.Treeview",background="#F0F0F0",fieldbackground="#FFFFFF",foreground="black",rowheight=25)
        style.configure("Riwayat.Treeview.Heading",background="#BFBFBF",foreground="black",font=('Arial',10,'bold'),relief="flat")
        style.map("Riwayat.Treeview.Heading",background=[('active','#A0A0A0')])
        
        y_buttons = 15
        tbl(self.canvas, 50, y_buttons, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali", self.screen_manager.show_riwayat_utama_screen)
        
        self.create_canvas_text(self.app_instance.appwidth/2, 50,text="Riwayat Aktivitas Penghuni",fill="#000000",font=("Cooper Black",24,"bold"))

        table_padding_horizontal = 30
        table_padding_top = y_buttons + 50 + 20 
        table_padding_bottom = 20 
        
        table_x = table_padding_horizontal
        table_y = table_padding_top
        
        table_container_width = self.app_instance.appwidth-(2*table_padding_horizontal);scr_w=20;tree_w=table_container_width-scr_w 
        tree_h=self.app_instance.appheight-table_y-table_padding_bottom - 50 

        cols=("log_id","waktu","aksi","nim", "user_aksi", "nama","detail_kamar","keterangan") 
        self.log_treeview=ttk.Treeview(self.canvas,columns=cols,show='headings',style="Riwayat.Treeview")
        hdrs={"log_id":"ID","waktu":"Waktu","aksi":"Aksi","nim":"NIM", "user_aksi":"User", "nama":"Nama Terkait","detail_kamar":"Detail Perubahan","keterangan":"Keterangan"}
        cols_cfg={"log_id":{"w":0.04,"anc":tk.CENTER,"st":tk.NO},"waktu":{"w":0.15,"anc":tk.W,"st":tk.YES},"aksi":{"w":0.07,"anc":tk.W,"st":tk.YES},
                  "nim":{"w":0.10,"anc":tk.W,"st":tk.YES}, "user_aksi":{"w":0.10,"anc":tk.W,"st":tk.YES}, "nama":{"w":0.15,"anc":tk.W,"st":tk.YES},
                  "detail_kamar":{"w":0.22,"anc":tk.W,"st":tk.YES},"keterangan":{"w":0.17,"anc":tk.W,"st":tk.YES}}
        for c,t in hdrs.items(): self.log_treeview.heading(c,text=t); self.log_treeview.column(c,width=int(tree_w*cols_cfg[c]["w"]),anchor=cols_cfg[c]["anc"],stretch=cols_cfg[c]["st"])
        self.log_scrollbar=ttk.Scrollbar(self.canvas,orient="vertical",command=self.log_treeview.yview); self.log_treeview.configure(yscrollcommand=self.log_scrollbar.set)
        logs=self.db_service.get_audit_log_penghuni(limit=200)
        for i in self.log_treeview.get_children(): self.log_treeview.delete(i)
        if logs:
            for log in logs: self.log_treeview.insert("","end",values=(
                log['log_id'],log['waktu_aksi_formatted'],log['aksi'],log['nim'],
                log.get('user_aksi', 'N/A'), 
                log['nama_terkait'],log['detail_perubahan'],log['keterangan_tambahan']
                ))
        else: self.log_treeview.insert("","end",values=("","Belum ada riwayat.","","","","","",""))
        self.add_widget(self.log_treeview); self.add_widget(self.log_scrollbar)
        self.canvas.create_window(table_x,table_y,anchor=tk.NW,window=self.log_treeview,width=tree_w,height=tree_h)
        self.canvas.create_window(table_x+tree_w,table_y,anchor=tk.NW,window=self.log_scrollbar,height=tree_h) # Disesuaikan dengan tbl_y
        
    def clear_screen_elements(self): super().clear_screen_elements(); self.log_treeview=None; self.log_scrollbar=None
