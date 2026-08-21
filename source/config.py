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

# Динамически получаем допустимые расширения из ключей FORMATS
ALLOWED_EXTENSIONS = set(FORMATS.keys())

VERSION = "1.2"
APP_TITLE = f"OSRT v{VERSION}"
