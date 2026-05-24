"""Plugin tarayıcı ve yükleyici."""
import os
import importlib.util
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.orchestrator import Orchestrator


class PluginLoader:
    """modules/plugins/ altındaki tüm .py dosyalarını tarar ve yükler."""

    def __init__(self, orchestrator: "Orchestrator") -> None:
        self.orch = orchestrator
        self.plugin_dir = os.path.dirname(__file__)

    def load_all(self) -> list[str]:
        """Tüm pluginleri yükler, yüklenen isimleri döner."""
        loaded = []
        if not os.path.isdir(self.plugin_dir):
            return loaded

        for filename in sorted(os.listdir(self.plugin_dir)):
            if filename.startswith("_") or not filename.endswith(".py"):
                continue
            name = filename[:-3]
            path = os.path.join(self.plugin_dir, filename)
            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{name}", path
                )
                if spec is None or spec.loader is None:
                    continue
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "register"):
                    mod.register(self.orch)
                    loaded.append(name)
            except Exception as e:
                msg = f"[PLUGIN HATASI] '{name}' yüklenemedi: {e}"
                print(msg)
                try:
                    self.orch.logger.error(f"{msg}\n{traceback.format_exc()}")
                except Exception:
                    pass
        return loaded
