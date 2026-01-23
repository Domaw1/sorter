import os

BASE_DIR = os.path.expanduser("~/Desktop/test")

SOURCE_DIR = BASE_DIR
TARGET_DIR = None
LOG_DIR = os.path.join(BASE_DIR, "log")


NAME_PATTERN = "GPNG-GEP-RD"

PROJECT_MAP = {
    "003": "Ранние работы",
    "113": "Основной договор",
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc", ".docx",
    ".xls", ".xlsx", ".xlsm",
    ".dwg",
}

BLACK_LIST_EXTENSIONS = {
    ".lnk"
}

FILE_TYPE_MAP = {
    ".pdf": "пдф",
    # ".doc": "ред.формат",
    # ".docx": "ред.формат",
    # ".xls": "ред.формат",
    # ".xlsx": "ред.формат",
    # ".xlsm": "ред.формат",
    # ".dwg": "ред.формат",
}

DEFAULT_CATEGORY = "Неизвестный проект"
