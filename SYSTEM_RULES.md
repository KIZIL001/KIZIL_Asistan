# KIZIL Asistan — Sistem Kuralları

KIZIL Asistan:
tek kullanıcı için geliştirilmiş,
yerel çalışan,
modüler,
deterministik,
minimalist,
otonom destekli bir AI runtime sistemidir.

Bu proje:
enterprise architecture,
distributed systems,
cloud-native infrastructure,
multi-agent ecosystems
ve production-scale orchestration sistemi DEĞİLDİR.

Tüm geliştirmeler aşağıdaki kurallara uymak zorundadır.

---

# 1. TEMEL FELSEFE

Öncelik sırası:

1. Stabil çalışma
2. Deterministik davranış
3. Basitlik
4. Güvenlik
5. Genişletilebilirlik
6. Performans optimizasyonu

KIZIL:
minimal,
anlaşılır,
debug edilebilir,
kontrollü büyüyen bir sistem olarak kalmalıdır.

---

# 2. MİMARİ SINIRLAR

Sistem:

* single process
* sequential runtime
* local runtime
* synchronous execution

mantığında çalışır.

Aşağıdakiler yasaktır:

* asyncio
* multiprocessing
* distributed systems
* worker pools
* queue brokers
* microservices
* kubernetes
* docker orchestration
* cloud infrastructure
* realtime distributed agents
* autonomous recursive loops
* self-modifying architecture

---

# 3. GELİŞTİRME FELSEFESİ

Yeni özellik eklemeden önce:

* mevcut yapı korunmalı
* minimal patch uygulanmalı
* gereksiz abstraction engellenmeli
* mevcut mimari büyütülmemeli

YAGNI ilkesi zorunludur:
"You Aren’t Gonna Need It"

Gelecekte lazım olabilir düşüncesiyle sistem büyütülemez.

---

# 4. DOSYA VE MODÜL KURALLARI

Yeni modül gerekiyorsa:
önce mevcut modüller değerlendirilmelidir.

Mevcut modüller zorla büyütülemez.

Orchestrator:
tanrı nesnesine dönüşemez.

Her modül:
tek sorumluluk prensibiyle çalışmalıdır.

---

# 5. GÜVENLİK FELSEFESİ

Sistem:
varsayılan olarak güvenli davranmalıdır.

Asla:

* shell=True
* sınırsız subprocess
* kontrolsüz dosya erişimi
* proje dışına çıkış
* sınırsız internet erişimi

kullanılamaz.

---

# 6. AI DAVRANIŞ KURALI

AI modelleri:

* mevcut mimariyi bozamaz
* yeni sistem önermeden önce mevcut yapıyı analiz etmek zorundadır
* minimal çözüm üretmelidir
* enterprise mimariye kayamaz
* gereksiz bağımlılık ekleyemez

AI:
mimariyi yeniden tasarlayamaz.
Sadece mevcut sistemi kontrollü geliştirebilir.

---

# 7. KIZIL PRENSİBİ

KIZIL:
küçük ama keskin,
minimal ama güçlü,
basit ama sağlam
kalmalıdır.
