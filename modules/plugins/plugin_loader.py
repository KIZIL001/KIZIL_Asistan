"""Plugin tarayıcı, yükleyici ve doğrulayıcı."""
import os
import importlib.util
import traceback
from types import ModuleType
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from core.orchestrator import Orchestrator


class PluginLoader:
    """modules/plugins/ altındaki tüm .py dosyalarını tarar, doğrular ve yükler."""

    def __init__(self, orchestrator: "Orchestrator") -> None:
        self.orch = orchestrator
        self.plugin_dir = os.path.dirname(__file__)

    def _safe_log(self, level: str, msg: str) -> None:
        """Logger yoksa print'e düşer, AttributeError çıkmaz."""
        try:
            logger = self.orch.logger
            if logger:
                getattr(logger, level, logger.info)(msg)
            else:
                print(f"[{level.upper()}] {msg}")
        except Exception:
            print(f"[{level.upper()}] {msg}")

    def validate_plugin(self, filepath: str) -> tuple[bool, Union[ModuleType, str]]:
        """
        Bir plugin dosyasının standarda uygun olup olmadığını kontrol eder.
        Başarılıysa (True, modül_nesnesi), başarısızsa (False, hata_mesajı) döner.
        """
        if not os.path.isfile(filepath):
            return False, "Dosya bulunamadı."

        filename = os.path.basename(filepath)
        if filename.startswith("_") or not filename.endswith(".py"):
            return False, "Geçersiz dosya adı. '_' ile başlamamalı, .py bitmeli."

        name = filename[:-3]
        try:
            spec = importlib.util.spec_from_file_location(f"plugins.{name}", filepath)
            if spec is None or spec.loader is None:
                return False, "Modül spec oluşturulamadı."
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            if not hasattr(mod, "register"):
                return False, "'register(orch)' fonksiyonu bulunamadı."
            if not callable(mod.register):
                return False, "'register' bir fonksiyon değil."

            return True, mod
        except Exception as e:
            return False, f"Doğrulama hatası: {e}"

    def load_all(self) -> list[str]:
        """Tüm pluginleri tarar, doğrular ve yükler. Yüklenen isimleri döner."""
        loaded = []
        if not os.path.isdir(self.plugin_dir):
            return loaded

        for filename in sorted(os.listdir(self.plugin_dir)):
            if filename.startswith("_") or not filename.endswith(".py"):
                continue
            name = filename[:-3]
            path = os.path.join(self.plugin_dir, filename)

            valid, result = self.validate_plugin(path)
            if not valid:
                self._safe_log("warning", f"Plugin atlandı '{name}': {result}")
                continue

            mod = result
            try:
                mod.register(self.orch)
                loaded.append(name)
                self._safe_log("info", f"Plugin yüklendi: {name}")
            except Exception as e:
                self._safe_log("error", f"[PLUGIN HATASI] '{name}' register başarısız: {e}\n{traceback.format_exc()}")

        return loaded
