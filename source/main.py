import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, UnidentifiedImageError
from pathlib import Path
import webbrowser


# =========================
# Настройки
# =========================

# ПОДДЕРЖКА
# SUPPORT_URL = "https://example.com"


image_path = None
save_path = None


# =========================
# Выбор изображения
# =========================

def choose_image():
    global image_path

    file = filedialog.askopenfilename(
        title="Выберите изображение",
        filetypes=[
            (
                "Изображения",
                "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"
            ),
            ("Все файлы", "*.*")
        ]
    )

    if not file:
        return

    try:
        with Image.open(file) as image:
            image.verify()

        with Image.open(file) as image:
            width = image.width
            height = image.height

    except UnidentifiedImageError:
        messagebox.showerror(
            "Ошибка",
            "Выбранный файл не является изображением."
        )
        return

    except PermissionError:
        messagebox.showerror(
            "Ошибка",
            "Нет доступа к выбранному файлу."
        )
        return

    except OSError:
        messagebox.showerror(
            "Ошибка",
            "Не удалось открыть изображение."
        )
        return

    image_path = file

    size_label.config(
        text=f"Размер: {width} x {height}"
    )

    image_label.config(
        text=Path(file).name
    )

    result_label.config(text="")


# =========================
# Выбор папки
# =========================

def choose_save_path():
    global save_path

    folder = filedialog.askdirectory(
        title="Выберите папку для сохранения"
    )

    if not folder:
        return

    save_path = folder

    save_label.config(
        text=folder
    )

    result_label.config(text="")


# =========================
# Изменение размера
# =========================

def resize_image():
    if not image_path:
        messagebox.showwarning(
            "Внимание",
            "Сначала выберите изображение."
        )
        return

    if not save_path:
        messagebox.showwarning(
            "Внимание",
            "Сначала выберите папку для сохранения."
        )
        return

    width_text = width_entry.get().strip()
    height_text = height_entry.get().strip()

    if not width_text or not height_text:
        messagebox.showwarning(
            "Внимание",
            "Введите ширину и высоту."
        )
        return

    try:
        width = int(width_text)
        height = int(height_text)

    except ValueError:
        messagebox.showerror(
            "Ошибка",
            "Ширина и высота должны быть целыми числами."
        )
        return

    if width <= 0 or height <= 0:
        messagebox.showerror(
            "Ошибка",
            "Ширина и высота должны быть больше нуля."
        )
        return

    if width > 10000 or height > 10000:
        messagebox.showerror(
            "Ошибка",
            "Максимальный размер — 10000 x 10000 пикселей."
        )
        return

    try:
        with Image.open(image_path) as image:
            resized = image.resize(
                (width, height),
                Image.Resampling.LANCZOS
            )

            original_name = Path(image_path).stem
            extension = Path(image_path).suffix.lower()

            # Форматы, которые Pillow нормально сохраняет
            supported_extensions = {
                ".jpg": "JPEG",
                ".jpeg": "JPEG",
                ".png": "PNG",
                ".bmp": "BMP",
                ".gif": "GIF",
                ".tiff": "TIFF",
                ".webp": "WEBP"
            }

            image_format = supported_extensions.get(extension)

            if not image_format:
                messagebox.showerror(
                    "Ошибка",
                    "Формат этого изображения не поддерживается "
                    "для сохранения."
                )
                return

            # JPEG не поддерживает прозрачность
            if image_format == "JPEG" and resized.mode in (
                "RGBA",
                "LA",
                "P"
            ):
                resized = resized.convert("RGB")

            output_path = (
                Path(save_path)
                / f"{original_name}_resized{extension}"
            )

            # Если файл уже существует
            if output_path.exists():
                replace = messagebox.askyesno(
                    "Файл уже существует",
                    f"Файл уже существует:\n\n"
                    f"{output_path.name}\n\n"
                    "Перезаписать его?"
                )

                if not replace:
                    return

            resized.save(
                output_path,
                format=image_format
            )

    except FileNotFoundError:
        messagebox.showerror(
            "Ошибка",
            "Исходный файл не найден."
        )
        return

    except PermissionError:
        messagebox.showerror(
            "Ошибка",
            "Нет разрешения на сохранение в эту папку."
        )
        return

    except UnidentifiedImageError:
        messagebox.showerror(
            "Ошибка",
            "Файл повреждён или не является изображением."
        )
        return

    except OSError as error:
        messagebox.showerror(
            "Ошибка",
            f"Не удалось обработать изображение.\n\n{error}"
        )
        return

    except Exception as error:
        messagebox.showerror(
            "Неизвестная ошибка",
            f"Произошла непредвиденная ошибка:\n\n{error}"
        )
        return

    result_label.config(
        text="Изображение успешно сохранено!"
    )

    messagebox.showinfo(
        "Готово",
        f"Изображение сохранено:\n\n{output_path}"
    )


# =========================
# Поддержать
# =========================

