"""KIZIL Asistan - Gerileme Tespit Testleri."""
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime

FIXTURE_PATH = Path(__file__).parent / "regression_fixtures" / "regression_fixtures.json"
RESULTS_PATH = Path(__file__).parent / "regression_fixtures" / "regression_results.json"

def load_fixtures():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def test_uncertainty_filter(tests):
    from core.uncertainty_filter import apply_filter
    results = []
    for t in tests:
        result = apply_filter(t["input"])
        passes = True
        errors = []
        for expected in t.get("expected_contains", []):
            if expected not in result:
                passes = False
                errors.append(f"'{expected}' bulunamadi")
        for not_expected in t.get("expected_not_contains", []):
            if not_expected in result:
                passes = False
                errors.append(f"'{not_expected}' olmamaliydi")
        results.append({
            "id": t["id"],
            "pass": passes,
            "errors": errors,
            "output_hash": hash_text(result),
            "output_preview": result[:100]
        })
    return results

def test_decision_trace(tests):
    from modules.tools.tool_manager import ToolManager
    results = []
    for t in tests:
        try:
            tm = ToolManager()
            setup = t.get("setup", {})
            func = eval(setup.get("tool_func", "lambda msg='test': f'Islem tamam: {msg}'"))
            tm.register(
                setup.get("tool_name", "test_araci"),
                setup.get("tool_desc", ""),
                setup.get("tool_params", {}),
                func
            )
            result = tm.parse_and_execute(t["input"])
            passes = True
            errors = []
            for expected in t.get("expected_contains", []):
                if expected not in (result or ""):
                    passes = False
                    errors.append(f"'{expected}' bulunamadi")
            results.append({
                "id": t["id"],
                "pass": passes,
                "errors": errors,
                "output_hash": hash_text(result or ""),
                "output_preview": (result or "")[:100]
            })
        except Exception as e:
            results.append({
                "id": t["id"],
                "pass": False,
                "errors": [f"Istisna: {type(e).__name__}: {str(e)}"],
                "output_hash": "",
                "output_preview": ""
            })
    return results

def test_sanitize_input(tests):
    from modules.chat.chat_module import ChatModule
    chat = ChatModule.__new__(ChatModule)
    results = []
    for t in tests:
        result = chat._sanitize_input(t["input"])
        passes = True
        errors = []
        for expected in t.get("expected_contains", []):
            if expected not in result:
                passes = False
                errors.append(f"'{expected}' bulunamadi")
        for not_expected in t.get("expected_not_contains", []):
            if not_expected in result:
                passes = False
                errors.append(f"'{not_expected}' olmamaliydi")
        results.append({
            "id": t["id"],
            "pass": passes,
            "errors": errors,
            "output_hash": hash_text(result),
            "output_preview": result[:100]
        })
    return results

def test_context_poisoning(tests):
    from modules.chat.chat_module import ChatModule
    chat = ChatModule.__new__(ChatModule)
    # Mock: logger ve _log için gerekli attribute'ları ekle
    chat.logger = None  # _log metodu None'u tolere eder
    if not hasattr(chat, '_context_defense_enabled'):
        chat._context_defense_enabled = lambda: True
    results = []
    for t in tests:
        msg, history = chat._check_context_poisoning(t["input"], [])
        passes = True
        errors = []
        for expected in t.get("expected_contains", []):
            if expected not in msg:
                passes = False
                errors.append(f"'{expected}' bulunamadi")
        for not_expected in t.get("expected_not_contains", []):
            if not_expected in msg:
                passes = False
                errors.append(f"'{not_expected}' olmamaliydi")
        results.append({
            "id": t["id"],
            "pass": passes,
            "errors": errors,
            "output_hash": hash_text(msg),
            "output_preview": msg[:100]
        })
    return results

def test_jaccard_pruning(tests):
    from modules.chat.chat_module import ChatModule
    from core.llm_router import LLMRouter
    from utils.config import Config
    cfg = Config()
    router = LLMRouter(model=cfg._data["LLM_MODEL"], logger=None)
    chat = ChatModule(router)
    results = []
    for t in tests:
        inp = t["input"]
        result = chat._jaccard_prune(inp["history"], inp["user_msg"])
        passes = True
        errors = []
        min_len = t.get("expected_min_len", 0)
        max_len = t.get("expected_max_len", 999)
        if len(result) < min_len:
            passes = False
            errors.append(f"Uzunluk {len(result)} < {min_len}")
        if len(result) > max_len:
            passes = False
            errors.append(f"Uzunluk {len(result)} > {max_len}")
        results.append({
            "id": t["id"],
            "pass": passes,
            "errors": errors,
            "output_len": len(result)
        })
    return results


def test_prompt_firewall(tests):
    from modules.chat.prompt_firewall import check_firewall
    results = []
    for t in tests:
        result = check_firewall(t["input"]) or t["input"]
        passes = True
        errors = []
        for expected in t.get("expected_contains", []):
            if expected not in result:
                passes = False
                errors.append(f"'{expected}' bulunamadi")
        for not_expected in t.get("expected_not_contains", []):
            if not_expected in result:
                passes = False
                errors.append(f"'{not_expected}' olmamaliydi")
        results.append({
            "id": t["id"],
            "pass": passes,
            "errors": errors,
            "output_hash": hash_text(result),
            "output_preview": result[:100]
        })
    return results

def main():
    # Test izolatörü: KIZIL_TEST_MODE=1 ise safe-mode bypass ve temiz çevre
    import os
    if os.environ.get("KIZIL_TEST_MODE") == "1":
        # Temiz test ortamı: safe_mode_flag dosyasını yok say
        safe_flag = "storage/.safe_mode"
        if os.path.exists(safe_flag):
            os.remove(safe_flag)
        print("[TEST MODU] Safe-mode bypass edildi, test ortamı sıfırlandı.")

    fixtures = load_fixtures()
    all_results = {}
    total_pass = 0
    total_fail = 0
    
    test_runners = {
        "uncertainty_filter": test_uncertainty_filter,
        "decision_trace": test_decision_trace,
        "sanitize_input": test_sanitize_input,
        "context_poisoning": test_context_poisoning,
        "jaccard_pruning": test_jaccard_pruning,
        "prompt_firewall": test_prompt_firewall,
    }
    
    for category, data in fixtures.items():
        if category in test_runners:
            results = test_runners[category](data["tests"])
            all_results[category] = results
            passes = sum(1 for r in results if r["pass"])
            fails = len(results) - passes
            total_pass += passes
            total_fail += fails
            status = "OK" if fails == 0 else "FAIL"
            print(f"{status}: {category} -> {passes}/{len(results)} gecti")
            for r in results:
                if not r["pass"]:
                    print(f"  HATA {r['id']}: {r['errors']}")
        else:
            print(f"UYARI: {category} icin test runner bulunamadi")
    
    print(f"\n{'='*50}")
    print(f"Toplam: {total_pass} basarili, {total_fail} basarisiz")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_pass": total_pass,
        "total_fail": total_fail,
        "results": all_results
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Sonuclar kaydedildi: {RESULTS_PATH}")
    
    return 0 if total_fail == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
