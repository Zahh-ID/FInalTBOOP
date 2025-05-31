from .base_screen import BaseScreen
from tkinter import *
from tkinter import messagebox
from tombol import tbl
class SignUpScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.username_var = StringVar()
        self.password_var = StringVar()
        self.confirm_password_var = StringVar()
        self.username_entry = None
        self.password_entry = None
        self.confirm_password_entry = None

    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 150, 
                                text="REGISTRASI PENGGUNA BARU", 
                                fill="#F4FEFF", font=("Cooper Black", 30, "bold"))
        
        y_pos = 230
        self.create_canvas_text(self.app_instance.appwidth / 2 - 200, y_pos + 10, text="Username Baru:", 
                                fill="#F4FEFF", font=("Arial", 12, "bold"), anchor="e")
        self.username_entry = self.add_widget(Entry(self.canvas, textvariable=self.username_var, 
                                                       width=25, font=("Arial", 12)))
        self.username_entry.place(x=self.app_instance.appwidth / 2 - 190, y=y_pos)
        y_pos += 40

        self.create_canvas_text(self.app_instance.appwidth / 2 - 200, y_pos + 10, text="Password Baru:", 
                                fill="#F4FEFF", font=("Arial", 12, "bold"), anchor="e")
        self.password_entry = self.add_widget(Entry(self.canvas, textvariable=self.password_var, 
                                                       width=25, font=("Arial", 12), show="*"))
        self.password_entry.place(x=self.app_instance.appwidth / 2 - 190, y=y_pos)
        y_pos += 40

        self.create_canvas_text(self.app_instance.appwidth / 2 - 200, y_pos + 10, text="Konfirmasi Password:", 
                                fill="#F4FEFF", font=("Arial", 12, "bold"), anchor="e")
        self.confirm_password_entry = self.add_widget(Entry(self.canvas, textvariable=self.confirm_password_var, 
                                                       width=25, font=("Arial", 12), show="*"))
        self.confirm_password_entry.place(x=self.app_instance.appwidth / 2 - 190, y=y_pos)
        y_pos += 60

        tbl(self.canvas, self.app_instance.appwidth / 2 - 220, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "#4CAF50", "Daftar", self._attempt_signup) 
        tbl(self.canvas, self.app_instance.appwidth / 2 + 20, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "gray", "Kembali ke Login", self.screen_manager.show_login_screen)

    def _attempt_signup(self):
        username = self.username_var.get()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()

        if not username or not password or not confirm_password:
            messagebox.showerror("Input Tidak Valid", "Semua field harus diisi.", parent=self.app_instance.window)
            return
        if password != confirm_password:
            messagebox.showerror("Password Tidak Cocok", "Password dan konfirmasi password tidak sama.", parent=self.app_instance.window)
            return
        if len(password) < 6: 
            messagebox.showerror("Password Lemah", "Password minimal harus 6 karakter.", parent=self.app_instance.window)
            return

        success, message = self.db_service.register_user(username, password)
        if success:
            messagebox.showinfo("Registrasi Berhasil", message, parent=self.app_instance.window) 
            self.screen_manager.show_login_screen()
        else:
            if message: 
                messagebox.showerror("Gagal Registrasi", message, parent=self.app_instance.window)
            else: 
                messagebox.showerror("Gagal Registrasi", "Terjadi kesalahan tidak diketahui.", parent=self.app_instance.window)
