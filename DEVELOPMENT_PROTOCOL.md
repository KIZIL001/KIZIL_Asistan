# KIZIL Asistan — Development Protocol

Bu belge:
KIZIL üzerinde çalışan tüm AI sistemleri için zorunlu geliştirme protokolüdür.

Bu kurallar:
Gemini,
DeepSeek,
ChatGPT
ve diğer tüm modeller için bağlayıcıdır.

---

# 1. PATCH KURALI

Kaynak dosyalar:
tamamen yeniden yazılamaz.

Değişiklikler:

* minimal patch
* lokal değişiklik
* kontrollü ekleme

mantığında yapılmalıdır.

Tam dosya üretimi yasaktır.

---

# 2. ANALİZ PROTOKOLÜ

Her geliştirme isteğinde AI:

1. Önce mevcut mimariyi analiz eder
2. Riskleri belirtir
3. Minimal çözüm önerir
4. Gereksiz büyümeyi engeller
5. Sonra patch üretir
Bir patch:
- tercihen 30 satırı,
- maksimum 80 satırı

geçmemelidir.

Daha büyük değişiklikler parçalanmalıdır.

Direkt kod üretmek yasaktır.

---

# 3. BAĞIMLILIK KURALI

Standart Python kütüphanesi dışında
yeni bağımlılık eklemek yasaktır.

Önce mevcut standart library çözümleri değerlendirilmelidir.

---

# 4. RUNTIME KURALI

Sequential runtime korunmalıdır.

Aşağıdakiler yasaktır:

* asyncio
* threading
* multiprocessing
* background workers
* distributed queues

---

# 5. LOG VE HATA YÖNETİMİ

Sessiz hata yasaktır.

Aşağıdakiler yasaktır:

* bare except
* except: pass
* loglanmayan hata
* kontrolsüz fallback

Her hata:
güvenli şekilde loglanmalıdır.

---

# 6. MİMARİ DİSİPLİN

AI:
mevcut sistemi yeniden tasarlayamaz.

Aşağıdakiler yasaktır:

* gereksiz abstraction
* premature optimization
* enterprise architecture
* speculative design
* geleceğe yönelik aşırı genişleme
Çalışan sistem davranışını değiştirmeyen kozmetik refactor yasaktır.
---

# 7. GELİŞTİRME STRATEJİSİ

Her geliştirme:

* küçük adımlar
* test edilebilir değişiklikler
* rollback yapılabilir patchler
* küçük commitler

şeklinde ilerlemelidir.

---

# 8. ORCHESTRATOR KORUMA KURALI

orchestrator.py:
tanrı nesnesine dönüştürülemez.

Yeni sorumluluklar:
uygun modüllere ayrılmalıdır.

---

# 9. GÜVENLİK KURALI

Asla:

* shell=True
* kontrolsüz subprocess
* sınırsız filesystem erişimi
* proje dışına yazma
* güvenlik bypass

kullanılamaz.

---

# 10. FINAL RULE

KIZIL:
minimal,
deterministik,
kontrollü,
debug edilebilir
bir sistem olarak kalmalıdır.

Her geliştirme:
bu prensibi korumak zorundadır.


## REGRESSION GOVERNANCE

Her değişiklik:
1. Regression fixture testlerinden geçmeli
2. Replay testleriyle doğrulanmalı
3. Determinism hash sapması üretmemeli
4. Yeni telemetry yükü oluşturmamalı
5. Config drift üretmemeli

Eğer bir değişiklik:
- yeni abstraction gerektiriyorsa,
- yeni lifecycle oluşturuyorsa,
- yeni orchestration mantığı istiyorsa,
- mevcut sequential akışı karmaşıklaştırıyorsa

REDDEDİLMELİDİR.