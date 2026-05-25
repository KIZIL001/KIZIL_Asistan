import json
import hashlib
from pathlib import Path
from typing import Any, Dict

class DeterministicDiff:
    def __init__(self, results_path: str = 'tests/regression_fixtures/regression_results.json'):
        self.results_path = Path(results_path)
        self.hash_path = self.results_path.with_suffix('.hash')

    def normalize(self, data: Any) -> Any:
        if isinstance(data, dict):
            normalized = {}
            for k, v in sorted(data.items()):
                if k == 'timestamp':
                    normalized[k] = 'DETERMINISTIC'
                else:
                    normalized[k] = self.normalize(v)
            return normalized
        elif isinstance(data, list):
            return [self.normalize(item) for item in data]
        elif isinstance(data, str):
            return data.strip()
        elif isinstance(data, (int, float, bool)) or data is None:
            return data
        return str(data)

    def compute_hash(self, data: Dict) -> str:
        normalized = self.normalize(data)
        serialized = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def load_previous_report(self) -> Dict:
        if self.results_path.exists():
            with open(self.results_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def save_hash(self, hash_value: str) -> None:
        self.hash_path.write_text(hash_value)

    def load_previous_hash(self) -> str:
        if self.hash_path.exists():
            return self.hash_path.read_text().strip()
        return None

    def compare(self, current_report: Dict) -> Dict:
        current_hash = self.compute_hash(current_report)
        previous_hash = self.load_previous_hash()
        previous_report = self.load_previous_report()

        diff_report = {
            'previous_hash': previous_hash,
            'current_hash': current_hash,
            'changed': previous_hash is not None and previous_hash != current_hash,
            'details': []
        }

        if diff_report['changed'] and previous_report is not None:
            for key in set(list(previous_report.keys()) + list(current_report.keys())):
                if key == 'timestamp':
                    continue
                prev_val = previous_report.get(key)
                curr_val = current_report.get(key)
                if prev_val != curr_val:
                    diff_report['details'].append(f'~ {key}')

        self.save_hash(current_hash)
        return diff_report
