# KIZIL Intelligence Refinement Roadmap
**Sürüm:** 3.0 (Minimal Runtime Engineering)  
**Tarih:** 2026-05-25  
**Önceki Aşama:** Hardening (Tamamlandı)  
**Amaç:** Behavioral precision ve runtime reliability. Yeni yetenek eklenmez; yalnızca mevcut davranış keskinleştirilir, doğrulanır, sınırlanır, açıklanabilir hale getirilir.

### REFINEMENT PRECEDENCE RULE
- Yeni capability eklenemez.
- Yeni runtime modeli, retrieval architecture, async yapı, abstraction layer, inference framework oluşturulamaz.
- Yalnızca: mevcut davranışı keskinleştirme, doğrulama, sınırlama, açıklanabilir kılma yapılır.
- Her değişiklik minimal patch olmalı, determinizmi bozmamalı, rollback güvenlikli olmalı, telemetri ile doğrulanmalı.

---

## Faz 1: Kural Tabanlı Halüsinasyon Azaltma (Rule-Based Hallucination Reduction)
**Hedef:** Modelin uydurma bilgi üretme etkisini, hiçbir model içi sinyale (logit, entropy) bağlı olmadan, yalnızca çıktı metni üzerinde deterministik desen eşleştirme ile azaltmak.

**Yöntem:**
- Mevcut `output_handler.py` içine `uncertainty_filter(text)` fonksiyonu ekle.
- Filtre, metindeki sayısal iddiaları (tarih, miktar, yüzde, büyük sayılar) ve kesinlik ifadelerini (`kesinlikle`, `her zaman`, `asla` gibi) regex ile yakala.
- Yakalanan her iddiayı, projede zaten bulunan güvenilir bilgi kırıntıları sözlüğü (`data/trusted_facts.json`) ile karşılaştır. Eşleşme yoksa cümlenin başına `[Kesin değil]` ekle.
- Hiçbir model parametresine erişilmez; tamamen deterministik string işlemidir.

**Risk Analizi:**
1. Risk: Düşük, yalnızca metin üzerinde çalışır.
2. Mimari etki: `output_handler.py` içinde bir fonksiyon çağrısı eklenir.
3. Regression riski: Gereksiz `[Kesin değil]` etiketleri eklenebilir; `ENABLE_UNCERTAINTY_FILTER=False` ile devre dışı bırakılabilir.
4. Memory etkisi: `trusted_facts.json` birkaç KB, ek yük yok.
5. Determinism: Tam deterministik, aynı girdiye her zaman aynı etiketleme.
6. Hallucination riski: Yeni halüsinasyon kaynağı oluşturmaz, var olanı görünür kılar.

**Uygulama:**
- Patch: `core/output_handler.py` sonuna `from .uncertainty_filter import apply_filter` ve dönüş satırına `return apply_filter(raw_text)`.
- Test: 20 adet uydurma içerikli metinle birim test; determinizm için 100 çağrı aynı sonuç.
- Rollback: Config anahtarı ile eski davranışa anında dönüş.
- Telemetri: Etiketlenen ifade sayısı loglanır.

---

## Faz 2: Deterministik Karar İzi (Decision Trace)
**Hedef:** Modelin neden belirli bir yanıtı seçtiğini, hangi aracı çağırdığını, hangi bellek kaydını kullandığını şeffaflaştırmak. (Citation değil, karar izi.)

**Yöntem:**
- Her yanıt üretimi sonrası, kullanılan tool (varsa), erişilen memory key’leri ve varsa tetiklenen kurallar basit bir `decision_log` listesine eklenir.
- Yanıtın sonuna isteğe bağlı olarak `[Karar: ...]` satırı eklenir (config ile kontrol edilir).
- Loglama tamamen mevcut `logger` ile yapılır, yeni bir sistem eklenmez.

**Risk Analizi:**
- Mimari etki: `pipeline.py` içinde bir sözlük toplanır ve çıktıya eklenir.
- Regression: Çıktı formatına bir satır eklenir, kapatılabilir.
- Determinism: Hangi tool’un seçileceği zaten deterministik; log da öyle olur.
- Embedding, vektör, retrieval yok.

---

