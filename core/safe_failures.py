"""
Safe Failure Modes – Güvenli bozulma davranışı.
Tüm çağrılar safe_call ile sarılır; cascade failure önlenir.
"""
import traceback


def safe_call(func, *args, fallback=None, context: str = "", _logger=None):
    """Fonksiyonu güvenli çağırır.
    Hata durumunda fallback (çağrılabilir veya sabit değer) döner.
    fallback de hata verirse hardcoded güvenli varsayılan döner.
    """
    try:
        return func(*args)
    except Exception as e:
        # Hatayı logla (varsa logger'a)
        if _logger:
            _logger.warning(f"Safe failure in '{context}': {e}")
        # fallback'i dene
        if callable(fallback):
            try:
                return fallback()
            except Exception:
                # Cascade failure – en dip güvenli varsayılan
                if _logger:
                    _logger.error(f"Cascade failure in fallback for '{context}'")
                return _hardcoded_safe_default()
        else:
            return fallback


def _hardcoded_safe_default():
    """Her türlü senaryoda güvenli varsayılan."""
    return None
