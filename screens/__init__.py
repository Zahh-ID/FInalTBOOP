# screens/__init__.py

# Mengimpor kelas-kelas layar agar bisa diakses langsung dari package 'screens'
from .base_screen import BaseScreen
from .login_screen import LoginScreen
from .signup_screen import SignUpScreen
from .main_menu_screen import MainMenuScreen
from .asrama_selection_screen import AsramaSelectionScreen
from .kamar_list_screen import KamarListScreen
from .kamar_detail_screen import KamarDetailScreen
from .insert_data_screen import InsertDataScreen
from .update_data_screen import UpdateDataScreen
from .delete_data_screen import DeleteDataScreen
from .pindah_kamar_screen import PindahKamarScreen
from .add_asrama_screen import AddAsramaScreen
from .add_kamar_screen import AddKamarScreen
from .riwayat_utama_screen import RiwayatUtamaScreen
from .riwayat_penghuni_screen import RiwayatPenghuniScreen
from .riwayat_asrama_screen import RiwayatAsramaScreen
from .riwayat_kamar_screen import RiwayatKamarScreen
from .update_asrama_screen import UpdateAsramaScreen
from .update_kamar_screen import UpdateKamarScreen


# Anda bisa juga mendefinisikan __all__ jika ingin mengontrol apa yang diimpor
# ketika seseorang melakukan 'from screens import *', meskipun ini kurang umum
# untuk kasus penggunaan seperti ini.
# Contoh:
# __all__ = [
#     "BaseScreen", "LoginScreen", "SignUpScreen", "MainMenuScreen",
#     "AsramaSelectionScreen", "KamarListScreen", "KamarDetailScreen",
#     "InsertDataScreen", "UpdateDataScreen", "DeleteDataScreen",
#     "PindahKamarScreen", "RiwayatAktivitasScreen", "UpdateAsramaScreen",
#     "UpdateKamarScreen"
# ]
