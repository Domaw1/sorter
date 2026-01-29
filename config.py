import os

BASE_DIR = os.path.expanduser("~/Desktop/test")

SOURCE_DIR = BASE_DIR
TARGET_DIR = None
LOG_DIR = os.path.join(BASE_DIR, "log")

import json

DEFAULT_CONFIG_PATH = "default_paths.json"

def load_default_paths():
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        return {"source": "", "target": ""}
    try:
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"source": "", "target": ""}

def save_default_paths(data: dict):
    with open(DEFAULT_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

NAME_PATTERN = r"GPNG-GEP-RD"

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

STATUS_LABELS = {
    "copied": "Скопировано",
    "duplicate": "Дубликат (не копировался)",
    "conflict": "Конфликт имён",
    "error": "Ошибка",
    "skipped_pattern": "Не было скопировано (не соответствует шаблону имени)",
    "warning": "Предупреждение",
}
