import os
from pathlib import Path
from PIL import Image, ImageOps, ImageStat
from config import MAX_SIZE, FORMATS, ALLOWED_EXTENSIONS

class ImageProcessor:
    @staticmethod
    def is_valid_image(file_path: str) -> bool:
        """Проверяет, является ли файл поддерживаемым изображением."""
        ext = Path(file_path).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    @staticmethod
    def get_image_info(file_path: str) -> tuple[int, int]:
        """Возвращает ширину и высоту изображения."""
        with Image.open(file_path) as img:
            return img.size

    @staticmethod
    def create_thumbnail(file_path: str, max_size: tuple[int, int] = (180, 180)) -> Image.Image:
        """Создает превью для интерфейса."""
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            return img

    @staticmethod
    def process_single_image(
        file_path: str,
        save_dir: str,
        width: int,
        height: int,
        target_format: str = "Исходный",
        quality: int = 85,
        strip_metadata: bool = True,
        resize_mode: str = "Stretch"  # "Stretch", "Fit", "Crop"
    ):
        """Обрабатывает одно изображение с учетом режима масштабирования."""
        with Image.open(file_path) as img:
            if strip_metadata:
                # Предотвращает разворот по EXIF при удалении метаданных
                img = ImageOps.exif_transpose(img)

            # Выбор алгоритма изменения размера
            if resize_mode == "Crop":
                # Обрезка по центру под точный размер
                processed_img = ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)
            elif resize_mode == "Fit":
                # Вписывание с сохранением пропорций и добавлением полей
                img_copy = img.copy()
                img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)
                
                # Фоновый цвет (прозрачный для PNG/WEBP с альфа-каналом, иначе белый)
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    bg_color = (0, 0, 0, 0)
                    bg_mode = "RGBA"
                else:
                    bg_color = (255, 255, 255)
                    bg_mode = "RGB"

                processed_img = Image.new(bg_mode, (width, height), bg_color)
                
                # Центрирование
                paste_x = (width - img_copy.width) // 2
                paste_y = (height - img_copy.height) // 2
                
                if bg_mode == "RGBA" and img_copy.mode != "RGBA":
                    img_copy = img_copy.convert("RGBA")
                    
                processed_img.paste(img_copy, (paste_x, paste_y))
            else: # "Stretch"
                # Прямое растягивание
                processed_img = img.resize((width, height), Image.Resampling.LANCZOS)

            # Формирование имени и формата
            src_path = Path(file_path)
            orig_ext = src_path.suffix.lower()

            if target_format == "Исходный":
                out_ext = orig_ext
            else:
                fmt_map = {v: k for k, v in FORMATS.items()}
                out_ext = fmt_map.get(target_format, orig_ext)

            output_filename = f"{src_path.stem}_resized{out_ext}"
            output_path = Path(save_dir) / output_filename

            # Приведение режимов цвета для формата JPEG (он не поддержит RGBA)
            if out_ext in ('.jpg', '.jpeg') and processed_img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', processed_img.size, (255, 255, 255))
                if processed_img.mode == 'P':
                    processed_img = processed_img.convert('RGBA')
                background.paste(processed_img, mask=processed_img.split()[-1] if processed_img.mode == 'RGBA' else None)
                processed_img = background

            save_kwargs = {}
            if out_ext in ('.jpg', '.jpeg', '.webp'):
                save_kwargs['quality'] = quality

            if not strip_metadata and 'exif' in img.info:
                save_kwargs['exif'] = img.info['exif']

            processed_img.save(output_path, **save_kwargs)
