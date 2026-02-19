import logging
import os
import re
from pathlib import Path

def normalize_revision(rev: str) -> str:
    mapping = {
        "А": "A", "В": "B", "Е": "E", "К": "K",
        "М": "M", "Н": "H", "О": "O", "Р": "P",
        "С": "C", "Т": "T", "У": "Y", "Х": "X",
    }
    return "".join(mapping.get(ch, ch) for ch in rev)


def extract_with_regex(text, pattern, label):
    reg = re.search(pattern, text)
    if reg:
        value = reg.group()
        logging.info(f"{label} = {value}")
        return value
    logging.warning(f"{label} not found in: {text}")
    return None

def extract_base_folder(filename):
    # Извлекаем всё до первого "_"
    return filename.split("_")[0]

# def extract_project_code(folder_name):
#     return extract_with_regex(folder_name, r'\d{3}', "Project code")


def match_pattern(filename, pattern):
    reg = re.search(pattern, filename)
    return reg.group() if reg else None


# def extract_section_code(filename):
#     # Ищем 0407.000
#     return extract_with_regex(filename, r'\d{4}[\. ]\d{3}', "Section code")

def extract_section_code(filename):
    return extract_with_regex(filename, r'\d{4}[\. \-_]\d{3}', "Section code")


def extract_project_code(folder_name):
    parts = folder_name.split("-")
    for part in parts:
        if part.isdigit() and len(part) == 3:
            return part
    logging.warning(f"Project code not found in: {folder_name}")
    return None

# def extract_subfolder_code(filename):
#     reg = re.search(r'(^GPNG-GEP-RD-[\d\.]+-\d+-[A-Z0-9]+-[A-Z0-9]+)', filename)
#     return reg.group() if reg else None

def extract_subfolder_code(filename):
    """
    Извлекает код подпапки из имени файла.
    Исключает ADRC-папки и файлы.
    Поддерживает оба формата:
      - GPNG-GEP-RD-0407.000-000-PI-TK-SPE-002
      - GEP-ASPA-GPNG-003-TRA-0138
    """

    # 1. Полное исключение ADRC
    if filename.startswith("ADRC-GPNG-GEP-RD"):
        return None

    # 2. Формат типа GPNG-GEP-RD-0407.000-000-PI-TK-SPE-002
    reg = re.match(r'^[A-Z]+-[A-Z]+-[A-Z]+-[\d\.]+-\d+-[A-Z0-9]+-[A-Z0-9]+', filename)
    if reg:
        return reg.group()

    # 3. Формат типа GEP-ASPA-GPNG-003-TRA-0138
    reg = re.match(r'^[A-Z]+-[A-Z]+-[A-Z]+-\d+-[A-Z0-9]+-\d+', filename)
    if reg:
        return reg.group()

    return None

# def extract_subfolder_code(filename):
#     # Берём всё до _rXX или до расширения
#     match = re.match(r'^(.+?)(?=_r\d+|_r[A-Za-zА-Яа-я]+|\.pdf|\.doc|\.docx|\.xls|\.xlsx|\.xlsm|\.dwg)', filename)
#     if match:
#         return match.group(1)
#     return None


# def extract_revision(filename):
#     reg = re.search(r'_r([A-Za-zА-Яа-яЁё0-9]+)', filename)
#     if reg:
#         return reg.group(1)
#     logging.warning(f"Revision not found in: {filename}")
#     return None

def extract_revision(filename):
    """
    Извлекает ревизию из имени файла.
    Поддерживает:
    - rXX
    - r XX
    - r_XX
    - r-XX
    - r.XX
    Игнорирует хвосты типа _RU, .zip и т.п.
    """
    name, _ = os.path.splitext(filename)

    # Ищем rXX с любым разделителем, но захватываем только саму ревизию
    match = re.search(r'[_\-\.\s]r[_\-\.\s]?([A-Za-zА-Яа-яЁё0-9]{1,3}|VOID)(?=[_\-\.\s]|$)', name)
    if match:
        raw_rev = match.group(1)
        norm_rev = normalize_revision(raw_rev)
        return raw_rev, norm_rev
    # match = re.search(r'[_\-\.\s]r[_\-\.\s]?(VOID|[A-Za-zА-Яа-яЁё0-9]{1,3})(?=[_\-\.\s]|$)', name, re.IGNORECASE)
    # if match:
    #     return match.group(1)

    # Альтернатива: Рев. XX
    match = re.search(r'Рев[.\s_-]+([A-Za-zА-Яа-яЁё0-9]{1,3}|VOID)(?=[_\-\.\s]|$)', name)
    if match:
        raw_rev = match.group(1)
        norm_rev = normalize_revision(raw_rev)
        return raw_rev, norm_rev

    logging.warning(f"Revision not found in: {filename}")
    return None, None


# def extract_extension_file(filename):
#     return extract_with_regex(filename, r'\.[A-Za-z0-9]+$', "Extension")

def extract_extension_file(filename):
    return extract_with_regex(filename, r'\.[A-Za-zА-Яа-яЁё0-9]+$', "Extension")

def get_project_folder_name(folder_path: Path):
    # Если это корневая папка проекта
    if extract_project_code(folder_path.name):
        return folder_path.name

    # Если это вложенная папка — берём родителя
    if extract_project_code(folder_path.parent.name):
        return folder_path.parent.name

    return None
