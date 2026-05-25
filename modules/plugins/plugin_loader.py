"""Plugin tarayıcı, yükleyici ve doğrulayıcı."""
import os
import importlib.util
import traceback
from types import ModuleType
from typing import TYPE_CHECKING, Union
from modules.tools.tool_manager import ToolManager

if TYPE_CHECKING:
    from core.orchestrator import Orchestrator


class FilteredToolManager:
    def __init__(self, real_manager, allowed_tools, allowed_paths, allow_network):
        self._real = real_manager
        self.allowed_tools = allowed_tools
        self.allowed_paths = allowed_paths
        self.allow_network = allow_network

    def parse_and_execute(self, text):
        import re, json
        match = re.search(r'\[TOOL_CALL:(\w+)\]', text)
        if match:
            tool_name = match.group(1)
            if tool_name not in self.allowed_tools:
                return f"[HATA] '{tool_name}' aracı bu plugin için izinli değil."
            if not self.allow_network and (tool_name.startswith('browser_') or tool_name.startswith('http_')):
                return f"[HATA] '{tool_name}' ağ izni olmadığı için kullanılamaz."
            if tool_name in ('dosya_oku', 'dosya_yaz', 'dosya_listele'):
                try:
                    params_str = re.search(r'\[TOOL_CALL:\w+\]\s*(.*)', text, re.DOTALL)
                    if params_str:
                        params = json.loads(params_str.group(1).strip()) if params_str.group(1).strip() else {}
                        dosya_yolu = params.get('dosya_yolu', params.get('dizin', ''))
                        if dosya_yolu:
                            if not any(dosya_yolu.startswith(ap) for ap in self.allowed_paths):
                                return f"[HATA] '{dosya_yolu}' bu plugin için izinli bir yol değil."
                except Exception:
                    pass
        return self._real.parse_and_execute(text)

    def has_tool_call(self, text):
        return self._real.has_tool_call(text)


class PluginSandbox:
    def __init__(self, orch, manifest):
        self._orch = orch
        self._manifest = manifest
        self._filtered_tool_manager = None

    @property
    def tool_manager(self):
        if self._filtered_tool_manager is None:
            self._filtered_tool_manager = FilteredToolManager(
                self._orch.tool_manager,
                self._manifest["allowed_tools"],
                self._manifest["allowed_paths"],
                self._manifest["allow_network"]
            )
        return self._filtered_tool_manager

    @property
    def logger(self):
        return self._orch.logger



class PluginLoader:
    """modules/plugins/ altındaki tüm .py dosyalarını tarar, doğrular ve yükler."""

    def __init__(self, orchestrator: "Orchestrator") -> None:
        self.orch = orchestrator
        self.plugin_dir = os.path.dirname(__file__)
        self.plugin_manifests = {}

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

            # Manifest kontrolü
            if not hasattr(mod, "PLUGIN_MANIFEST"):
                return False, "PLUGIN_MANIFEST tanımlı değil."
            manifest = mod.PLUGIN_MANIFEST
            if not isinstance(manifest, dict):
                return False, "PLUGIN_MANIFEST bir dict olmalı."
            required_keys = {"allowed_tools", "allowed_paths", "allow_network"}
            missing = required_keys - set(manifest.keys())
            if missing:
                return False, f"Manifest eksik anahtarlar: {missing}"
            if not isinstance(manifest["allowed_tools"], list):
                return False, "allowed_tools bir liste olmalı."
            if not isinstance(manifest["allowed_paths"], list):
                return False, "allowed_paths bir liste olmalı."
            if not isinstance(manifest["allow_network"], bool):
                return False, "allow_network bir bool olmalı."

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
                mod.register(PluginSandbox(self.orch, mod.PLUGIN_MANIFEST))
                loaded.append(name)
                self.plugin_manifests[name] = mod.PLUGIN_MANIFEST
                self._safe_log("info", f"Plugin yüklendi: {name}")
            except Exception as e:
                self._safe_log("error", f"[PLUGIN HATASI] '{name}' register başarısız: {e}\n{traceback.format_exc()}")

        return loaded