def support():
    # ВРЕМЕННО
    messagebox.showerror(
        "Ошибка",
        "Не удалось открыть страницу поддержки.\n"
        "Поддержка пока не доступна!"
    )

    # try:
    #     webbrowser.open(SUPPORT_URL)

    # except Exception:
    #     messagebox.showerror(
    #         "Ошибка",
    #         "Не удалось открыть страницу поддержки."
    #     )

# =========================
# Окно
# =========================

root = tk.Tk()

root.title("Image Resizer v0.1")
root.geometry("350x450")
root.resizable(False, False)


# =========================
# Размер изображения
# =========================

size_label = tk.Label(
    root,
    text="Размер: —"
)

size_label.pack(pady=25)


# =========================
# Выбор изображения
# =========================

image_frame = tk.Frame(root)
image_frame.pack(
    fill="x",
    padx=20,
    pady=10
)

image_button = tk.Button(
    image_frame,
    text="Выбрать",
    command=choose_image
)

image_button.pack(side="left")

image_label = tk.Label(
    image_frame,
    text="—",
    anchor="w"
)

image_label.pack(
    side="left",
    padx=10
)


# =========================
# Ширина
# =========================

width_frame = tk.Frame(root)
width_frame.pack(pady=5)

width_label = tk.Label(
    width_frame,
    text="Ширина:"
)

width_label.pack(side="left")

width_entry = tk.Entry(
    width_frame,
    width=30
)

width_entry.pack(
    side="left",
    padx=10
)


# =========================
# Высота
# =========================

height_frame = tk.Frame(root)
height_frame.pack(pady=5)

height_label = tk.Label(
    height_frame,
    text="Высота:"
)

height_label.pack(side="left")

height_entry = tk.Entry(
    height_frame,
    width=30
)

height_entry.pack(
    side="left",
    padx=10
)


# =========================
# Выбор папки
# =========================

save_frame = tk.Frame(root)
save_frame.pack(
    fill="x",
    padx=20,
    pady=20
)

save_button = tk.Button(
    save_frame,
    text="Сохранить",
    command=choose_save_path
)

save_button.pack(side="left")

save_label = tk.Label(
    save_frame,
    text="—",
    anchor="w"
)

save_label.pack(
    side="left",
    padx=10
)


# =========================
# Изменить размер
# =========================

resize_button = tk.Button(
    root,
    text="Изменить размер",
    command=resize_image,
    width=15,
    height=2
)

resize_button.pack(pady=20)


# =========================
# Результат
# =========================

result_label = tk.Label(
    root,
    text=""
)

result_label.pack()


# =========================
# Нижняя панель
# =========================

bottom_frame = tk.Frame(root)

bottom_frame.pack(
    side="bottom",
    fill="x",
    pady=15
)


version_label = tk.Label(
    bottom_frame,
    text="Версия: 0.1"
)

version_label.pack(
    side="left",
    padx=20
)


support_button = tk.Button(
    bottom_frame,
    text="Поддержать",
    command=support
)

support_button.pack(
    side="right",
    padx=20
)


# =========================
# Запуск
# =========================

root.mainloop()


# V 0.01

# import tkinter as tk
# from tkinter import filedialog
# from PIL import Image

# image_path = None
# save_path = None

# def choose_image():
#     file = filedialog.askopenfilename()
    
#     if not file:
#         return
#     global image_path
#     image_path = file
    
#     image = Image.open(file)
    
#     size_label.config(text=f"Размер: {image.width} x {image.height}")
    
# def choose_save_path():
#     global save_path

#     save_path = filedialog.asksaveasfilename(
#         title="Сохранить изображение",
#         defaultextension=".png",
#         filetypes=[
#             ("PNG", "*.png"),
#             ("JPEG", "*.jpg"),
#             ("WEBP", "*.webp")
#         ]
#     )
    
#     if save_path:
#         save_label.config(text=f"Сохранить: {save_path}")

# def resize_image():
#     if not image_path:
#         return

#     if not save_path:
#         return

#     width = int(width_entry.get())
#     height = int(height_entry.get())
    
#     image = Image.open(image_path)
#     resized = image.resize((width, height))
    
#     resized.save(save_path)
    
#     result_label.config(text="Изображение успешно сохранено!")

# root = tk.Tk()
# root.title("Image Resizer")
# root.geometry("450x300")

# button = tk.Button(
#     root,
#     text="Выбрать изображение",
#     command=choose_image
# )

# size_label = tk.Label(root, text="Размер: -")
# size_label.pack()

# width_label = tk.Label(root, text="Ширина:")
# width_label.pack()

# width_entry = tk.Entry(root)
# width_entry.pack()

# height_label = tk.Label(root, text="Высота:")
# height_label.pack()

# height_entry = tk.Entry(root)
# height_entry.pack()

# save_label = tk.Label(root, text="Место сохранения: -")
# save_label.pack()

# save_button = tk.Button(
#     root,
#     text="Куда сохранить",
#     command=choose_save_path
# )

# save_button.pack()

# resize_button = tk.Button(
#     root,
#     text="Изменить размер",
#     command=resize_image
# )

# resize_button.pack()

# result_label = tk.Label(root, text="")
# result_label.pack()

# button.pack()

# root.mainloop()
