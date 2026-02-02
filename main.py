import tkinter as tk
from ttkthemes import ThemedTk
from gui.main_window import CIGSApp

if __name__ == "__main__":
    # Aqui a gente define o tema "radiance" na criação da janela
    try:
        #root = ThemedTk(theme="arc")
        root = ThemedTk(theme="radiance")
    except:
        root = tk.Tk()
        
    app = CIGSApp(root)
    root.mainloop()