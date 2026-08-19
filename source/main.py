from tkinterdnd2 import TkinterDnD
from main_window import ImageResizerApp

if __name__ == "__main__":
    # Вместо tk.Tk() используем класс из tkinterdnd2
    root = TkinterDnD.Tk()
    app = ImageResizerApp(root)
    root.mainloop()
