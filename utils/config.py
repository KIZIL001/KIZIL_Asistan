class Config:
    """Uygulama genelinde kullanılacak ayarları tutar."""
    # Depolama
    STORAGE_DIR = "storage"
    CONVERSATIONS_DIR = "conversations"
    LOG_FILE = "kizil.log"

    # Log seviyesi (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL = "DEBUG"

    # LLM ayarları
    LLM_MODEL = "phi3:mini"   # Ollama ile kullanılacak model

    # Varsayılan yanıtlar (yedek)
    DEFAULT_UNKNOWN_RESPONSE = "Henüz tam olarak anlayamadım. Biraz daha basit sormayı dene ya da 'yardım' yaz."
