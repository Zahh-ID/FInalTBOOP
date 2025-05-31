from .base_screen import BaseScreen
from tombol import tbl
class MainMenuScreen(BaseScreen):
    def setup_ui(self):
        self.create_canvas_text(50, 300, text="MANAJEMEN\nSISTEM\nASRAMA", fill="#F47B07", font=("Cooper Black", 50, "bold"), anchor="w")
        tbl(self.canvas, 700, 180, 300, 100, 20, 20, 90, 180, 270, 360, "#F47B07", "Masuk", self.screen_manager.show_asrama_selection)
        tbl(self.canvas, 700, 300, 300, 100, 20, 20, 90, 180, 270, 360, "#4682B4", "Riwayat Aktivitas", self.screen_manager.show_riwayat_utama_screen) # Diubah ke RiwayatUtamaScreen
        tbl(self.canvas, 700, 420, 300, 100, 20, 20, 90, 180, 270, 360, "red", "Keluar", self.app_instance.quit)
