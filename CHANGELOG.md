# KIZIL Asistan – Değişiklik Günlüğü (Changelog)

## v1.1.0 – Production Engineering (2026-05-26)

### Yeni Özellikler (Capability Expansion Yok – Yalnızca Operasyonel Olgunluk)
- **Faz 1 – Release Engineering & Recovery**
  - Sürüm manifestosu (`storage/release.json`)
  - Safe‑mode kontrolü (binary)
  - Poison pill koruması
  - Atomik dosya işlemleri (`utils/file_utils.py`)
  - Kurtarma aracı (`recovery.py`)

- **Faz 2 – Stability Watchdog**
  - Pasif kararlılık gözlemcisi (`core/stability_watchdog.py`)
  - Anormal kapanış tespiti (clean_exit bayrağı)
  - Heartbeat yalnızca RAM'de

- **Faz 3 – Config Immutability & Rollback**
  - Config dondurma (freeze/unfreeze)
  - Binary drift tespiti
  - Otomatik yedekleme ve rollback (maks. 5 yedek)

- **Faz 4 – Forensic Logging**
  - Request ID zinciri (`[req_XXXXXX]`)
  - Log state pollution önlemi

- **Faz 5 – Data Integrity**
  - JSON bozulma tespiti ve kısmi kurtarma
  - Kritik/operasyonel dosya ayrımı
  - Tüm JSON'lara `schema_version: "1.0"` enjeksiyonu

- **Faz 6 – Safe Failure Modes**
  - Cascade failure korumalı `safe_call` sarmalayıcı
  - Hardcoded güvenli varsayılan

- **Faz 7 – Telemetry Archive & Dashboard**
  - Terminal tabanlı operasyonel sağlık paneli (`panel` komutu)
  - Salt‑okunur, bozuk dosyada `[VERI YOK]`

- **Faz 8 – Session Fuzzer**
  - Deterministik varyasyon motoru (seed=42)
  - 200+ fuzzer senaryosu
  - `--fuzz` flag ile opsiyonel çalıştırma

### Anayasa Güncellemeleri
- SYSTEM\_RULES.md: Production Stability Doctrine, Release Discipline Rule, Data Contract Rule eklendi.
- DEVELOPMENT\_PROTOCOL.md: Regression Governance eklendi.
- ARCHITECTURE.md: Architectural Maturity State eklendi.

### Test Durumu
- 51 regresyon testi: %100 başarılı
- 200 fuzzer senaryosu: %100 yüklendi ve şema doğrulandı
- Determinizm: korundu
- Bellek sızıntısı: yok
- Yeni bağımlılık: sıfır

### Kalan Fazlar (Gözlem Aşamasında)
- Faz 9: Behavioral Drift Detector
- Faz 10: Auto‑Fixture Suggestion
- Faz 11: Schema Governance
