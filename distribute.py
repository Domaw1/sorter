import csv
import os
import shutil
import logging
from datetime import datetime

import config

from utils.file_parser import (
    extract_project_code,
    match_pattern,
    extract_section_code,
    extract_subfolder_code,
    extract_revision,
    extract_extension_file,
)

from utils.crc import crc32_of_file
from utils.logger import setup_logger
from utils.report import write_report


import os
import config

def build_target_path(category, section, subfolder, revision, file_type):
    # Базовая папка — та, что выбрал пользователь
    base = os.path.join(
        config.TARGET_DIR,
        category,
        section,
        subfolder
    )

    # Если есть ревизия — добавляем её
    if revision:
        base = os.path.join(base, "Ревизии", revision)

    # Папка типа файла (pdf / ред.формат)
    base = os.path.join(base, file_type)

    return base

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def write_report_(rows, filename):
    report_path = os.path.join("reports", filename)
    os.makedirs("reports", exist_ok=True)

    headers = [
        "Имя файла",
        "Исходный путь",
        "Конечный путь",
        "Категория",
        "Раздел",
        "Подпапка",
        "Ревизия",
        "Тип файла",
        "CRC",
        "Статус"
    ]

    with open(report_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)

    return report_path

def handle_duplicates(dst_file, src_file):
    src_crc = crc32_of_file(src_file)
    dst_crc = crc32_of_file(dst_file)

    if src_crc == dst_crc:
        return "duplicate", src_crc, dst_crc, dst_file, None

    base, ext = os.path.splitext(dst_file)
    new_dst = base + "_conflict" + ext
    logging.error("Name conflict: " + new_dst)
    return "conflict", src_crc, dst_crc, dst_file, new_dst


def process_file(folder_path, filename, category, report_rows):
    src_file = os.path.join(folder_path, filename)

    # 1. Проверка шаблона
    if not match_pattern(filename, config.NAME_PATTERN):
        logging.info(f"Пропуск: {filename} — не соответствует шаблону")
        return "skipped_pattern", filename, None

    # 2. Разбор имени
    section = extract_section_code(filename)
    subfolder = extract_subfolder_code(filename)
    revision = extract_revision(filename)
    ext = extract_extension_file(filename)

    if section is None:
        logging.error(f"Пропуск: {filename} — раздел не найден")
        return "error", filename, None

    if subfolder is None:
        logging.error(f"Пропуск: {filename} — подпапка не найдена")
        return "error", filename, None

    if ext is None:
        logging.error(f"Пропуск: {filename} — расширение не найдено")
        return "error", filename, None

    ext = ext.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        logging.warning(f"Пропуск: {filename} — недопустимое расширение {ext}")
        return "warning", filename, None

    file_type = config.FILE_TYPE_MAP.get(ext)
    if not file_type:
        logging.warning(f"Пропуск: {filename} — неизвестный тип файла")
        return "warning", filename, None

    # 3. Построение пути
    target_dir = build_target_path(category, section, subfolder, revision, file_type)
    ensure_dir(target_dir)
    dst_file = os.path.join(target_dir, filename)

    # 4. Проверка дубликатов
    status = "copied"
    src_crc = crc32_of_file(src_file)
    dst_crc = None

    if os.path.exists(dst_file):
        status, src_crc, dst_crc, old_dst, new_dst = handle_duplicates(dst_file, src_file)
        if status == "conflict":
            dst_file = new_dst
    else:
        old_dst = None
        new_dst = None

    # 5. Копирование
    if status in ("copied", "conflict"):
        ensure_dir(os.path.dirname(dst_file))
        shutil.copy2(src_file, dst_file)

    # 6. Логирование
    logging.info(
        f"{status.upper()} | {src_file} → {dst_file} | "
        f"Категория: {category} | Раздел: {section} | Подпапка: {subfolder} | Ревизия: {revision} | CRC: {src_crc}"
    )

    # 7. Отчёт
    report_rows.append([
        filename,
        src_file,
        dst_file,
        category,
        section,
        subfolder,
        revision,
        file_type,
        src_crc,
        status
    ])

    if status == "conflict":
        return status, old_dst, new_dst
    else:
        return status, dst_file, None

def main(progress_callback=None, stats_callback=None):
    setup_logger()
    report_rows = []

    stats = {
        "processed": 0,
        "copied": 0,
        "skipped_pattern": 0,
        "duplicates": 0,
        "conflicts": 0,
        "errors": 0,
        "report_path": "",
        "conflict_files": []
    }

    # Подсчёт общего количества файлов
    all_files = []

    for folder in os.listdir(config.SOURCE_DIR):
        folder_path = os.path.join(config.SOURCE_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        for f in os.listdir(folder_path):
            all_files.append((folder_path, f))

    total_files = len(all_files)

    processed = 0

    for folder_path, filename in all_files:
        project_code = extract_project_code(os.path.basename(folder_path))
        category = config.PROJECT_MAP.get(project_code, config.DEFAULT_CATEGORY)

        # status, fname = process_file(folder_path, filename, category, report_rows)

        status, p1, p2 = process_file(folder_path, filename, category, report_rows)

        stats["processed"] += 1

        if status == "error":
            stats["errors"] += 1
        elif status == "skipped_pattern":
            stats["skipped_pattern"] += 1
        elif status == "duplicate":
            stats["duplicates"] += 1
        elif status == "conflict":
            stats["conflicts"] += 1
            stats["conflict_files"].append((p1, p2))
        elif status == "copied":
            stats["copied"] += 1

        processed += 1

        if progress_callback:
            progress_callback(processed, total_files, filename)

    # Отчёт
    report_name = f"report_{datetime.now():%Y-%m-%d}.csv"
    report_path = write_report_(report_rows, report_name)

    if stats_callback:
        stats["report_path"] = report_path
        stats_callback(stats)

