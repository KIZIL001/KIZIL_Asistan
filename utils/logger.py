import logging
import os

class Logger:
    def __init__(self, log_dir="storage", log_file="kizil.log", log_level="DEBUG", debug_mode=False):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, log_file)
        os.makedirs(self.log_dir, exist_ok=True)

        level = getattr(logging, log_level.upper(), logging.DEBUG)

        self.logger = logging.getLogger("KIZIL")
        self.logger.setLevel(level)
        self.logger.handlers.clear()

        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        self.logger.addHandler(file_handler)

        if debug_mode:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(console_handler)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)
