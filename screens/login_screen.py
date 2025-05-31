from screens import BaseScreen
from tkinter import *
from tkinter import messagebox
from tombol import tbl
class LoginScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.username_var = StringVar()
        self.password_var = StringVar()
        self.username_entry = None
        self.password_entry = None

    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 150, 
                                text="LOGIN APLIKASI ASRAMA", 
                                fill="#F4FEFF", font=("Cooper Black", 30, "bold"))
        
        y_pos = 250
        self.create_canvas_text(self.app_instance.appwidth / 2 - 180, y_pos + 10, text="Username:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.username_entry = self.add_widget(Entry(self.canvas, textvariable=self.username_var, 
                                                       width=25, font=("Arial", 14)))
        self.username_entry.place(x=self.app_instance.appwidth / 2 - 170, y=y_pos)
        y_pos += 50

        self.create_canvas_text(self.app_instance.appwidth / 2 - 180, y_pos + 10, text="Password:", 
                                fill="#F4FEFF", font=("Arial", 14, "bold"), anchor="e")
        self.password_entry = self.add_widget(Entry(self.canvas, textvariable=self.password_var, 
                                                       width=25, font=("Arial", 14), show="*"))
        self.password_entry.place(x=self.app_instance.appwidth / 2 - 170, y=y_pos)
        y_pos += 70

        tbl(self.canvas, self.app_instance.appwidth / 2 - 220, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "#F47B07", "Login", self._attempt_login)
        tbl(self.canvas, self.app_instance.appwidth / 2 + 20, y_pos, 200, 50, 10, 10, 90, 180, 270, 360,
            "#4682B4", "Sign Up", self.screen_manager.show_signup_screen)

    def _attempt_login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showerror("Login Gagal", "Username dan password tidak boleh kosong.", parent=self.app_instance.window)
            return

        user_id, logged_in_username, status_message = self.db_service.login_user(username, password) 
        
        if user_id: 
            self.app_instance.current_user_id = user_id 
            self.app_instance.current_username = logged_in_username 
            self.screen_manager.logged_in_user_id = user_id 
            self.screen_manager.show_main_menu() 
        else:
            if status_message: 
                 messagebox.showerror("Login Gagal", status_message, parent=self.app_instance.window)
            else: 
                 messagebox.showerror("Login Gagal", "Terjadi kesalahan tidak diketahui saat login.", parent=self.app_instance.window)