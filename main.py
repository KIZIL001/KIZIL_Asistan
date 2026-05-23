import argparse
from core.orchestrator import Orchestrator

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KIZIL Asistan")
    parser.add_argument("--model", default=None, help="Kullanılacak LLM modeli (varsayılan: phi3:mini)")
    parser.add_argument("--debug", action="store_true", help="Debug modunda çalıştır")
    args = parser.parse_args()

    app = Orchestrator(debug_mode=args.debug)
    if args.model:
        app.router.model = args.model

    if args.debug:
        app.logger.info(f"Debug modu aktif. Model: {app.router.model}")

    app.start()
