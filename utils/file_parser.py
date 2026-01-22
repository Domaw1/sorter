import logging
import os
import re


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

def extract_project_code(folder_name):
    return extract_with_regex(folder_name, r'\d{3}', "Project code")


def match_pattern(filename, pattern):
    reg = re.search(pattern, filename)
    return reg.group() if reg else None


def extract_section_code(filename):
    # Ищем 0407.000
    return extract_with_regex(filename, r'\d{4}\.\d{3}', "Section code")


def extract_subfolder_code(filename):
    reg = re.search(r'(^GPNG-GEP-RD-[\d\.]+-\d+-[A-Z0-9]+-[A-Z0-9]+)', filename)
    return reg.group() if reg else None


def extract_revision(filename):
    # Ищем _rC, _rA, _r01
    reg = re.search(r'_r([A-Za-z0-9]+)', filename)
    if reg:
        return reg.group(1)
    logging.warning(f"Revision not found in: {filename}")
    return None


def extract_extension_file(filename):
    return extract_with_regex(filename, r'\.[A-Za-z0-9]+$', "Extension")
