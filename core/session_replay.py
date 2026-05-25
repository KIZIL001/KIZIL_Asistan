"""KIZIL Oturum Replay Altyapısı - Deterministik oturum tekrarı."""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional

class SessionRecorder:
    """Bir oturumdaki kullanıcı girdilerini kaydeder."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.turns: List[Dict] = []
    
    def record_turn(self, user_input: str, assistant_output: str, metadata: Optional[Dict] = None) -> None:
        self.turns.append({
            'input': user_input,
            'output': assistant_output,
            'metadata': metadata or {}
        })
    
    def save(self, directory: str = 'sessions') -> str:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        path = dir_path / f'{self.session_id}.json'
        data = {
            'session_id': self.session_id,
            'turns': self.turns,
            'checksum': self._compute_checksum()
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        return str(path)
    
    def _compute_checksum(self) -> str:
        serialized = json.dumps(self.turns, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

class SessionReplayer:
    """Kaydedilmiş bir oturumu tekrar oynatır ve karşılaştırır."""
    def __init__(self, session_path: str):
        with open(session_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.session_id = self.data['session_id']
        self.turns = self.data['turns']
        self.original_checksum = self.data.get('checksum')
    
    def verify_checksum(self) -> bool:
        serialized = json.dumps(self.turns, sort_keys=True, ensure_ascii=False)
        current = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
        return current == self.original_checksum
    
    def replay(self, response_fn) -> Dict:
        """response_fn: kullanıcı girdisini alıp asistan yanıtı döndüren fonksiyon."""
        results = []
        all_match = True
        for i, turn in enumerate(self.turns):
            actual_output = response_fn(turn['input'])
            expected_output = turn['output']
            match = (actual_output.strip() == expected_output.strip())
            if not match:
                all_match = False
            results.append({
                'turn': i + 1,
                'input': turn['input'],
                'expected': expected_output,
                'actual': actual_output,
                'match': match
            })
        return {
            'session_id': self.session_id,
            'all_match': all_match,
            'total_turns': len(self.turns),
            'matched': sum(1 for r in results if r['match']),
            'results': results
        }
