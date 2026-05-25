"""KIZIL Failure Corpus – Deterministik başarısızlık kaydı."""
import json, hashlib
from pathlib import Path
from typing import Optional

class FailureRecorder:
    def __init__(self, corpus_dir: str = 'tests/failure_corpus'):
        self.corpus_dir = Path(corpus_dir)
        self.corpus_dir.mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, category: str, error_msg: str) -> str:
        raw = f'{category}|{error_msg.strip()}'
        return hashlib.sha256(raw.encode()).hexdigest()[:20]

    def record(self, category: str, error_msg: str, context: Optional[dict] = None) -> str:
        error_hash = self._compute_hash(category, error_msg)
        filename = f'{category}_{error_hash}.json'
        filepath = self.corpus_dir / filename

        if filepath.exists():
            return str(filepath)

        entry = {
            'category': category,
            'error': error_msg,
            'context': context or {},
            'hash': error_hash
        }
        filepath.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding='utf-8')
        return str(filepath)

    def stats(self) -> dict:
        if not self.corpus_dir.exists():
            return {'total': 0, 'categories': {}}
        cats = {}
        for f in self.corpus_dir.glob('*.json'):
            try:
                data = json.loads(f.read_text())
                cat = data.get('category', 'unknown')
                cats[cat] = cats.get(cat, 0) + 1
            except:
                pass
        return {'total': sum(cats.values()), 'categories': cats}
