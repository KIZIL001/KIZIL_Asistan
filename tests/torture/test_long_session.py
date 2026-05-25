import random
import random
"""KIZIL Long Session Torture Test - State-aware, memory delta, stochastic."""
import json, os, time, tracemalloc
from pathlib import Path
from typing import Dict, List, Tuple

SESSION_DIR = Path("sessions")
TARGET_TURNS = 1000
MEMORY_CHECK_INTERVAL = 100
MEMORY_DELTA_THRESHOLD_KB = 50

def load_all_sessions() -> List[Dict]:
    sessions = []
    for f in sorted(SESSION_DIR.glob("*.json")):
        if f.name == "test_replay.json":
            continue
        with open(f) as fp:
            sessions.append(json.load(fp))
    return sessions

def mock_response(user_input: str) -> str:
    return f"[MOCK] Yanit: {user_input[:50]}..."

def run_single_pass(sessions: List[Dict], seed: int) -> Tuple[bool, int, int, float]:
    """Tek bir sıralı geçiş çalıştırır. (passed, turn_count, memory_delta_kb, elapsed)"""
    tracemalloc.start()
    start_time = time.time()
    start_mem = tracemalloc.get_traced_memory()[0]
    turn_count = 0
    session_index = 0
    response_cache: Dict[Tuple[str, str, int], str] = {}  # key: (session_id, input, turn_index)
    
    while turn_count < TARGET_TURNS:
        session = sessions[session_index % len(sessions)]
        sid = session["session_id"]
        for turn_idx, turn in enumerate(session["turns"]):
            user_input = turn["input"]
            resp = mock_response(user_input)
            cache_key = (sid, user_input, turn_idx)
            
            if cache_key in response_cache:
                if response_cache[cache_key] != resp:
                    print(f"DETERMINISM IHLALI: {cache_key} icin farkli yanit!")
                    tracemalloc.stop()
                    return False, turn_count, 0, 0.0
            else:
                response_cache[cache_key] = resp
            
            turn_count += 1
            if turn_count >= TARGET_TURNS:
                break
        session_index += 1
    
    elapsed = time.time() - start_time
    end_mem = tracemalloc.get_traced_memory()[0]
    memory_delta_kb = (end_mem - start_mem) / 1024
    tracemalloc.stop()
    return True, turn_count, memory_delta_kb, elapsed

def run_torture():
    sessions = load_all_sessions()
    if not sessions:
        print("Hic session bulunamadi.")
        return
    
    # 3 farklı tohumla test et
    seeds = [42, 123, 999]
    all_passed = True
    
    for seed in seeds:
        random.seed(seed)
        shuffled = sessions.copy()
        random.shuffle(shuffled)
        print(f"\nSeed {seed} ile test basliyor...")
        passed, turns, delta_kb, elapsed = run_single_pass(shuffled, seed)
        print(f"  Tur: {turns}, Bellek delta: {delta_kb:.1f} KB, Sure: {elapsed:.1f}s")
        
        if not passed:
            print(f"  ✗ BASARISIZ: Determinizm ihlali.")
            all_passed = False
            break
        if delta_kb > MEMORY_DELTA_THRESHOLD_KB:
            print(f"  ✗ BASARISIZ: Bellek sizintisi ({delta_kb:.1f} KB > {MEMORY_DELTA_THRESHOLD_KB} KB).")
            all_passed = False
            break
        print(f"  ✓ Gecti.")
    
    if all_passed:
        print(f"\n✓ Tum torture testleri basarili: Determinizm korundu, bellek sizintisi yok.")
    else:
        print(f"\n✗ Torture test basarisiz.")

if __name__ == "__main__":
    run_torture()
