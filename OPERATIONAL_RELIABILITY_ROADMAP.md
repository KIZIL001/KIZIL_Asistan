# KIZIL Asistan – Operasyonel Güvenilirlik Yol Haritası

**Sürüm:** 1.1 (Production-Grade Nihai)
**Tarih:** 2026-05-25
**Önceki Aşamalar:** 
- Hardening (Tamamlandı, 17/17)
- Intelligence Refinement (Tamamlandı, 16/16 test başarılı)
**Mevcut Durum:** v0.8-operational
**Amaç:** KIZIL'ı "sürekli gelişen AI projesi" olmaktan çıkarıp, "kararlı local runtime ürünü" haline getirmek.

---

## OPERATIONAL RELIABILITY PRECEDENCE RULE (Kesin Anayasa Maddesi)

Bundan sonraki hiçbir faz:
- yeni runtime modeli,
- yeni abstraction,
- yeni pipeline katmanı,
- yeni orchestration sistemi,
- yeni memory architecture,
- yeni framework

öneremez.

Yeni fazların tek amacı:
- mevcut davranışı ölçmek,
- regresyon bulmak,
- deterministikliği korumak,
- tool güvenilirliğini doğrulamak,
- hallucination etkisini azaltmak,
- uzun oturum stabilitesini izlemek,
- kullanıcı güvenini artırmak

olmalıdır.

**Her öneri:**
- minimal patch (tercihen 30, maksimum 80 satır),
- replace yöntemi,
- test stratejisi,
- rollback güvenliği (config anahtarı),
- telemetry doğrulaması

ile birlikte gelmelidir.

---

## Kritik Disiplinler (ChatGPT Onaylı)

### 1. Patch Budget Kuralı
Bir patch tercihen 30 satırı, maksimum 80 satırı geçmemelidir. Daha büyük değişiklikler parçalanmalıdır.

### 2. Refactor Freeze
Çalışan sistem davranışını değiştirmeyen kozmetik refactor yasaktır. "Temizlik", "modernizasyon" veya "iyileştirme" adı altında çalışan kodu değiştirmek yasaktır.

### 3. Emergency Disable Flags (Zaten Mevcut)
Her refinement sistemi config flag ile kapanabilmelidir:
- `ENABLE_UNCERTAINTY_FILTER`
- `ENABLE_DECISION_TRACE`
- `ENABLE_CONTEXT_POISONING_DEFENSE`
- `ENABLE_JACCARD_PRUNING`
- `ENABLE_RESPONSE_TEMPLATES`
- `ENABLE_TOOL_VERIFICATION`
- `ENABLE_PROMPT_FIREWALL`

### 4. Runtime Version Fingerprint
Her snapshot'ta `storage/runtime_fingerprint.json` oluşturulacak:
- commit hash
- enabled configs
- active refinement flags
- tool count
- plugin count
- roadmap phase
- determinism mode
- patch count

---

## Faz 1: Regression Observatory (Gerileme Gözlemevi)

**Amaç:** Her patch sonrası davranış kaymasını otomatik yakalamak.

**İçerik:**
- Golden test fixtures (mevcut `tests/regression_fixtures/` genişletilecek)
- Aynı seed + aynı config + aynı fixture altında deterministik çıktı doğrulaması
- Halüsinasyon regresyon takibi
- Araç çıktısı karşılaştırma
- Oturum tekrar oynatma (Gerçek LLM çağrısı yerine fixture replay tercih edilir; amaç model benchmark değil, runtime stabilitesidir.)

**Uygulama:**
- Mevcut `tests/regression_test.py` genişletilecek
- Çıktılar `regression_results.json`'da versiyonlanacak
- Hash tabanlı deterministik diff eklenecek
- Patch Budget: ~25 satır

**Başarı Kriteri:**
- 50+ fixture testi
- Aynı seed + config + fixture altında %100 deterministik çıktı
- Sürümler arası sıfır kayma toleransı

---

