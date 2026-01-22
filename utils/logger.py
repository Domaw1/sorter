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