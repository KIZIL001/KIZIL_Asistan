
import sys

# Eğer sistemde gerçek bir RuntimeDiagnostics sınıfı yoksa safe_call'un çökmesini önleyen deterministik yapı
if 'RuntimeDiagnostics' not in globals() and 'RuntimeDiagnostics' not in dir(sys.modules[__name__]):
    class RuntimeDiagnostics:
        @staticmethod
        def register_failure(*args, **kwargs):
            pass
        @staticmethod
        def report(*args, **kwargs):
            return {}

"""
Safe Failure Modes – Güvenli bozulma davranışı.
Tüm çağrılar safe_call ile sarılır; cascade failure önlenir.
"""
import traceback


def safe_call(func, *args, fallback=None, context="general", _logger=None, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if _logger:
            _logger.error(f"[{context.upper()}] Hata: {str(e)}")
        else:
            print(f"[{context.upper()}] Hata: {str(e)}")
        return fallback() if callable(fallback) else fallback
def _hardcoded_safe_default():
    """Her türlü senaryoda güvenli varsayılan."""
    return None