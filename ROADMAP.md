# KIZIL Asistan – Yol Haritası ve Mimari Gelişim Planı

Durum: v0.4-stable-runtime
Mimari Model: Sequential Local AI Runtime
Disiplin: Deterministik, modüler, düşük bağımlılık, kontrollü sadelik

---

# 1. PROJE FELSEFESİ

KIZIL Asistan bir:
- distributed system,
- enterprise orchestration platform,
- async agent framework,
- cloud-native runtime

DEĞİLDİR.

KIZIL:
- tek process,
- sequential çalışan,
- yerel makinede çalışan,
- deterministik davranış hedefleyen,
- modüler AI runtime sistemidir.

Temel öncelik:
kararlılık > sadelik > kontrol edilebilirlik > genişleme.

---

# 2. DEĞİŞTİRİLEMEZ MİMARİ KURALLAR

Aşağıdaki sınırlar ASLA aşılmaz:

- asyncio yasak
- threading yasak
- multiprocessing yasak
- queue.Queue yasak
- harici broker sistemleri yasak
- pip bağımlılığı eklemek yasak
- enterprise design pattern kullanımı yasak
- orchestrator.py şişirilemez
- mevcut dosyalar tamamen yeniden yazılamaz
- replace-patch dışında değişiklik yapılamaz

Yasak enterprise örnekleri:
- Observer
- AbstractFactory
- ServiceContainer
- DependencyInjection
- DistributedWorkers
- EventDrivenArchitecture
- CQRS
- MessageBroker yapıları

---

# 3. MEVCUT SİSTEM DURUMU

## Güçlü Yanlar

- Modüler yapı
- Atomik yazma sistemi
- Vektör hafıza
- Otonom araç kullanımı
- Çok adımlı planlama
- Retry mekanizması
- Güvenlik katmanları
- Plugin altyapısı
- Context budama farkındalığı

## Mevcut Riskler

| Risk | Öncelik |
|------|----------|
| Task sistemi state-aware değil | Orta |
| Plugin izin sistemi eksik | Orta |
| Tool timeout sistemi eksik | Düşük-Orta |
| Context büyümesi | Orta |
| Orchestrator şişme riski | Orta |

---

# 4. FAZ PLANI

## Faz 0 — Stabil Runtime ✅

Tamamlandı:
- Atomik yazma
- Retry sistemi
- Memory geliştirmeleri
- Otonom workflow başlangıcı
- Tool karar sisteminin LLM'e devri

---

## Faz 1 — Mimari Disiplin ✅

Tamamlandı:
- SYSTEM_RULES.md
- ARCHITECTURE.md
- DEVELOPMENT_PROTOCOL.md
- Sequential-only disiplin
- Replace-patch protokolü

---

## Faz 2 — Task Execution Engine

Amaç:
Görev sistemini deterministik state machine yapısına geçirmek.

### 2.1 Task State Machine
Dosya:
- modules/tasks/task_manager.py

Hedef:
- pending
- running
- done
- failed

durum geçişlerini desteklemek.

---

### 2.2 Basit Görev Bağımlılığı

Amaç:
Parent task tamamlanmadan child task çalışamaz.

NOT:
Topological sorting,
graph engine,
workflow DAG sistemi
EKLENMEYECEK.

---

### 2.3 Retry Sistemi

Amaç:
Başarısız görevlerin sınırlı tekrar denenmesi.

Kurallar:
- max_retry
- exponential backoff YOK
- async retry YOK
- background retry YOK

---

### 2.4 Execution Context

Amaç:
Her görevin kendi execution context bilgisini taşıması.

Örnek:
- input
- retry_count
- created_at
- last_error

---

## Faz 3 — Güvenlik ve Kontrol

### 3.1 Plugin Permission System

Dosya:
- modules/plugins/plugin_loader.py

Amaç:
Plugin yetkilerini sınırlamak.

Manifest örneği:
- allowed_tools
- allowed_paths
- allow_network

---

### 3.2 Tool Timeout Sistemi

Dosya:
- modules/tools/tool_manager.py

Amaç:
Araçların sonsuza kadar çalışmasını önlemek.

NOT:
OS-level sandbox YOK.
Containerization YOK.
Resource virtualization YOK.

Sadece:
- timeout
- exception handling
- güvenli fail-state

---

### 3.3 Context Budget Manager

Dosya:
- modules/chat/chat_module.py

Amaç:
LLM context büyümesini kontrol etmek.

Kurallar:
- proaktif budama
- summary fallback
- duplicate cleanup
- recursive growth engeli

---

## Faz 4 — Uzun Vadeli Araştırmalar

Bu faz ZORUNLU değildir.
Sadece ihtiyaç oluşursa değerlendirilir.

### 4.1 Hot / Cold Memory

Sık kullanılan anılar RAM önbelleğinde tutulabilir.

---

### 4.2 Incremental Reindex Araştırması

Sadece:
vector store performansı gerçekten sorun olursa değerlendirilecek.

---

### 4.3 Ephemeral Reasoning Notes

Amaç:
LLM'in kısa süreli geçici düşünce notları oluşturabilmesi.

Kurallar:
- RAM'de tutulur
- conversation history'ye yazılmaz
- export edilmez
- vector store'a kaydedilmez

---

# 5. TEST STRATEJİSİ

Her faz sonrası zorunlu:

- manuel smoke test
- tool dry-run testleri
- task chain edge-case testleri
- memory corruption testleri
- retry davranış testleri
- export/import bütünlük testi
- context prune testleri

Kod yazıldı ≠ sistem güvenli.

---

# 6. GELİŞTİRME AKIŞI

Her geliştirme şu sırayla ilerler:

Analiz
→ Risk değerlendirmesi
→ Onay
→ Replace-patch
→ Test
→ Commit
→ Snapshot

Kod üretmeden önce:
- hangi dosyanın değişeceği,
- neden değişeceği,
- riskin ne olduğu
açıklanmalıdır.

---

# 7. PROJE HEDEFİ

KIZIL'ın hedefi:
genel amaçlı enterprise platform olmak değildir.

Hedef:
- güvenilir,
- sade,
- yerel çalışan,
- kontrollü,
- modüler,
- deterministic AI runtime sistemi olmaktır.
