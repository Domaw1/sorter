import logging
from datetime import datetime
import os

def setup_logger():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    # Основной лог
    logging.basicConfig( level=logging.INFO,
                         format="%(asctime)s — %(levelname)s — %(message)s",
                         handlers=[ logging.FileHandler(os.path.join(log_dir, "app.log"),
                                                        encoding="utf-8"), logging.StreamHandler() ] )

    error_handler = logging.FileHandler(os.path.join(log_dir, "errors.log"), encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter("%(asctime)s — %(levelname)s — %(message)s"))
    logging.getLogger().addHandler(error_handler)

def clear_log_files():
    log_dir = "logs"
    app_log = os.path.join(log_dir, "app.log")
    err_log = os.path.join(log_dir, "errors.log")

    # Закрываем все FileHandler, чтобы можно было очистить файлы
    for handler in logging.root.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            logging.root.removeHandler(handler)

    # Очищаем файлы
    open(app_log, "w", encoding="utf-8").close()
    open(err_log, "w", encoding="utf-8").close()

    # Перезапускаем логгер
    setup_logger()
