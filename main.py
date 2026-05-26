import argparse
import os
import sys
from core.orchestrator import Orchestrator
from core.safe_mode import is_safe_mode, enable_safe_mode, disable_safe_mode
from utils.file_utils import atomic_read_json
if __name__ == "__main__":
    # Test izolatörü: KIZIL_TEST_MODE=1 ise safe-mode bypass
    if os.environ.get("KIZIL_TEST_MODE") == "1":
        print("[TEST MODU] Safe-mode ve recovery bypass edildi.")
    elif is_safe_mode():
        print("⚠️  KIZIL safe-mode'da başlatılıyor.")
        print("   Kritik dosyalarda bozulma tespit edildi.")
        release = atomic_read_json("storage/release.json", {})
        print(f"   Sürüm: {release.get('version', 'bilinmiyor')}")
        print("   Recovery için 'python3 recovery.py' çalıştırın veya")
        print("   safe-mode'u devre dışı bırakmak için 'storage/.safe_mode' dosyasını silin.")
        # Safe-mode'da da çalışabilir, ama uyarı verdik
    else:
        disable_safe_mode()  # Önceki safe-mode kalıntısını temizle

    parser = argparse.ArgumentParser(description="KIZIL Asistan")
    parser.add_argument("--model", default=None, help="Kullanılacak LLM modeli (varsayılan: phi3:mini)")
    parser.add_argument("--debug", action="store_true", help="Debug modunda çalıştır")
    args = parser.parse_args()

    app = Orchestrator(debug_mode=args.debug)

    if args.model:
        app.router.model = args.model
        app.config.set("LLM_MODEL", args.model)

    if args.debug:
        app.logger.info(f"Debug modu aktif. Model: {app.router.model}")

    app.start()