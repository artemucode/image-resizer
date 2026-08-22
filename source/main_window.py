import os
import webbrowser
import tkinter as tk
import threading
import tempfile
import shutil
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES
from PIL import Image, ImageTk, ImageGrab
from datetime import datetime

from config import MAX_SIZE, FORMATS, VERSION, APP_TITLE
from image_processor import ImageProcessor
from ui_components import setup_styles
from settings_manager import SettingsManager

import sys

# Системный звук для Windows
if sys.platform == "win32":
    import winsound

class ImageResizerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("750x830")
        self.root.minsize(650, 750)

        # 1. Загрузка сохраненных настроек
        saved_settings = SettingsManager.load_settings()

        # Состояние
        self.image_paths = []
        self.save_path = saved_settings.get("save_path", "")
        self.is_processing = False
        self.keep_ratio_var = tk.BooleanVar(value=False)
        self.strip_meta_var = tk.BooleanVar(value=True)
        self.format_var = tk.StringVar(value="Исходный")
        self.mode_var = tk.StringVar(value="Растянуть")
        self.quality_var = tk.IntVar(value=saved_settings.get("quality", 85))
        
        self.root.bind("<Control-Key>", self._on_ctrl_key)
        
        # Перехват закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        setup_styles()
        self._create_widgets()
        self._layout_widgets()
        self._update_quality_state()

        # 2. Восстановление пути, если он сохранен и существует
        if self.save_path and os.path.exists(self.save_path):
            self.save_path_label.config(text=self.save_path, foreground="black")

    def _on_close(self):
        """Сохранение настроек и очистка временных файлов перед выходом."""
        SettingsManager.save_settings(
            save_path=self.save_path,
            quality=self.quality_var.get()
        )
        
        # Очистка временных файлов из буфера обмена
        temp_dir = Path(tempfile.gettempdir()) / "ImageResizerApp"
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except OSError as e:
            print(f"[ImageResizerApp] Ошибка удаления временной папки: {e}")

        self.root.destroy()

    def choose_save_path(self):
        if self.is_processing:
            return

        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.save_path = folder
            self.save_path_label.config(text=folder, foreground="black")
            self.result_label.config(text="")
            SettingsManager.save_settings(
                save_path=self.save_path,
                quality=self.quality_var.get()
            )

    def open_output_folder(self):
        if self.save_path and os.path.exists(self.save_path):
            if os.name == 'nt':
                os.startfile(self.save_path)
            else:
                webbrowser.open(self.save_path)
        else:
            messagebox.showwarning("Внимание", "Папка не выбрана или не существует.")

    def _update_quality_label(self, val):
        self.lbl_quality_val.config(text=f"{int(float(val))}%")
        SettingsManager.save_settings(
            save_path=self.save_path,
            quality=self.quality_var.get()
        )

    def _create_widgets(self):
        self.main_container = ttk.Frame(self.root, padding=15)

        # Верхняя секция
        self.top_frame = ttk.Frame(self.main_container)
        self.left_frame = ttk.Frame(self.top_frame)
        self.listbox_label = ttk.Label(self.left_frame, text="Список файлов:")
        
        self.listbox = tk.Listbox(
            self.left_frame, height=10, selectmode=tk.SINGLE, 
            activestyle="dotbox", borderwidth=1, relief="solid"
        )
        self.listbox.bind("<<ListboxSelect>>", self._on_select_image)
        self.listbox.bind("<Delete>", self._remove_selected_image)

        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind("<<Drop>>", self._on_drop_files)

        self.placeholder_label = tk.Label(
            self.left_frame,
            text="Выберите или перетяните файлы",
            font=("Segoe UI", 9, "italic"),
            fg="gray",
            bg="white",
            anchor="center",
            cursor="hand2"
        )
        self.placeholder_label.bind("<Button-1>", lambda e: self.choose_images())
        self.placeholder_label.drop_target_register(DND_FILES)
        self.placeholder_label.dnd_bind("<<Drop>>", self._on_drop_files)

        self.counter_label = ttk.Label(
            self.left_frame, 
            text="Файлов: 0 | Общий размер: 0 МБ", 
            foreground="gray"
        )

        self.btn_files_frame = ttk.Frame(self.left_frame)
        self.btn_add = ttk.Button(self.btn_files_frame, text="Добавить", command=self.choose_images)
        self.btn_clear = ttk.Button(self.btn_files_frame, text="Очистить", command=self.clear_file_list)

        self.right_frame = ttk.Frame(self.top_frame)
        self.preview_label = ttk.Label(
            self.right_frame, background="#F0F0F0", anchor="center", relief="solid", borderwidth=1
        )
        self.size_label = ttk.Label(self.right_frame, text="Размер: —", anchor="center")

        # Параметры
        self.param_frame = ttk.LabelFrame(self.main_container, text="Параметры изменения")
        self.wh_frame = ttk.Frame(self.param_frame)
        self.lbl_width = ttk.Label(self.wh_frame, text="Ширина:")
        self.width_entry = ttk.Entry(self.wh_frame, width=10)
        self.lbl_height = ttk.Label(self.wh_frame, text="Высота:")
        self.height_entry = ttk.Entry(self.wh_frame, width=10)
        self.keep_ratio_check = ttk.Checkbutton(
            self.wh_frame, text="Сохранять пропорции", variable=self.keep_ratio_var, command=self._toggle_keep_ratio
        )

        # Выбор режима масштабирования
        self.mode_frame = ttk.Frame(self.param_frame)
        self.lbl_mode = ttk.Label(self.mode_frame, text="Режим кадрирования:")
        self.mode_combo = ttk.Combobox(
            self.mode_frame, 
            textvariable=self.mode_var, 
            values=["Растянуть", "Вписать с полями (Fit)", "Ообрезать лишнее (Crop)"], 
            state="readonly", 
            width=24
        )
        self.mode_combo.bind("<<ComboboxSelected>>", self._on_mode_change)

        self.format_frame = ttk.Frame(self.param_frame)
        self.lbl_format = ttk.Label(self.format_frame, text="Выходной формат:")
        format_choices = ["Исходный"] + sorted(list(set(FORMATS.values())))
        self.format_combo = ttk.Combobox(
            self.format_frame, textvariable=self.format_var, values=format_choices, state="readonly", width=12
        )
        self.format_combo.bind("<<ComboboxSelected>>", lambda e: self._update_quality_state())

        self.quality_frame = ttk.Frame(self.param_frame)
        self.lbl_quality = ttk.Label(self.quality_frame, text="Качество (JPG/WEBP):")
        self.quality_slider = ttk.Scale(
            self.quality_frame, from_=1, to=100, orient="horizontal", 
            variable=self.quality_var, command=self._update_quality_label
        )
        self.lbl_quality_val = ttk.Label(self.quality_frame, text=f"{self.quality_var.get()}%", width=5)

        self.meta_frame = ttk.Frame(self.param_frame)
        self.strip_meta_check = ttk.Checkbutton(
            self.meta_frame, text="Удалять метаданные (EXIF)", variable=self.strip_meta_var
        )

        # Сохранение
        self.save_frame = ttk.LabelFrame(self.main_container, text="Сохранение")
        self.btn_save_dir = ttk.Button(self.save_frame, text="Выбрать папку", command=self.choose_save_path)
        self.save_path_label = ttk.Label(self.save_frame, text="Папка не выбрана", foreground="gray")
        self.btn_open_dir = ttk.Button(self.save_frame, text="Открыть папку", command=self.open_output_folder)

        # Запуск и прогресс
        self.action_frame = ttk.Frame(self.main_container)
        self.progress_bar = ttk.Progressbar(self.action_frame, orient="horizontal", mode="determinate")
        self.btn_process = ttk.Button(
            self.action_frame, text="Обработать все файлы", command=self.resize_images, style="Action.TButton"
        )
        self.result_label = ttk.Label(self.main_container, text="", font=("Segoe UI", 10), anchor="center")

        # Подвал
        self.bottom_frame = ttk.Frame(self.main_container)
        self.lbl_version = ttk.Label(self.bottom_frame, text=f"Версия: {VERSION}")
        self.btn_support = ttk.Button(self.bottom_frame, text="Поддержать", command=self.support)

    def _layout_widgets(self):
        self.main_container.pack(fill="both", expand=True)

        self.top_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.listbox_label.pack(anchor="w")
        self.listbox.pack(fill="both", expand=True, pady=5)
        self.counter_label.pack(anchor="w", pady=(0, 5))
        
        self.btn_files_frame.pack(fill="x")
        self.btn_add.pack(side="left", padx=(0, 5))
        self.btn_clear.pack(side="left")

        self.right_frame.pack(side="right", fill="both", expand=False)
        self.preview_label.pack(fill="both", expand=True, pady=(18, 5))
        self.preview_label.config(width=20)
        self.size_label.pack(fill="x")

        self.param_frame.pack(fill="x", pady=5)
        
        self.wh_frame.pack(fill="x", pady=5)
        self.lbl_width.pack(side="left", padx=(0, 5))
        self.width_entry.pack(side="left", padx=(0, 15))
        self.lbl_height.pack(side="left", padx=(0, 5))
        self.height_entry.pack(side="left", padx=(0, 15))
        self.keep_ratio_check.pack(side="left", padx=(10, 0))

        self.mode_frame.pack(fill="x", pady=5)
        self.lbl_mode.pack(side="left", padx=(0, 10))
        self.mode_combo.pack(side="left")

        self.format_frame.pack(fill="x", pady=5)
        self.lbl_format.pack(side="left", padx=(0, 10))
        self.format_combo.pack(side="left")

        self.quality_frame.pack(fill="x", pady=5)
        self.lbl_quality.pack(side="left", padx=(0, 10))
        self.quality_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.lbl_quality_val.pack(side="left")

        self.meta_frame.pack(fill="x", pady=5)
        self.strip_meta_check.pack(side="left")

        self.save_frame.pack(fill="x", pady=5)
        self.btn_save_dir.pack(side="left", padx=(0, 10))
        self.save_path_label.pack(side="left", fill="x", expand=True)
        self.btn_open_dir.pack(side="right")

        self.action_frame.pack(fill="x", pady=10)
        self.progress_bar.pack(fill="x", pady=(0, 10))
        self.btn_process.pack(ipady=3)

        self.result_label.pack(fill="x", pady=5)

        self.bottom_frame.pack(side="bottom", fill="x", pady=(10, 0))
        self.lbl_version.pack(side="left")
        self.btn_support.pack(side="right")

        self._update_placeholder_visibility()

    def _on_mode_change(self, event=None):
        if self.mode_var.get() in ("Вписать с полями (Fit)", "Ообрезать лишнее (Crop)"):
            self.keep_ratio_var.set(False)
            self._toggle_keep_ratio()

    def _update_quality_state(self):
        selected_fmt = self.format_var.get()
        if selected_fmt in ("JPEG", "WEBP"):
            state = "normal"
        elif selected_fmt == "Исходный" and self.image_paths:
            has_quality_support = any(
                FORMATS.get(Path(p).suffix.lower()) in ("JPEG", "WEBP") for p in self.image_paths
            )
            state = "normal" if has_quality_support else "disabled"
        else:
            state = "disabled"

        self.quality_slider.config(state=state)
        self.lbl_quality.config(state=state)
        self.lbl_quality_val.config(state=state)

    def _update_file_counter(self):
        count = len(self.image_paths)
        if count == 0:
            self.counter_label.config(text="Файлов: 0 | Общий размер: 0 МБ")
            return

        total_bytes = 0
        for path_str in self.image_paths:
            try:
                total_bytes += Path(path_str).stat().st_size
            except OSError:
                pass

        if total_bytes < 1024 * 1024:
            size_str = f"{total_bytes / 1024:.1f} КБ"
        else:
            size_str = f"{total_bytes / (1024 * 1024):.1f} МБ"

        self.counter_label.config(text=f"Файлов: {count} | Общий размер: {size_str}")

    def choose_images(self):
        if self.is_processing:
            return

        files = filedialog.askopenfilenames(
            title="Выберите изображения",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("Все файлы", "*.*")
            ]
        )
        if not files:
            return

        valid_files = [f for f in files if f not in self.image_paths and ImageProcessor.is_valid_image(f)]

        if not valid_files and not self.image_paths:
            messagebox.showerror("Ошибка", "Ни один из выбранных файлов не является корректным изображением.")
            return

        self.image_paths.extend(valid_files)
        self._refresh_listbox()

        if self.image_paths:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(tk.END)
            self.update_preview()

        self._update_quality_state()
        self.result_label.config(text="")

    def _refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for path in self.image_paths:
            self.listbox.insert(tk.END, Path(path).name)
        self._update_placeholder_visibility()
        self._update_file_counter()

    def clear_file_list(self):
        if self.is_processing:
            return

        self.image_paths.clear()
        self.listbox.delete(0, tk.END)
        self.preview_label.config(image="")
        self.preview_label.image = None
        self.size_label.config(text="Размер: —")
        self.result_label.config(text="")
        self._update_quality_state()
        self._update_placeholder_visibility()
        
    def _remove_selected_image(self, event=None):
        if self.is_processing:
            return

        selection = self.listbox.curselection()
        if not selection:
            return

        index = selection[0]

        self.image_paths.pop(index)
        self.listbox.delete(index)

        if not self.image_paths:
            self.preview_label.config(image="")
            self.preview_label.image = None
            self.size_label.config(text="Размер: —")
            self.result_label.config(text="")
            self._update_quality_state()
            self._update_placeholder_visibility()
        else:
            new_index = min(index, len(self.image_paths) - 1)
            self.listbox.selection_set(new_index)
            self.update_preview()
        self._update_file_counter()
        self._update_quality_state()

    def _on_select_image(self, event):
        self.update_preview()
        
    def _on_ctrl_key(self, event):
        if event.keycode == 86 or (event.char and event.char.lower() in ('v', 'м')):
            self.paste_from_clipboard()

    def paste_from_clipboard(self, event=None):
        if self.is_processing:
            return

        try:
            img = ImageGrab.grabclipboard()

            if isinstance(img, Image.Image):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Clipboard_{timestamp}.png"
                self._process_clipboard_image(img, filename)
        except Exception as e:
            print(f"[ImageResizerApp] Ошибка при вставке из буфера: {e}")

    def _process_clipboard_image(self, img: Image.Image, filename: str):
        temp_dir = Path(tempfile.gettempdir()) / "ImageResizerApp"
        temp_dir.mkdir(exist_ok=True)
        temp_file_path = str(temp_dir / filename)

        img.save(temp_file_path, "PNG")

        if temp_file_path not in self.image_paths:
            self.image_paths.append(temp_file_path)
            self._refresh_listbox()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(tk.END)
            self.update_preview()
            self._update_quality_state()
            self.result_label.config(text="")

    def update_preview(self):
        selection = self.listbox.curselection()
        if not selection:
            return

        file_path = self.image_paths[selection[0]]
        try:
            w, h = ImageProcessor.get_image_info(file_path)
            self.size_label.config(text=f"Размер: {w} × {h}")

            img_thumb = ImageProcessor.create_thumbnail(file_path)
            photo = ImageTk.PhotoImage(img_thumb)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except Exception:
            self.preview_label.config(image="")
            self.preview_label.image = None
            self.size_label.config(text="Ошибка файла")

    def _toggle_keep_ratio(self):
        if self.keep_ratio_var.get():
            self.width_entry.bind("<KeyRelease>", lambda e: self._update_linked_size("width"))
            self.height_entry.bind("<KeyRelease>", lambda e: self._update_linked_size("height"))
        else:
            self.width_entry.unbind("<KeyRelease>")
            self.height_entry.unbind("<KeyRelease>")

    def _update_linked_size(self, changed_side: str):
        if not self.keep_ratio_var.get() or not self.image_paths:
            return

        selection = self.listbox.curselection()
        file_path = self.image_paths[selection[0]] if selection else self.image_paths[0]

        try:
            orig_w, orig_h = ImageProcessor.get_image_info(file_path)
            if orig_w == 0 or orig_h == 0:
                return

            if changed_side == "width":
                w_str = self.width_entry.get().strip()
                if w_str.isdigit() and int(w_str) > 0:
                    new_h = int(int(w_str) * orig_h / orig_w)
                    self.height_entry.delete(0, tk.END)
                    self.height_entry.insert(0, str(new_h))
                elif w_str == "":
                    self.height_entry.delete(0, tk.END)
            else:
                h_str = self.height_entry.get().strip()
                if h_str.isdigit() and int(h_str) > 0:
                    new_w = int(int(h_str) * orig_w / orig_h)
                    self.width_entry.delete(0, tk.END)
                    self.width_entry.insert(0, str(new_w))
                elif h_str == "":
                    self.width_entry.delete(0, tk.END)
        except (ValueError, Exception):
            pass

    def _update_placeholder_visibility(self):
        if not self.image_paths:
            self.placeholder_label.place(in_=self.listbox, relx=0, rely=0, relwidth=1, relheight=1, x=2, y=2, width=-4, height=-4)
        else:
            self.placeholder_label.place_forget()
            
    def _on_drop_files(self, event):
        if self.is_processing:
            return

        raw_files = [f.strip("{}") for f in self.root.tk.splitlist(event.data)]
        
        valid_files = [
            f for f in raw_files 
            if f not in self.image_paths and ImageProcessor.is_valid_image(f)
        ]
        
        if valid_files:
            self.image_paths.extend(valid_files)
            self._refresh_listbox()
            
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set("end")
            self.update_preview()
            self._update_quality_state()
            self.result_label.config(text="")

    def set_ui_state(self, state: str):
        self.is_processing = (state == "disabled")
        btn_state = "disabled" if self.is_processing else "normal"
        
        self.btn_add.config(state=btn_state)
        self.btn_clear.config(state=btn_state)
        self.btn_save_dir.config(state=btn_state)
        self.btn_process.config(state=btn_state)

    def resize_images(self):
        if self.is_processing:
            return

        if not self.image_paths:
            messagebox.showwarning("Внимание", "Сначала выберите изображения.")
            return

        if not self.save_path:
            messagebox.showwarning("Внимание", "Сначала выберите папку для сохранения.")
            return

        w_text = self.width_entry.get().strip()
        h_text = self.height_entry.get().strip()

        if not w_text or not h_text:
            messagebox.showwarning("Внимание", "Укажите ширину и высоту.")
            return

        try:
            width = int(w_text)
            height = int(h_text)
        except ValueError:
            messagebox.showerror("Ошибка", "Размеры должны быть целыми числами.")
            return

        if width <= 0 or height <= 0:
            messagebox.showerror("Ошибка", "Размеры должны быть больше нуля.")
            return

        if width > MAX_SIZE or height > MAX_SIZE:
            messagebox.showerror("Ошибка", f"Максимальный размер: {MAX_SIZE}×{MAX_SIZE} px.")
            return
        
        mode_mapping = {
            "Растянуть": "Stretch",
            "Вписать с полями (Fit)": "Fit",
            "Ообрезать лишнее (Crop)": "Crop"
        }
        selected_mode = mode_mapping.get(self.mode_var.get(), "Stretch")

        total_files = len(self.image_paths)
        self.progress_bar['maximum'] = total_files
        self.progress_bar['value'] = 0
        
        self.set_ui_state("disabled")
        self.result_label.config(text="Обработка файлов...", foreground="blue")

        params = {
            "image_paths": list(self.image_paths),
            "save_path": self.save_path,
            "width": width,
            "height": height,
            "selected_format": self.format_var.get(),
            "quality_val": self.quality_var.get(),
            "strip_meta": self.strip_meta_var.get(),
            "resize_mode": selected_mode
        }

        thread = threading.Thread(
            target=self._async_resize_worker, 
            kwargs=params, 
            daemon=True
        )
        thread.start()

    def _async_resize_worker(self, image_paths, save_path, width, height, selected_format, quality_val, strip_meta, resize_mode):
        errors = []
        total_files = len(image_paths)

        for idx, file_path in enumerate(image_paths):
            try:
                ImageProcessor.process_single_image(
                    file_path=file_path,
                    save_dir=save_path,
                    width=width,
                    height=height,
                    target_format=selected_format,
                    quality=quality_val,
                    strip_metadata=strip_meta,
                    resize_mode=resize_mode
                )
            except Exception as e:
                errors.append(f"{Path(file_path).name}: {str(e)}")

            self.root.after(10, lambda v=idx + 1: self.progress_bar.config(value=v))

        self.root.after(20, self._on_process_complete, total_files, errors)

    def _on_process_complete(self, total_files, errors):
        self.set_ui_state("normal")

        successful = total_files - len(errors)
        self.result_label.config(
            text=f"Готово! Успешно: {successful} из {total_files}.",
            foreground="black" if not errors else "#D9822B"
        )

        self.play_finish_sound(has_errors=bool(errors))

        if errors:
            msg = "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... и еще {len(errors) - 5} ошибок."
            messagebox.showwarning("Предупреждение", f"Обработано с ошибками:\n\n{msg}")
        else:
            messagebox.showinfo("Успешно", "Все файлы успешно сохранены!")
            
    def play_finish_sound(self, has_errors: bool = False):
        """Воспроизводит звук после завершения обработки."""
        try:
            if sys.platform == "win32":
                # Стандартный звук уведомления Windows
                sound_type = winsound.MB_ICONEXCLAMATION if has_errors else winsound.MB_ICONASTERISK
                winsound.MessageBeep(sound_type)
            else:
                # Универсальный бип для линукс/мак ос
                print("\a")
        except Exception as e:
            print(f"[OSRT] Ошибка воспроизведения звука: {e}")

    def support(self):
        USDT_ADDRESS = "UQALTsk6AvmcEg7fTFCL349d2OXKF1LqPP5iFWoX6aMKTSJZ"

        dialog = tk.Toplevel(self.root)
        dialog.title("Поддержать разработчика")
        dialog.geometry("420x240")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.geometry(f"+{self.root.winfo_x() + 40}+{self.root.winfo_y() + 40}")

        container = ttk.Frame(dialog, padding=15)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container, 
            text="Поддержка криптовалютой", 
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(
            container, 
            text="Монета: USDT | Сеть: TON (Trust Wallet)\nАдрес кошелька:", 
            foreground="gray"
        ).pack(anchor="w", pady=(0, 5))

        address_entry = ttk.Entry(container, font=("Consolas", 9))
        address_entry.insert(0, USDT_ADDRESS)
        address_entry.config(state="readonly")
        address_entry.pack(fill="x", pady=(0, 10))

        def copy_address():
            self.root.clipboard_clear()
            self.root.clipboard_append(USDT_ADDRESS)
            self.root.update()
            btn_copy.config(text="Скопировано!")
            dialog.after(2000, lambda: btn_copy.config(text="Копировать адрес"))

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill="x", side="bottom")

        btn_copy = ttk.Button(btn_frame, text="Копировать адрес", command=copy_address)
        btn_copy.pack(side="left")

        ttk.Button(btn_frame, text="Закрыть", command=dialog.destroy).pack(side="right")