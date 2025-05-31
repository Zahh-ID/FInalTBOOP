from .base_screen import BaseScreen
from tkinter import ttk
from tombol import tbl
import tkinter as tk
class RiwayatKamarScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.log_treeview = None
        self.log_scrollbar = None

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Riwayat.Treeview", background="#F0F0F0", fieldbackground="#FFFFFF", foreground="black", rowheight=25)
        style.configure("Riwayat.Treeview.Heading", background="#BFBFBF", foreground="black", font=('Arial', 10, 'bold'), relief="flat")
        style.map("Riwayat.Treeview.Heading", background=[('active', '#A0A0A0')])

        y_buttons = 15
        tbl(self.canvas, 50, y_buttons, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali", self.screen_manager.show_riwayat_utama_screen)
        self.create_canvas_text(self.app_instance.appwidth / 2, 50, text="Riwayat Aktivitas Kamar", fill="#000000", font=("Cooper Black", 24, "bold"))

        table_padding_horizontal = 20
        table_padding_top = y_buttons + 50 + 20
        table_padding_bottom = 20
        table_x = table_padding_horizontal
        table_y = table_padding_top
        table_container_width = self.app_instance.appwidth - (2 * table_padding_horizontal)
        scrollbar_width = 20
        treeview_actual_width = table_container_width - scrollbar_width
        treeview_display_height = self.app_instance.appheight - table_y - table_padding_bottom - 50

        cols = ("log_id", "waktu", "aksi", "kamar_id", "no_kamar_lama", "no_kamar_baru", "asrama_lama", "asrama_baru", "kap_lama", "kap_baru", "user_aksi", "keterangan")
        self.log_treeview = ttk.Treeview(self.canvas, columns=cols, show='headings', style="Riwayat.Treeview")
        
        headers_config = {
            "log_id": {"text": "ID", "width": 0.03}, "waktu": {"text": "Waktu", "width": 0.12},
            "aksi": {"text": "Aksi", "width": 0.06}, "kamar_id": {"text": "ID Kamar", "width": 0.07},
            "no_kamar_lama": {"text": "No. Lama", "width": 0.07}, "no_kamar_baru": {"text": "No. Baru", "width": 0.07},
            "asrama_lama": {"text": "Asrama Lama", "width": 0.10}, "asrama_baru": {"text": "Asrama Baru", "width": 0.10},
            "kap_lama": {"text": "Kap. Lama", "width": 0.07}, "kap_baru": {"text": "Kap. Baru", "width": 0.07},
            "user_aksi": {"text": "User", "width": 0.08}, "keterangan": {"text": "Keterangan", "width": 0.16}
        }

        for col, config in headers_config.items():
            self.log_treeview.heading(col, text=config["text"])
            self.log_treeview.column(col, width=int(treeview_actual_width * config["width"]), anchor=tk.W, stretch=tk.YES)
        self.log_treeview.column("log_id", anchor=tk.CENTER)
        self.log_treeview.column("kamar_id", anchor=tk.CENTER)


        self.log_scrollbar = ttk.Scrollbar(self.canvas, orient="vertical", command=self.log_treeview.yview)
        self.log_treeview.configure(yscrollcommand=self.log_scrollbar.set)

        logs = self.db_service.get_audit_log_kamar(limit=200)
        for i in self.log_treeview.get_children(): self.log_treeview.delete(i)
        if logs:
            for log in logs:
                self.log_treeview.insert("", "end", values=(
                    log['log_id'], log['waktu_aksi_formatted'], log['aksi'],
                    log.get('kamar_id_internal_aksi', 'N/A'),
                    log.get('nomor_kamar_lama', 'N/A'), log.get('nomor_kamar_baru', 'N/A'),
                    log.get('nama_asrama_lama', 'N/A'), log.get('nama_asrama_baru', 'N/A'),
                    log.get('kapasitas_lama', 'N/A'), log.get('kapasitas_baru', 'N/A'),
                    log.get('user_aksi', 'N/A'),
                    log.get('keterangan_tambahan', '')
                ))
        else:
            self.log_treeview.insert("", "end", values=("", "Belum ada riwayat.", "", "", "", "", "", "", "", "", "", ""))

        self.add_widget(self.log_treeview)
        self.add_widget(self.log_scrollbar)
        self.canvas.create_window(table_x, table_y, anchor=tk.NW, window=self.log_treeview, width=treeview_actual_width, height=treeview_display_height)
        self.canvas.create_window(table_x + treeview_actual_width, table_y, anchor=tk.NW, window=self.log_scrollbar, height=treeview_display_height)

