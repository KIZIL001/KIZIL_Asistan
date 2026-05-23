import os

class FileManager:
    """Temel dosya işlemleri için yardımcı sınıf."""

    @staticmethod
    def read_file(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Dosya bulunamadı: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write_file(path, content):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def list_files(directory, extension=None):
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Dizin bulunamadı: {directory}")
        files = []
        for e in os.listdir(directory):
            full = os.path.join(directory, e)
            if os.path.isfile(full) and (extension is None or e.endswith(extension)):
                files.append(e)
        return files