## Faz 3: Bağlam Zehirlenmesine Karşı Savunma (Context Poisoning Defense)
**Hedef:** Kullanıcının sohbet geçmişine sızarak modeli yanıltmasını engellemek.

**Yöntem:**
- Gelen kullanıcı girdisi ve geçmiş bağlam, `context_manager.py` içinde basit kara liste regex’leri ile taranır.
- Şüpheli desen (çok uzun komut zincirleri, sistem talimatı taklidi, tekrarlayan yönlendirme ifadeleri) tespit edilirse bağlam kırpılır veya kullanıcı uyarılır.
- Deterministik, salt kural tabanlı.

---

## Faz 4: Uzun Oturum Kararlılığı (Long-Session Stability)
**Hedef:** Uzun diyaloglarda bağlam penceresinin dağılmasını önlemek.

**Yöntem (öncekiyle aynı, sadeleşmiş hali):**
- `context_manager.py` içinde, son kullanıcı ifadesi ile önceki turların Jaccard benzerliğine (kelime örtüşmesi) göre en alakalı son N cümle seçilir.
- Eşik altındaki cümleler pencereden çıkarılır.
- Hiçbir semantik sıralama motoru yok; saf Python set işlemleri.

---

## Faz 5: Gerileme Tespiti (Regression Detection)
**Hedef:** Yapılan değişikliklerin eski kararlı davranışı bozup bozmadığını anlamak.

**Yöntem:**
- Kritik 20-30 adet girdi için beklenen çıktılar (hash veya birebir metin) `tests/regression_fixtures/` altında saklanır.
- CI benzeri manuel test betiği, her değişiklik sonrası bu fixture’ları çalıştırır ve aynı çıktıyı üretip üretmediğini kontrol eder.
- Yeni bağımlılık yok; basit bir `diff` script’i.

---

## Faz 6: Yanıt Tutarlılığı (Response Consistency)
**Hedef:** Aynı tür sorulara hep aynı yapıda yanıt verilmesini sağlamak.

**Yöntem:**
- `response_templates.json` içinde, sık kullanılan sorgu tipleri için iskelet formatlar bulunur (örn. “Tanım: …”, “Adımlar: 1…2…”).
- Model çıktısı, bu şablonlardan uygun olanla sarılır; eğer şablon uymazsa zorlanmaz, yalnızca uyduğunda uygulanır.
- Dönüşüm tamamen `str.format()` ile yapılır; boru hattı yok.

---

## Faz 7: Araç Doğrulaması (Tool Verification)
**Hedef:** Modelin çağırdığı yerel araçların (hesap makinesi, takvim vb.) sonuçlarını deterministik olarak doğrulamak.

**Yöntem:**
- Her araç çağrısının dönüşü, basit bir doğrulayıcı fonksiyondan geçer (örn. matematiksel işlem tekrar hesaplanır, tarih formatı regex ile kontrol edilir).
- Yanlış sonuçta `[Araç hatası]` işareti konur.

---

## Faz 8: İstem Güvenlik Duvarı (Prompt Firewall)
**Hedef:** Zararlı veya manipülatif kullanıcı girdilerini reddetmek.

**Yöntem:**
- Girdi, `prompt_firewall.py` içindeki kara liste regex’lerine (sistem talimatı sızdırma, jailbreak desenleri) takılırsa yanıt verilmez, sabit bir uyarı döner.
- Deterministik, tamamen kural tabanlı.

---

## Uygulama Takvimi (Öncelik Sırası)
1. Faz 1: Halüsinasyon Azaltma (Hafta 1-2)
2. Faz 2: Karar İzi (Hafta 3)
3. Faz 3: Bağlam Zehirlenmesi Savunması (Hafta 4)
4. Faz 4: Uzun Oturum Kararlılığı (Hafta 5)
5. Faz 5: Gerileme Tespit Altyapısı (Hafta 6)
6. Faz 6: Yanıt Tutarlılığı (Hafta 7)
7. Faz 7: Araç Doğrulaması (Hafta 8)
8. Faz 8: İstem Güvenlik Duvarı (Hafta 9)

Her faz, tamamlandığında `HARDENING_FINAL_RAPOR.md`’deki başarı kriterleriyle çapraz kontrol edilecek.