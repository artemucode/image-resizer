import json
from pathlib import Path

class SettingsManager:
    # Имя файла настроек рядом с исполняемым файлом
    SETTINGS_FILE = Path("settings.json")

    DEFAULT_SETTINGS = {
        "save_path": "",
        "quality": 85
    }

    @classmethod
    def load_settings(cls) -> dict:
        """Загружает настройки из JSON файла или возвращает стандартные."""
        if cls.SETTINGS_FILE.exists():
            try:
                with open(cls.SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Гарантируем наличие всех необходимых ключей
                    return {
                        "save_path": data.get("save_path", cls.DEFAULT_SETTINGS["save_path"]),
                        "quality": data.get("quality", cls.DEFAULT_SETTINGS["quality"])
                    }
            except Exception as e:
                print(f"[OSRT] Ошибка чтения settings.json: {e}")
        
        return cls.DEFAULT_SETTINGS.copy()

    @classmethod
    def save_settings(cls, save_path: str, quality: int):
        """Сохраняет текущие настройки в JSON файл."""
        data = {
            "save_path": save_path or "",
            "quality": int(quality)
        }
        try:
            with open(cls.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[OSRT] Ошибка сохранения settings.json: {e}")