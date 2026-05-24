import logging
import os
from logging.handlers import RotatingFileHandler


class Logger:
    def __init__(self, log_dir, log_file, log_level="INFO", debug_mode=False,
                 max_bytes=2_000_000, backup_count=3):
        self.logger = logging.getLogger("KIZIL")
        self.logger.setLevel(logging.DEBUG if debug_mode else getattr(logging, log_level.upper(), logging.INFO))

        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, log_file)

        # Rotating handler: dosya max_bytes'e ulaşınca yenisini açar, backup_count kadar eskiyi saklar
        fh = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
        fh.setLevel(logging.DEBUG if debug_mode else getattr(logging, log_level.upper(), logging.INFO))

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # Debug modunda terminale de yaz
        if debug_mode:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)
