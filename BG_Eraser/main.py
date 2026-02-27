# main.py
import tkinter as tk
from app import BGRemoverApp

if __name__ == "__main__":
    root = tk.Tk()
    app = BGRemoverApp(root)
    root.mainloop()