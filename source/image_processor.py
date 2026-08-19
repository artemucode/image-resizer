from pathlib import Path
from PIL import Image
from config import FORMATS

class ImageProcessor:
    @staticmethod
    def is_valid_image(file_path: str) -> bool:
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    @staticmethod
    def get_image_info(file_path: str):
        with Image.open(file_path) as img:
            return img.size

    @staticmethod
    def create_thumbnail(file_path: str, size=(160, 160)):
        with Image.open(file_path) as img:
            img_copy = img.copy()
            img_copy.thumbnail(size)
            return img_copy

    @staticmethod
    def process_single_image(
        file_path: str, 
        save_dir: str, 
        width: int, 
        height: int, 
        target_format: str, 
        quality: int, 
        strip_metadata: bool = True
    ):
        with Image.open(file_path) as img:
            resized_img = img.resize((width, height), Image.Resampling.LANCZOS)

            ext_map = {v: k for k, v in FORMATS.items()}
            target_ext = ext_map.get(target_format)

            out_ext = target_ext if target_ext else Path(file_path).suffix.lower()
            img_format = FORMATS.get(out_ext)

            if not img_format:
                raise ValueError(f"Неподдерживаемый формат ({out_ext})")

            # Конвертируем прозрачность в RGB для JPEG
            if img_format == "JPEG" and resized_img.mode in ("RGBA", "LA", "P"):
                resized_img = resized_img.convert("RGB")

            # Удаление метаданных (EXIF, ICC профилей и т.д.)
            if strip_metadata:
                clean_img = Image.new(resized_img.mode, resized_img.size)
                clean_img.putdata(list(resized_img.getdata()))
                resized_img = clean_img

            output_name = f"{Path(file_path).stem}_resized{out_ext}"
            output_path = Path(save_dir) / output_name

            save_kwargs = {"format": img_format}
            if img_format in ("JPEG", "WEBP"):
                save_kwargs["quality"] = quality

            resized_img.save(output_path, **save_kwargs)
