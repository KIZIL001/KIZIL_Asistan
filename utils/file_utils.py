"""
Atomik dosya işlemleri yardımcıları.
Tüm kalıcı veri yazmaları .tmp + os.replace ile atomik yapılır.
Doğrudan hedef dosyaya yazmak yasaktır.
"""
import json
import os

MAX_BUFFER_BYTES = 10_485_760  # 10 MB statik sınır


def atomic_write_json(path: str, data) -> None:
    """JSON veriyi atomik olarak yazar. Hata durumunda orijinal dosya bozulmaz."""
    tmp_path = path + ".tmp"
    try:
        content = json.dumps(data, ensure_ascii=False, indent=2)
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > MAX_BUFFER_BYTES:
            raise ValueError(f"Veri boyutu {len(content_bytes)} byte, maksimum {MAX_BUFFER_BYTES} aşıldı.")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def atomic_read_json(path: str, default=None):
    """JSON dosyayı güvenli okur. Bozuksa default döner."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def safe_read_text(path: str, default: str = "") -> str:
    """Metin dosyasını güvenli okur, yoksa veya bozuksa default döner."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return default
