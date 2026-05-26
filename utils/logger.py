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
        prefix = f"[{self._request_id}] " if self._request_id else ""
        self.logger.debug(prefix + msg)

    def info(self, msg):
        prefix = f"[{self._request_id}] " if self._request_id else ""
        self.logger.info(prefix + msg)

    def warning(self, msg):
        prefix = f"[{self._request_id}] " if self._request_id else ""
        self.logger.warning(prefix + msg)

    def error(self, msg):
        prefix = f"[{self._request_id}] " if self._request_id else ""
        self.logger.error(prefix + msg)

    def critical(self, msg):
        prefix = f"[{self._request_id}] " if self._request_id else ""
        self.logger.critical(prefix + msg)

    def set_request_id(self, request_id: str) -> None:
        """Her işlem (tur) başında çağrılır. Log satırlarına prefix olarak eklenir."""
        self._request_id = request_id

    def clear_request_id(self) -> None:
        """İşlem sonunda request_id'yi temizler (log state pollution önlemi)."""
        self._request_id = ""
