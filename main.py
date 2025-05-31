import tkinter as tk
import sys
import os

project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app_gui import AppGui 

if __name__ == "__main__":
    root = tk.Tk()
    main_app = AppGui(root) 
    root.mainloop()
