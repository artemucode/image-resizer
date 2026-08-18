import os
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk


class ImageResizerApp:
    
    # ========== КОНСТАНТЫ ==========
    MAX_SIZE = 10000
    
    FORMATS = {
        ".jpg": "JPEG", 
        ".jpeg": "JPEG",
        ".png": "PNG", 
        ".bmp": "BMP",
        ".gif": "GIF", 
        ".tiff": "TIFF",
        ".webp": "WEBP"
    }

    def __init__(
        self, 
        root: tk.Tk
    ):
        self.root = root
        
        self.root.title(
            "Image Resizer v0.5"
        )
        
        self.root.geometry(
            "750x780"
        )
        
        self.root.minsize(
            650, 
            700
        )

        # ========== СОСТОЯНИЕ ПРИЛОЖЕНИЯ ==========
        self.image_paths = []
        self.save_path = None
        
        self.keep_ratio_var = tk.BooleanVar(
            value=False
        )
        
        self.format_var = tk.StringVar(
            value="Исходный"
        )
        
        self.quality_var = tk.IntVar(
            value=85
        )

        # ========== ИНИЦИАЛИЗАЦИЯ ИНТЕРФЕЙСА ==========
        self._setup_styles()
        self._create_widgets()
        self._layout_widgets()
        
        # Первоначальная проверка доступности слайдера качества
        self._update_quality_state()

    # ==========================================
    #             НАСТРОЙКА ИНТЕРФЕЙСА
    # ==========================================

    def _setup_styles(self):
        self.style = ttk.Style()
        
        self.style.configure(
            "TLabel", 
            padding=4
        )
        
        self.style.configure(
            "TButton", 
            padding=6
        )
        
        self.style.configure(
            "TLabelframe", 
            padding=8
        )
        
        self.style.configure(
            "Action.TButton", 
            font=(
                "Segoe UI", 
                10, 
                "bold"
            )
        )

    def _create_widgets(self):
        # Главный контейнер
        self.main_container = ttk.Frame(
            self.root, 
            padding=15
        )

        # ----- Секция списка и предпросмотра -----
        self.top_frame = ttk.Frame(
            self.main_container
        )
        
        # Левая панель (Список)
        self.left_frame = ttk.Frame(
            self.top_frame
        )
        
        self.listbox_label = ttk.Label(
            self.left_frame, 
            text="Список файлов:"
        )
        
        self.listbox = tk.Listbox(
            self.left_frame, 
            height=10, 
            selectmode=tk.SINGLE, 
            activestyle="dotbox",
            borderwidth=1,
            relief="solid"
        )
        
        self.listbox.bind(
            "<<ListboxSelect>>", 
            self._on_select_image
        )

        self.btn_files_frame = ttk.Frame(
            self.left_frame
        )
        
        self.btn_add = ttk.Button(
            self.btn_files_frame, 
            text="Добавить", 
            command=self.choose_images
        )
        
        self.btn_clear = ttk.Button(
            self.btn_files_frame, 
            text="Очистить", 
            command=self.clear_file_list
        )

        # Правая панель (Превью)
        self.right_frame = ttk.Frame(
            self.top_frame
        )
        
        self.preview_label = ttk.Label(
            self.right_frame, 
            background="#F0F0F0", 
            anchor="center",
            relief="solid",
            borderwidth=1
        )
        
        self.size_label = ttk.Label(
            self.right_frame, 
            text="Размер: —", 
            anchor="center"
        )

        # ----- Секция параметров -----
        self.param_frame = ttk.LabelFrame(
            self.main_container, 
            text="Параметры изменения"
        )
        
        self.wh_frame = ttk.Frame(
            self.param_frame
        )
        
        self.lbl_width = ttk.Label(
            self.wh_frame, 
            text="Ширина:"
        )
        
        self.width_entry = ttk.Entry(
            self.wh_frame, 
            width=10
        )
        
        self.lbl_height = ttk.Label(
            self.wh_frame, 
            text="Высота:"
        )
        
        self.height_entry = ttk.Entry(
            self.wh_frame, 
            width=10
        )

        self.keep_ratio_check = ttk.Checkbutton(
            self.wh_frame, 
            text="Сохранять пропорции", 
            variable=self.keep_ratio_var, 
            command=self._toggle_keep_ratio
        )

        self.format_frame = ttk.Frame(
            self.param_frame
        )
        
        self.lbl_format = ttk.Label(
            self.format_frame, 
            text="Выходной формат:"
        )
        
        format_choices = ["Исходный"] + sorted(list(set(self.FORMATS.values())))
        
        self.format_combo = ttk.Combobox(
            self.format_frame, 
            textvariable=self.format_var, 
            values=format_choices, 
            state="readonly", 
            width=12
        )
        
        self.format_combo.bind(
            "<<ComboboxSelected>>", 
            lambda e: self._update_quality_state()
        )

        # Секция качества сжатия
        self.quality_frame = ttk.Frame(
            self.param_frame
        )
        
        self.lbl_quality = ttk.Label(
            self.quality_frame, 
            text="Качество (JPG/WEBP):"
        )
        
        self.quality_slider = ttk.Scale(
            self.quality_frame, 
            from_=1, 
            to=100, 
            orient="horizontal", 
            variable=self.quality_var,
            command=self._update_quality_label
        )
        
        self.lbl_quality_val = ttk.Label(
            self.quality_frame, 
            text="85%", 
            width=5
        )

        # ----- Секция сохранения -----
        self.save_frame = ttk.LabelFrame(
            self.main_container, 
            text="Сохранение"
        )
        
        self.btn_save_dir = ttk.Button(
            self.save_frame, 
            text="Выбрать папку", 
            command=self.choose_save_path
        )
        
        self.save_path_label = ttk.Label(
            self.save_frame, 
            text="Папка не выбрана", 
            foreground="gray"
        )
        
        self.btn_open_dir = ttk.Button(
            self.save_frame, 
            text="Открыть папку", 
            command=self.open_output_folder
        )

        # ----- Секция запуска и прогресса -----
        self.action_frame = ttk.Frame(
            self.main_container
        )
        
        self.progress_bar = ttk.Progressbar(
            self.action_frame, 
            orient="horizontal", 
            mode="determinate"
        )
        
        self.btn_process = ttk.Button(
            self.action_frame, 
            text="Обработать все файлы", 
            command=self.resize_images, 
            style="Action.TButton"
        )

        # Информационная метка результатов
        self.result_label = ttk.Label(
            self.main_container, 
            text="", 
            font=(
                "Segoe UI", 
                10
            ), 
            anchor="center"
        )

        # ----- Нижний подвал -----
        self.bottom_frame = ttk.Frame(
            self.main_container
        )
        
        self.lbl_version = ttk.Label(
            self.bottom_frame, 
            text="Версия: 0.5"
        )
        
        self.btn_support = ttk.Button(
            self.bottom_frame, 
            text="Поддержать", 
            command=self.support
        )

    def _layout_widgets(self):
        self.main_container.pack(
            fill="both", 
            expand=True
        )

        # Верхняя панель
        self.top_frame.pack(
            fill="both", 
            expand=True, 
            pady=(0, 10)
        )
        
        self.left_frame.pack(
            side="left", 
            fill="both", 
            expand=True, 
            padx=(0, 10)
        )
        
        self.listbox_label.pack(
            anchor="w"
        )
        
        self.listbox.pack(
            fill="both", 
            expand=True, 
            pady=5
        )
        
        self.btn_files_frame.pack(
            fill="x"
        )
        
        self.btn_add.pack(
            side="left", 
            padx=(0, 5)
        )
        
        self.btn_clear.pack(
            side="left"
        )

        self.right_frame.pack(
            side="right", 
            fill="both", 
            expand=False
        )
        
        self.preview_label.pack(
            fill="both", 
            expand=True, 
            pady=(18, 5)
        )
        
        self.preview_label.config(
            width=20
        )
        
        self.size_label.pack(
            fill="x"
        )

        # Параметры
        self.param_frame.pack(
            fill="x", 
            pady=5
        )
        
        self.wh_frame.pack(
            fill="x", 
            pady=5
        )
        
        self.lbl_width.pack(
            side="left", 
            padx=(0, 5)
        )
        
        self.width_entry.pack(
            side="left", 
            padx=(0, 15)
        )
        
        self.lbl_height.pack(
            side="left", 
            padx=(0, 5)
        )
        
        self.height_entry.pack(
            side="left", 
            padx=(0, 15)
        )
        
        self.keep_ratio_check.pack(
            side="left", 
            padx=(10, 0)
        )

        self.format_frame.pack(
            fill="x", 
            pady=5
        )
        
        self.lbl_format.pack(
            side="left", 
            padx=(0, 10)
        )
        
        self.format_combo.pack(
            side="left"
        )

        self.quality_frame.pack(
            fill="x", 
            pady=5
        )
        
        self.lbl_quality.pack(
            side="left", 
            padx=(0, 10)
        )
        
        self.quality_slider.pack(
            side="left", 
            fill="x", 
            expand=True, 
            padx=(0, 10)
        )
        
        self.lbl_quality_val.pack(
            side="left"
        )

        # Сохранение
        self.save_frame.pack(
            fill="x", 
            pady=5
        )
        
        self.btn_save_dir.pack(
            side="left", 
            padx=(0, 10)
        )
        
        self.save_path_label.pack(
            side="left", 
            fill="x", 
            expand=True
        )
        
        self.btn_open_dir.pack(
            side="right"
        )

        # Действие
        self.action_frame.pack(
            fill="x", 
            pady=10
        )
        
        self.progress_bar.pack(
            fill="x", 
            pady=(0, 10)
        )
        
        self.btn_process.pack(
            ipady=3
        )

        # Статус
        self.result_label.pack(
            fill="x", 
            pady=5
        )

        # Подвал
        self.bottom_frame.pack(
            side="bottom", 
            fill="x", 
            pady=(10, 0)
        )
        
        self.lbl_version.pack(
            side="left"
        )
        
        self.btn_support.pack(
            side="right"
        )

    # ==========================================
    #             БИЗНЕС-ЛОГИКА
    # ==========================================

    def _update_quality_state(self):
        """Блокирует или разблокирует ползунок качества."""
        selected_fmt = self.format_var.get()
        
        # Если выбран явный формат JPEG или WEBP
        if selected_fmt in ("JPEG", "WEBP"):
            state = "normal"
            
        # Если формат "Исходный", проверяем загруженные файлы
        elif selected_fmt == "Исходный" and self.image_paths:
            has_quality_support = False
            for path in self.image_paths:
                ext = Path(path).suffix.lower()
                if self.FORMATS.get(ext) in ("JPEG", "WEBP"):
                    has_quality_support = True
                    break
            state = "normal" if has_quality_support else "disabled"
            
        else:
            state = "disabled"

        self.quality_slider.config(
            state=state
        )
        
        self.lbl_quality.config(
            state=state
        )
        
        self.lbl_quality_val.config(
            state=state
        )

    def _update_quality_label(
        self, 
        val
    ):
        self.lbl_quality_val.config(
            text=f"{int(float(val))}%"
        )

    def choose_images(self):
        files = filedialog.askopenfilenames(
            title="Выберите изображения",
            filetypes=[
                (
                    "Изображения", 
                    "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"
                ),
                (
                    "Все файлы", 
                    "*.*"
                )
            ]
        )
        
        if not files:
            return

        valid_files = []
        
        for file_path in files:
            if file_path in self.image_paths:
                continue
                
            try:
                with Image.open(file_path) as img:
                    img.verify()
                valid_files.append(file_path)
            except Exception:
                pass

        if not valid_files and not self.image_paths:
            messagebox.showerror(
                "Ошибка", 
                "Ни один из выбранных файлов не является корректным изображением."
            )
            return

        self.image_paths.extend(valid_files)
        self._refresh_listbox()

        if self.image_paths:
            self.listbox.selection_clear(
                0, 
                tk.END
            )
            
            self.listbox.selection_set(
                tk.END
            )
            
            self.update_preview()

        self._update_quality_state()
        
        self.result_label.config(
            text=""
        )

    def _refresh_listbox(self):
        self.listbox.delete(
            0, 
            tk.END
        )
        
        for path in self.image_paths:
            self.listbox.insert(
                tk.END, 
                Path(path).name
            )

    def clear_file_list(self):
        self.image_paths.clear()
        
        self.listbox.delete(
            0, 
            tk.END
        )
        
        self.preview_label.config(
            image=""
        )
        
        self.preview_label.image = None
        
        self.size_label.config(
            text="Размер: —"
        )
        
        self.result_label.config(
            text=""
        )
        
        self._update_quality_state()

    def _on_select_image(
        self, 
        event
    ):
        self.update_preview()

    def update_preview(self):
        selection = self.listbox.curselection()
        
        if not selection:
            return

        index = selection[0]
        file_path = self.image_paths[index]

        try:
            with Image.open(file_path) as img:
                width, height = img.size
                
                self.size_label.config(
                    text=f"Размер: {width} × {height}"
                )

                img_copy = img.copy()
                img_copy.thumbnail(
                    (160, 160)
                )
                
                photo = ImageTk.PhotoImage(img_copy)
                
                self.preview_label.config(
                    image=photo
                )
                
                self.preview_label.image = photo
                
        except Exception:
            self.preview_label.config(
                image=""
            )
            
            self.preview_label.image = None
            
            self.size_label.config(
                text="Ошибка файла"
            )

    def choose_save_path(self):
        folder = filedialog.askdirectory(
            title="Выберите папку для сохранения"
        )
        
        if folder:
            self.save_path = folder
            
            self.save_path_label.config(
                text=folder, 
                foreground="black"
            )
            
            self.result_label.config(
                text=""
            )

    def open_output_folder(self):
        if self.save_path and os.path.exists(self.save_path):
            if os.name == 'nt':
                os.startfile(self.save_path)
            else:
                webbrowser.open(self.save_path)
        else:
            messagebox.showwarning(
                "Внимание", 
                "Папка не выбрана или не существует."
            )

    def _toggle_keep_ratio(self):
        if self.keep_ratio_var.get():
            self.width_entry.bind(
                "<KeyRelease>", 
                lambda e: self._update_linked_size("width")
            )
            
            self.height_entry.bind(
                "<KeyRelease>", 
                lambda e: self._update_linked_size("height")
            )
        else:
            self.width_entry.unbind(
                "<KeyRelease>"
            )
            
            self.height_entry.unbind(
                "<KeyRelease>"
            )

    def _update_linked_size(
        self, 
        changed_side: str
    ):
        if not self.keep_ratio_var.get() or not self.image_paths:
            return

        selection = self.listbox.curselection()
        
        if not selection:
            return

        file_path = self.image_paths[selection[0]]
        
        try:
            with Image.open(file_path) as img:
                orig_w, orig_h = img.size
        except Exception:
            return

        try:
            if changed_side == "width":
                w_str = self.width_entry.get().strip()
                
                if w_str and int(w_str) > 0:
                    new_h = int(int(w_str) * orig_h / orig_w)
                    
                    self.height_entry.delete(
                        0, 
                        tk.END
                    )
                    
                    self.height_entry.insert(
                        0, 
                        str(new_h)
                    )
            else:
                h_str = self.height_entry.get().strip()
                
                if h_str and int(h_str) > 0:
                    new_w = int(int(h_str) * orig_w / orig_h)
                    
                    self.width_entry.delete(
                        0, 
                        tk.END
                    )
                    
                    self.width_entry.insert(
                        0, 
                        str(new_w)
                    )
        except ValueError:
            pass

    def resize_images(self):
        if not self.image_paths:
            messagebox.showwarning(
                "Внимание", 
                "Сначала выберите изображения."
            )
            return

        if not self.save_path:
            messagebox.showwarning(
                "Внимание", 
                "Сначала выберите папку для сохранения."
            )
            return

        w_text = self.width_entry.get().strip()
        h_text = self.height_entry.get().strip()

        if not w_text or not h_text:
            messagebox.showwarning(
                "Внимание", 
                "Укажите ширину и высоту."
            )
            return

        try:
            width = int(w_text)
            height = int(h_text)
        except ValueError:
            messagebox.showerror(
                "Ошибка", 
                "Размеры должны быть целыми числами."
            )
            return

        if width <= 0 or height <= 0:
            messagebox.showerror(
                "Ошибка", 
                "Размеры должны быть больше нуля."
            )
            return

        if width > self.MAX_SIZE or height > self.MAX_SIZE:
            messagebox.showerror(
                "Ошибка", 
                f"Максимальный размер: {self.MAX_SIZE}×{self.MAX_SIZE} px."
            )
            return

        selected_format = self.format_var.get()
        ext_map = {v: k for k, v in self.FORMATS.items()}
        target_ext = ext_map.get(selected_format)

        total_files = len(self.image_paths)
        self.progress_bar['maximum'] = total_files
        self.progress_bar['value'] = 0

        errors = []
        quality_val = self.quality_var.get()

        for idx, file_path in enumerate(self.image_paths):
            try:
                with Image.open(file_path) as img:
                    resized_img = img.resize(
                        (width, height), 
                        Image.Resampling.LANCZOS
                    )
                    
                    if target_ext:
                        out_ext = target_ext
                    else:
                        out_ext = Path(file_path).suffix.lower()

                    img_format = self.FORMATS.get(out_ext)
                    
                    if not img_format:
                        errors.append(
                            f"{Path(file_path).name}: Неподдерживаемый формат ({out_ext})"
                        )
                        continue

                    if img_format == "JPEG" and resized_img.mode in ("RGBA", "LA", "P"):
                        resized_img = resized_img.convert("RGB")

                    output_name = f"{Path(file_path).stem}_resized{out_ext}"
                    output_path = Path(self.save_path) / output_name

                    save_kwargs = {
                        "format": img_format
                    }
                    
                    # Применяем качество, если формат поддерживает
                    if img_format in ("JPEG", "WEBP"):
                        save_kwargs["quality"] = quality_val

                    resized_img.save(
                        output_path, 
                        **save_kwargs
                    )
                    
            except Exception as e:
                errors.append(
                    f"{Path(file_path).name}: {str(e)}"
                )

            self.progress_bar['value'] = idx + 1
            self.root.update_idletasks()

        successful = total_files - len(errors)
        
        self.result_label.config(
            text=f"Готово! Успешно: {successful} из {total_files}.",
            foreground="black" if not errors else "#D9822B"
        )

        if errors:
            msg = "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... и еще {len(errors) - 5} ошибок."
            messagebox.showwarning(
                "Предупреждение", 
                f"Обработано с ошибками:\n\n{msg}"
            )
        else:
            messagebox.showinfo(
                "Успешно", 
                "Все файлы успешно сохранены!"
            )

    def support(self):
        messagebox.showinfo(
            "Информация", 
            "Функция поддержки временно недоступна."
        )


# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    root = tk.Tk()
    
    app = ImageResizerApp(
        root
    )
    
    root.mainloop()
