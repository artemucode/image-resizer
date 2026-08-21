import os
import sys
from tkinterdnd2 import TkinterDnD
from main_window import ImageResizerApp

def resource_path(relative_path):
    """
    Получает абсолютный путь к ресурсам.
    Работает как в режиме разработки, так и для скомпилированного PyInstaller .exe.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

if __name__ == "__main__":
    # Создаем главное окно с поддержкой Drag-and-Drop
    root = TkinterDnD.Tk()

    # Устанавливаем иконку окна и панели задач
    icon_path = resource_path(os.path.join("icon", "icon.ico"))
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass  # Пропускаем, если системный драйвер не смог загрузить .ico

    # Запускаем приложение
    app = ImageResizerApp(root)
    root.mainloop()
