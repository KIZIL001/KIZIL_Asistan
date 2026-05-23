import logging
import os
from datetime import datetime

class Logger:
    """Hem konsola hem dosyaya log yazan basit loglayıcı."""

    def __init__(self, log_dir="storage", log_file="kizil.log"):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, log_file)
        os.makedirs(self.log_dir, exist_ok=True)

        # Python'un dahili logging modülünü yapılandır
        self.logger = logging.getLogger("KIZIL")
        self.logger.setLevel(logging.DEBUG)

        # Dosyaya yazıcı
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        file_handler.setFormatter(file_format)

        # Konsola yazıcı
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_format)

        # Handler'ları ekle
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)
