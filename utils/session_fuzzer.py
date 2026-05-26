"""
Session Fuzzer – Golden session'lardan deterministik test senaryosu üretir.
Seed kilitlidir, her çalıştırmada aynı 200+ fixture'ı üretir.
Hiçbir LLM çağrısı yapmaz.
"""
import json
import os
import random
import hashlib
from pathlib import Path

random.seed(42)  # Determinizm kilidi

FIXTURE_FILE = "tests/regression_fixtures/regression_fixtures.json"
OUTPUT_DIR = "tests/fuzzer_corpus"
MAX_FUZZ = 200


def _hash_id(text: str, rule: str) -> str:
    raw = f"{rule}:{text}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _load_inputs():
    with open(FIXTURE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    inputs = []
    for category, group in data.items():
        for t in group.get("tests", []):
            inp = t.get("input", "")
            if isinstance(inp, str) and inp.strip():
                inputs.append(inp)
    return inputs


def _vary(text: str) -> list[tuple[str, str]]:
    variations = []
    # 1. Boşluk varyasyonları
    variations.append(("bosluk_bas", " " + text))
    variations.append(("bosluk_son", text + " "))
    # 2. Büyük/küçük harf (pseudo-random ama seed'li)
    upper = ''.join(c.upper() if random.random() > 0.5 else c for c in text)
    variations.append(("karisik_harf", upper))
    # 3. Özel karakter ekle
    variations.append(("ozel_karakter", text + "!"))
    variations.append(("ozel_karakter_soru", text + "?"))
    # 4. Türkçe karakter indirgeme
    tr_dict = {"ç":"c","ğ":"g","ı":"i","ö":"o","ş":"s","ü":"u",
               "Ç":"C","Ğ":"G","İ":"I","Ö":"O","Ş":"S","Ü":"U"}
    ascii_text = "".join(tr_dict.get(c, c) for c in text)
    variations.append(("ascii", ascii_text))
    # 5. Uzunluk katlama
    if len(text) < 2000:
        variations.append(("cift_uzunluk", text + " " + text))
    # 6. Sınır değerler
    variations.append(("bos_string", ""))
    variations.append(("tek_karakter", text[0] if text else "x"))
    if len(text) < 4900:
        variations.append(("uzun_tekrar", (text + " ") * 20))
    return variations


def generate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inputs = _load_inputs()
    fixtures = []
    for inp in inputs[:50]:  # İlk 50 girdiyi kullan
        for rule, variant in _vary(inp):
            if len(fixtures) >= MAX_FUZZ:
                break
            fid = _hash_id(variant, rule)
            fixtures.append({
                "id": fid,
                "rule": rule,
                "input": variant,
                "expected_behavior": "deterministic"
            })
        if len(fixtures) >= MAX_FUZZ:
            break

    out_path = os.path.join(OUTPUT_DIR, "fuzzer_fixtures.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fixtures, f, indent=2, ensure_ascii=False)
    print(f"✓ {len(fixtures)} fuzzer fixture'ı üretildi: {out_path}")


if __name__ == "__main__":
    generate()