## Faz 2: Golden Session Corpus (Altın Oturum Külliyatı)

**Amaç:** Gerçek kullanım örneklerini saklayarak davranış değişimini yakalamak.

**Klasör:** `tests/golden_sessions/`

**İçerik:**
- Gerçek kullanıcı oturumları
- Problemli tool çağrıları
- Halüsinasyon örnekleri
- Uzun task chain'ler
- Context poisoning örnekleri
- Başarısız retry akışları

**Uygulama:**
- Yeni bağımlılık yok
- Mevcut `save_conversation` mekanizması genişletilecek
- Deterministik replay mekanizması eklenecek

**Başarı Kriteri:**
- En az 20 golden session kaydı
- Her yeni sürümde replay testi zorunlu

---

## Faz 3: Failure Corpus (Başarısızlık Külliyatı)

**Amaç:** Başarısız örnekleri saklayarak sistemin zayıf noktalarını izlemek.

**Klasör:** `tests/failure_corpus/`

**İçerik:**
- Halüsinasyon response'ları
- Sonsuz retry döngüleri
- Bozuk tool input'ları
- Context collapse örnekleri
- Yanlış tool seçimleri
- Prompt override girişimleri
- Bozuk memory retrieval'lar

**Uygulama:**
- `storage/failure_corpus/` altında otomatik kayıt
- Config anahtarı: `ENABLE_FAILURE_CORPUS`

**Başarı Kriteri:**
- Her hata türü için en az 3 örnek
- Regression testlerinde kullanılabilir olması

---

## Faz 4: Long Session Torture Tests (Uzun Oturum Testleri)

**Amaç:** 2-3 saatlik manuel kullanımı otomatikleştirmek.

**İçerik:**
- 1000 mesajlık otomatik replay (Gerçek LLM çağrısı yerine fixture replay tercih edilir)
- Özyinelemeli araç denemeleri
- Bağlam zehirlenmesi simülasyonları
- Hızlı görev oluşturma
- Bellek doygunluk testleri

**Uygulama:**
- `tests/torture/` altında test betikleri
- Kaynak tüketimi izlenecek
- Her test sonunda sistem tutarlılık kontrolü

**Başarı Kriteri:**
- 1000 mesaj sonunda determinizm bozulmamalı
- Bellek sızıntısı olmamalı
- Sıfır crash

---

## Faz 5: Runtime Diagnostics (Çalışma Zamanı Tanılama)

**Amaç:** Canlı kullanım sırasında sistemin neden bozulduğunu anlamak.

**İçerik:**
- Bellek basıncı metrikleri (mevcut runtime iç telemetri ile)
- Araç gecikme histogramı
- Yeniden deneme sıklığı
- Bağlam budama sıklığı
- Bağlam çökmesi tespiti
- Görev başarısızlık dağılımı

**Uygulama:**
- Yeni bağımlılık yok; yalnızca mevcut runtime iç telemetri verileri kullanılacak
- `storage/diagnostics/` altında periyodik dökümler
- Config anahtarı: `ENABLE_RUNTIME_DIAGNOSTICS`

**Başarı Kriteri:**
- En az 5 farklı metrik tipi
- Günlük otomatik rapor (deterministik format)
- Anomali tespitinde `[UYARI]` logu

---

## Faz 6: Determinism Validation (Determinizm Doğrulaması)

**Amaç:** Aynı girdinin zamanla farklı davranış üretmesini yakalamak.

**İçerik:**
- Yanıt hash'leme
- Araç seçim tutarlılığı
- Yeniden deneme yolu karşılaştırması
- Bellek erişim tutarlılığı

**Uygulama:**
- Mevcut telemetry/logging katmanına determinism kontrol hook'ları eklenecek (saf Python)
- Her LLM çağrısında girdi/çıktı hash'i alınacak
- Aynı girdi için farklı hash tespitinde alarm
- Config anahtarı: `ENABLE_DETERMINISM_GUARD`

