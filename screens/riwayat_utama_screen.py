from .base_screen import BaseScreen
from tombol import tbl
class RiwayatUtamaScreen(BaseScreen):
    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 100, 
                                text="PILIH RIWAYAT AKTIVITAS", 
                                fill="#F4FEFF", font=("Cooper Black", 30, "bold"))
        
        y_pos = 200
        button_width = 300
        button_height = 70
        spacing = 20
        
        tbl(self.canvas, self.app_instance.appwidth / 2 - button_width / 2, y_pos, 
            button_width, button_height, 15, 15, 90, 180, 270, 360,
            "#17a2b8", "Riwayat Data Penghuni", self.screen_manager.show_riwayat_penghuni_screen)
        y_pos += button_height + spacing

        tbl(self.canvas, self.app_instance.appwidth / 2 - button_width / 2, y_pos, 
            button_width, button_height, 15, 15, 90, 180, 270, 360,
            "#17a2b8", "Riwayat Data Asrama", self.screen_manager.show_riwayat_asrama_screen)
        y_pos += button_height + spacing
        
        tbl(self.canvas, self.app_instance.appwidth / 2 - button_width / 2, y_pos, 
            button_width, button_height, 15, 15, 90, 180, 270, 360,
            "#17a2b8", "Riwayat Data Kamar", self.screen_manager.show_riwayat_kamar_screen)
        y_pos += button_height + spacing*2

        tbl(self.canvas, self.app_instance.appwidth / 2 - 100, y_pos, 
            200, 50, 10, 10, 90, 180, 270, 360,
            "gray", "Kembali ke Menu Utama", self.screen_manager.show_main_menu)