**Başarı Kriteri:**
- 1000 çağrıda %100 hash eşleşmesi
- Sapma durumunda anında log

---

## Faz 7: Tool Reliability Layer (Araç Güvenilirliği Katmanı)

**Amaç:** Araçların güvenilirlik skorunu ölçmek.

**İçerik:**
- Araç başına başarı oranı
- Sahte başarı tespiti
- Halüsinasyonlu araç sonucu takibi
- Yeniden deneme etkinliği

**Uygulama:**
- Mevcut `_tool_fail_counts` ve `metrics` genişletilecek
- `storage/tool_reliability.json`
- Config anahtarı: `ENABLE_TOOL_RELIABILITY`

**Başarı Kriteri:**
- Her araç için günlük güvenilirlik yüzdesi
- Eşik altı araçlar için otomatik uyarı

---

## Faz 8: Prompt Discipline Validation (Komut Disiplini Doğrulaması)

**Amaç:** Refinement fazlarının prompt davranışını bozup bozmadığını görmek.

**İçerik:**
- Ayrıntı sapması (verbosity drift)
- Talimat geçersiz kılma tespiti
- Stil kararsızlığı
- Şablon aşırı uyumu tespiti

**Uygulama:**
- `tests/prompt_discipline/` altında özel testler
- Yanıt yapısı stabil kalmalı, aşırı format sapması olmamalı
- Config anahtarı: `ENABLE_PROMPT_DISCIPLINE`

**Başarı Kriteri:**
- 100 örnek üzerinde stil sapması minimal
- Yanıt yapısı stabil kalmalı

---

## Production Freeze Kriterleri

`v1.0-production-freeze` aşağıdaki koşullar sağlandığında ilan edilecektir:

- 30 gün crash yok
- Determinism regression yok
- Torture testleri stabil
- Halüsinasyon oranı eşik altında
- Bellek sızıntısı yok
- Replay testleri stabil

Bu noktadan sonra:
- Yeni özellik geliştirme DURUR
- Sadece bugfix, telemetry iyileştirmesi ve güvenlik yaması yapılır

---

## Uygulama Takvimi (Optimal Sıralama)
Regression Observatory → Hafta 1
Golden Session Corpus → Hafta 2
Failure Corpus → Hafta 3
Long Session Torture Tests → Hafta 4
Determinism Validation → Hafta 5
Tool Reliability Metrics → Hafta 6
Runtime Diagnostics → Hafta 7
Prompt Discipline → Hafta 8
Production Freeze Candidate → Hafta 9
30-Day Stability Observation → Hafta 10-14
v1.0-production-freeze → Hafta 15

text

---

## Anayasa Uyumluluk Taahhüdü

Bu yol haritasındaki hiçbir madde:
- yeni bağımlılık,
- asenkron/thread yapısı,
- dağıtık mimari,
- enterprise desen,
- yeni framework

içermez. Tüm geliştirmeler mevcut sequential, deterministik, minimal bağımlılıklı runtime üzerinde saf Python yamaları ile gerçekleştirilecektir.

---

## Rol Dağılımı (AI Kullanım Stratejisi)

| Model | Kullanım Alanı |
|-------|---------------|
| DeepSeek | Küçük patch üretimi, test yazımı, telemetry genişletme, deterministik helper logic |
| Gemini | Regression riski, gereksiz abstraction tespiti, architecture creep analizi, prompt drift, overengineering tespiti |
| Kullanıcı | Nihai karar: gerçekten gerekli mi? runtime'ı bozuyor mu? complexity getiriyor mu? rollback güvenli mi? |

---

**Son Gerçek:** Bir local AI runtime'ın değeri, en karmaşık olmasında değil, en öngörülebilir olmasındadır. KIZIL artık "AI oyuncak projesi" değil, "kararlı local runtime ürünü"dür. Amaç: daha fazla özellik değil, aynı davranışı aylar sonra bile stabil sürdürebilmek.
